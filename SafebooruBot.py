import os
import math
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
from bot_token import safebooru_bot
from discord.ext import commands
from discord.utils import find
from discord.ext import tasks

import mysql.connector
from important import ep, user, ps, host, user_2, password

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!!', intents=intents)

#safebooru_dbs = mysql.connector.connect(
#    host=ep,
#    user=user,
#    password=ps
#)


@bot.event
async def on_guild_join(guild):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS server_{guild.id}")
        cursor.execute(f"CREATE DATABASE server_{guild.id}")
        
        cursor.execute(f"USE server_{guild.id};")
        cursor.execute("DROP TABLE IF EXISTS settings;")
        cursor.execute("Create TABLE settings(ID INT NOT NULL AUTO_INCREMENT, List_limit INT,  In_process TINYINT(1), PRIMARY KEY (ID));")
        row = [10, 0]
        cursor.execute("INSERT INTO settings (List_limit, In_process) VALUES (%s, %s)", row)
        # Perhaps a row added in once the setting is finalized
        cursor.execute("DROP TABLE IF EXISTS channels;")
        cursor.execute("Create TABLE channels(Row_ID INT NOT NULL AUTO_INCREMENT, Channel_ID VARCHAR(32), Name VARCHAR(48), Amount_of_tags_selected INT, PRIMARY KEY (Row_ID));")
        cursor.close()
    cnx.commit()
    cnx.close()


@bot.event
async def on_connect(guild):
    print(f"Connected to {guild.id}")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
   

@bot.command(help='Sets the current channel as a location for images to be sent to')
async def setArtThread(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )
    channel_id = "channel_" + str(ctx.channel.id)

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        cursor.execute('SHOW TABLES')
        table_names = [table[0] for table in cursor.fetchall()]

        if channel_id in table_names:
            await ctx.send("Silly. This channel is already a designated place for art")
        else:
            #cursor.execute(f"DROP TABLE IF EXISTS {channel_id};")
            cursor.execute(f"Create TABLE {channel_id}(ID INT NOT NULL, Name VARCHAR(256), Category VARCHAR(256), Type VARCHAR(16), Link VARCHAR(2400), Latest_art VARCHAR(2400), PRIMARY KEY(ID));")
            sql = "INSERT INTO channels (Channel_ID, Name, Amount_of_tags_selected) VALUES (%s, %s, %s)"
            row = (ctx.channel.id, ctx.channel.name, 0)
            cursor.execute(sql, row)
            cnx.commit()
            
            await ctx.send("This channel has been set as a location for art")
        cursor.close()
    cnx.close()

    #await ctx.send("Let me know if there is asnything else I can do for you")

@bot.command()
async def setLimit(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )
    
    number = ctx.message.content[10:].strip()

    if number.isnumeric():
        number = int(number)
        
        if number <= 25:
            if cnx.is_connected():
                cursor = cnx.cursor()
                cursor.execute(f"USE server_{ctx.guild.id};")
                sql = f"UPDATE settings SET List_limit = {number} WHERE ID = 1"
                cursor.execute(sql)
                cnx.commit()

                cursor.close()
            cnx.close()
            await ctx.send(f"The limit for the search command is now set to {number}")
        else:
            await ctx.send(f"{number} is too high of a value. Please keep it at 25 or below")

    else:
        await ctx.send(f"There are letters and/or symbols in your request. Can you use only numeric values please?")                       

@bot.command()
async def search(ctx):
    msg = ctx.message.content[8:].strip().split("|")
    name = []
    cat = []
    c_type = []

    error_text = []

    if len(msg) > 1:
        if len(msg) > 2:
            name, cat, c_type = [i.lower().split() for i in msg]
        else:
            name, cat = [i.lower().split() for i in msg]
    else:
        name.append(msg[0])

    if len(name) > 24:
        error_text.append(f"You exceeded the amount of words for the **name** by {len(name) - 24}. Make sure to use at most 24 words when searching with the **name**")
    if len(cat) > 4:
        error_text.append(f"You exceeded the amount of words for the **category** by {len(cat) - 4}. Make sure to use at most 4 words when searching with the **category**")
    if len(c_type) > 1:
        error_text.append(f"You exceeded the amount of words for the **type** by {len(c_type) - 1}. Make sure to use only 1 word when searching the **type**")

    if len(error_text) > 0:
        await ctx.send('\n \n'.join(error_text))
    else:
        srch = []
        slct = []

        if len(name) > 0:
            col_value = 1
            for i in name:
                # This line below would be too intensive for a database that I intend to be useable in multiple servers and pushed to cloud. Keeping it for future refrence on improvement
                # search_name.append(f"LOWER({i}) in (Name_1, Name_2, Name_3, Name_4, Name_5, Name_6, Name_7, Name_8, Name_9, Name_10, Name_11, Name_12, Name_13, Name_14, Name_15, Name_16, Name_17, Name_18, Name_19, Name_20, Name_21, Name_22, Name_23, Name_24)")
                srch.append(f"'{i}' LIKE Name_{col_value}")
                slct.append(f"Name_{col_value}")
                col_value += 1
        if len(cat) > 0:
            col_value = 1
            for i in cat:
                srch.append(f"'{i}' LIKE Category_{col_value}")
                slct.append(f"Category_{col_value}")
                col_value += 1
        if len(c_type) > 0:
            srch.append(f"'{c_type[0]}' LIKE Type")
            slct.append("Type")
        
        # print(srch)
        # print(slct)
       
        cnx = mysql.connector.connect(
        host=host,
        user=user_2,
        password=password
        )

        fnd_tags = []
        if cnx.is_connected():
                cursor = cnx.cursor()
                cursor.execute(f"USE server_{ctx.guild.id};")
                sql = f"SELECT List_limit FROM settings"
                cursor.execute(sql)
                limit = cursor.fetchone()[0]
                
                cursor.execute(f"USE safebooru_info;")
                sql = f"SELECT * FROM safebooru_tags WHERE {' AND '.join(srch)} LIMIT {limit}"
                cursor.execute(sql)
                tags = cursor.fetchall()
                cursor.close()

                list_tags = ["### __ID | Name | Category | Type | Link__"]
                #["### **ID** | **Name** | **Category** | **Type** | **Link**"]
                for i in tags:
                    name_sum = sum(j != None for j in i[1:25])
                    cat_sum = sum(j != None for j in i[25:-2])
                    #type_n_null = sum(j != None for j in i[-2])
                    k = [j for j in i if j != None]
                    for l in range(1, len(k)-1):
                        k[l] = k[l].replace("_", "\\_")
                    k[-1] = f"[Link](<{k[-1]}>)"
                    k[0] = str(k[0]) + " |"
                    
                    k[name_sum] = k[name_sum] + " |"
                    if cat_sum > 0:
                        k[name_sum + cat_sum] = k[name_sum + cat_sum] + " |"
                    else:
                        k.insert(name_sum + 1, "  |")
                    k[-2] = k[-2] + " |"

                    #indices = [ind for ind, item in enumerate(k) if item[-1] == "|"]
                    #col_1 = k[indices[0]]
                    #uneven_list = ' '.join(k)
                    list_tags.append(' '.join(k))
                #list_tags.insert(0, "ID | Name | Category | Type | Link")
                id_max = 0
                name_max = 0
                category_max = 0
                type_max = 0
                for i in list_tags[1:]:
                    cols = i.split("|")
                    if len(cols[0]) > id_max:
                        id_max = len(cols[0])
                    if len(cols[1]) > name_max:
                        name_max = len(cols[1])
                    if len(cols[2]) > category_max:
                        category_max = len(cols[2])
                    if len(cols[3]) > type_max:
                        type_max = len(cols[3])
                
                for i in range(0, len(list_tags)):
                    cols = list_tags[i].split("|")
                    if len(cols[0]) != id_max:
                        cols[0] += "\\_" * (id_max - len(cols[0]))
                    if len(cols[1]) != name_max:
                        cols[1] = "\\_" * math.ceil((name_max - len(cols[1])) / 2) + cols[1] + "\\_" * math.floor((name_max - len(cols[1])) / 2)
                    if len(cols[2]) != category_max:
                        cols[2] = "\\_" * math.ceil((category_max - len(cols[2])) / 2) + cols[2] + "\\_" * math.floor((category_max - len(cols[2])) / 2)
                    if len(cols[3]) != type_max:
                        cols[3] = "\\_" * math.ceil((type_max - len(cols[3])) / 2) + cols[3] + "\\_" * math.floor((type_max - len(cols[3])) / 2)
                    list_tags[i] = '|'.join(cols)

                fnd_tags = '\n'.join(list_tags)
                #print(fnd_tags)
        cnx.close()

        await ctx.send(f"{fnd_tags}")


@bot.command()
async def select(ctx):
    # add for when there are duplicates, maybe if database is not up, and nothing shows up in search
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    msg = ctx.message.content[13:].strip().split()
    #srch_key = 0
    channel_name = ""
    art_name = ""
    #print(msg)
    if msg[1].isnumeric():
        if msg[0].isnumeric():
            srch_row = int(msg[0])
            srch_key = int(msg[1])
            if cnx.is_connected():
                cursor = cnx.cursor()
                
                cursor.execute(f"USE safebooru_info;")
                sql = f"SELECT * FROM safebooru_tags WHERE Tag_Id LIKE {srch_key}"
                cursor.execute(sql)
                tag = cursor.fetchone()
                tag_id = tag[0]
                tag_name = ' '.join([i for i in tag[1:25] if i != None])
                tag_category = ' '.join([i for i in tag[25:-2] if i != None])
                tag_type = tag[-2]
                tag_link = tag[-1]

                art_name = tag_name
                clean_tag = (tag_id, tag_name, tag_category, tag_type, tag_link, "")
                

                cursor.execute(f"USE server_{ctx.guild.id};")
                sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels WHERE Row_ID LIKE {srch_row}"
                cursor.execute(sql)
                channel_row = cursor.fetchone()
                channel = channel_row[0]
                channel_name = channel_row[1]
                amt_tags = int(channel_row[2])
                
                sql = "INSERT INTO channel_" + channel + " VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, clean_tag)
                
                sql = f"UPDATE channels SET Amount_of_tags_selected = {amt_tags + 1} WHERE Row_ID = {srch_row}"
                cursor.execute(sql)

                cnx.commit()
                cursor.close()
                cnx.close()
            await ctx.send(f"The tag **{art_name}** has been added to **{channel_name}**. I hope you enjoy the art it brings!")
        else:
            await ctx.send("Make sure that the ID you listed is a numerical number please")
    else:
        srch_row = int(msg[0])
        srch_link = msg[1].lower()
        if "safebooru.org/index.php?page=post" in srch_link:
            if cnx.is_connected():
                link = srch_link.split("index.php?page=post", 1)[1].replace("_", "\_").replace("%", "\%")

                cursor = cnx.cursor()
                cursor.execute(f"USE safebooru_info;")
                print(link)
                sql = f"SELECT * FROM safebooru_tags WHERE Link LIKE '%{link}'"
                cursor.execute(sql)
                tag = cursor.fetchone()
                tag_id = tag[0]
                tag_name = ' '.join([i for i in tag[1:25] if i != None])
                tag_category = ' '.join([i for i in tag[25:-2] if i != None])
                tag_type = tag[-2]
                tag_link = tag[-1]

                clean_tag = (tag_id, tag_name, tag_category, tag_type, tag_link, "")

                print(ctx.guild.id)
                cursor.execute(f"USE server_{ctx.guild.id};")
                sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels WHERE Row_ID LIKE {srch_row}"
                cursor.execute(sql)
                channel_row = cursor.fetchone()
                channel = channel_row[0]
                channel_name = channel_row[1]
                amt_tags = int(channel_row[2])
                
                sql = "INSERT INTO channel_" + channel + " VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, clean_tag)
                
                sql = f"UPDATE channels SET Amount_of_tags_selected = {amt_tags + 1} WHERE Row_ID = {srch_row}"
                cursor.execute(sql)

                cnx.commit()
                cursor.close()
                cnx.close()
            await ctx.send(f"The tag **{art_name}** has been added to **{channel_name}**. I hope you enjoy the art it brings!")
        else:
            await ctx.send(f"Make sure the link you provided is spelt correctly and from safebooru posts")
        #else:
    #else:
    #    if 

@bot.command()
async def selectHere(ctx):
    await ctx.send("")

@bot.command()
async def howToSearchAndSelect(ctx):
    await ctx.send("")

#@bot.command(help='Sets the current channel as the location of new images to be sent in from the provided Safebooru link')
#async def setArtThread(ctx, link):
#    await db.collection('character_threads').add({'thread_id': ctx.channel.id, 'link': link, 'image': 'jpg'})

@bot.command(help='Starts displaying the latest new images from the given links')
async def startArtShow(ctx):
    #global keep_going 
    #keep_going = True

    #asyncio.create_task(artShow(ctx))
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    # while keep_going:
    #     documts = db.collection('character_threads')
    #     doc_ref = documts.stream()

    #     opt = webdriver.ChromeOptions()
    #     opt.add_argument("--incognito")
    #     driver = webdriver.Chrome(ChromeDriverManager().install(), options=opt)
    #     wait = WebDriverWait(driver, 20)
 
    #     async for doc in doc_ref:
    #         try:
    #             d = doc.to_dict()
    #             driver.get(d.get('link'))
        
    #             wait.until(EC.visibility_of_element_located((By.ID, 'post-list')))
    #             post_list = driver.find_element(By.ID, 'post-list')
    #             post = post_list.find_element(By.XPATH, f'div[2]/div[1]/span[1]/a')
    #             post.click()
        
    #             wait.until(EC.visibility_of_element_located((By.ID, 'right-col')))
    #             img_spot = driver.find_element(By.ID, 'right-col')
    #             img = img_spot.find_element(By.XPATH, f'div/img')
    #             img_URL = img.get_attribute('src')
    #             if img_URL == d.get('image'):
    #                 print('Image already posted')
    #             else:
    #                 await documts.document(doc.id).update({'image': img_URL})
    #                 print('Downloading image %s...' % (img_URL))
    #                 urllib.request.urlretrieve(img_URL, os.getcwd() + '/image.jpg')
    #                 channel = bot.get_channel(d.get('thread_id'))
    #                 await channel.send('', file=discord.File('image.jpg'))
    #         except (NoSuchElementException, JavascriptException):
    #             print('Page error occured')
    #     driver.close()
    #    await asyncio.sleep(1)

@bot.command(help='Stops the bot from searching for new images to post')
async def stopArtShow(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )
    
    #global keep_going 
    #keep_going = False
    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"UPDATE settings SET In_process = 0 WHERE Id = 1"
        cursor.execute(sql)
        cnx.commit()

        cursor.close()
    cnx.close()

    await ctx.send("Ending the show")

async def ArtShow(ctx):
    await print("This is where the art grabbing will start")

#@tasks.loop(seconds = 5)
async def artShow(ctx):
    None

bot.run(safebooru_bot)