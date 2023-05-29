import os
import asyncio
import urllib.request
import firebase_admin
from selenium import webdriver
from firebase_admin import credentials
from firebase_admin import firestore_async
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, JavascriptException
from selenium.webdriver.support import expected_conditions as EC
import discord
from bot_token import character_update_bot
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!!', intents=intents)
cred = credentials.Certificate('CharacterBot\\serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore_async.client()

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
   

@bot.command(help='Sets the current channel as the location of new images to be sent in from the provided Safebooru link')
async def setArtThread(ctx, link):
    await db.collection('character_threads').add({'thread_id': ctx.channel.id, 'link': link, 'image': 'jpg'})

@bot.command(help='Starts displaying the latest new images from the given links')
async def startArtShow(ctx):
    global keep_going 
    keep_going = True

    while keep_going:
        documts = db.collection('character_threads')
        doc_ref = documts.stream()

        opt = webdriver.ChromeOptions()
        opt.add_argument("--incognito")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=opt)
        wait = WebDriverWait(driver, 20)
 
        async for doc in doc_ref:
            try:
                d = doc.to_dict()
                driver.get(d.get('link'))
        
                wait.until(EC.visibility_of_element_located((By.ID, 'post-list')))
                post_list = driver.find_element(By.ID, 'post-list')
                post = post_list.find_element(By.XPATH, f'div[2]/div[1]/span[1]/a')
                post.click()
        
                wait.until(EC.visibility_of_element_located((By.ID, 'right-col')))
                img_spot = driver.find_element(By.ID, 'right-col')
                img = img_spot.find_element(By.XPATH, f'div/img')
                img_URL = img.get_attribute('src')
                if img_URL == d.get('image'):
                    print('Image already posted')
                else:
                    await documts.document(doc.id).update({'image': img_URL})
                    print('Downloading image %s...' % (img_URL))
                    urllib.request.urlretrieve(img_URL, os.getcwd() + '/image.jpg')
                    channel = bot.get_channel(d.get('thread_id'))
                    await channel.send('', file=discord.File('image.jpg'))
            except (NoSuchElementException, JavascriptException):
                print('Page error occured')
        driver.close()
        await asyncio.sleep(1)

@bot.command(help='Ends the bot from searching for new images to post')
async def stopArtShow(ctx):
    global keep_going 
    keep_going = False
    await ctx.send("Ending search")

bot.run(character_update_bot)