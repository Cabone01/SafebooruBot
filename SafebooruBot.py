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

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!") 
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

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

@bot.tree.command()#help='Sets the current channel as a location for images to be sent to')
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

@bot.tree.command()
async def deleteArtThread(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    dlt_channel = ctx.message.content.lower().split()[1]
    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        row_ids = [i[1] for i in artThreads]
        dlt_fnd = []

        if dlt_channel in row_ids:
            dlt_fnd = artThreads[row_ids.index(dlt_channel)]
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            await ctx.send(f"Are you sure you want to delete **{dlt_fnd[1]}**? You will lose **{dlt_fnd[2]}** tags that were added there")
            response = await ctx.bot.wait_for('message', check=check)
            if (response.content.lower() == 'yes') | (response.content.lower() == 'yeah') | (response.content.lower() == 'sure') | (response.content.lower() == 'y'):
                dlt_name = dlt_fnd[1].replace("_", "\_")

                sql = f"DROP TABLE IF EXISTS channel_{dlt_fnd[0]}"
                cursor.execute(sql)

                sql = f"DELETE FROM channels WHERE Name LIKE '{dlt_name}'"
                cursor.execute(sql)
                cnx.commit()

                cursor.close()
                cnx.close()
                await ctx.send(f"The channel **{dlt_name}** is no longer an art thread. Changes may take a moment to take affect")
            else:
                cursor.close()
                cnx.close()
                await ctx.send(f"Since you did not verify, **{dlt_fnd[1]}** will be kept as an art thread")
        else:
            cursor.close()
            cnx.close()
            await ctx.send(f"The channel **{dlt_channel}** does not exist in our file. Make sure to check the spelling or check the file to see if the name is different from what it is now")
        # await ctx.send(f"test: {dlt_channel}")

@bot.tree.command()
async def deleteArtThreadHere(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    dlt_channel = str(ctx.channel.id)#.message.content.split()[1]
    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels" 
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        row_ids = [i[0] for i in artThreads]
        dlt_fnd = []

        if dlt_channel in row_ids:
            dlt_fnd = artThreads[row_ids.index(dlt_channel)]
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            await ctx.send(f"Are you sure you want to delete **{dlt_fnd[1]}**? You will lose **{dlt_fnd[2]}** tags that were added there")
            response = await ctx.bot.wait_for('message', check=check)
            if (response.content.lower() == 'yes') | (response.content.lower() == 'yeah') | (response.content.lower() == 'sure') | (response.content.lower() == 'y'):
                dlt_name = dlt_fnd[1].replace("_", "\_")

                sql = f"DROP TABLE IF EXISTS channel_{dlt_fnd[0]}"
                cursor.execute(sql)

                sql = f"DELETE FROM channels WHERE Name LIKE '{dlt_name}'"
                cursor.execute(sql)
                cnx.commit()

                cursor.close()
                cnx.close()
                await ctx.send(f"The channel **{dlt_name}** is no longer an art thread. Changes may take a moment to take affect")
            else:
                cursor.close()
                cnx.close()
                await ctx.send(f"Since you did not verify, **{dlt_fnd[1]}** will be kept as an art thread")
        else:
            cursor.close()
            cnx.close()
            await ctx.send(f"The channel **{ctx.channel.name}** does not exist in our file.")
        # await ctx.send(f"test: {dlt_channel}")

@bot.tree.command()
async def seeArtThreads(ctx):
    # Maybe keep the code that evens out the text (despite it not being by much or at all)
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )
    
    threads = ["### __Channel Name | Number of tags added__"] #[]
    #max_name_len = 0
    if cnx.is_connected():
        cursor = cnx.cursor()  
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        threads_tup = cursor.fetchall()
        cursor.close()
        cnx.close()

        # max_name_len = max(len(i[0]) for i in threads_tup)
        # if 4 < max_name_len:
        #     txt = "### __Name" + ("\_" * (max_name_len - 4)) + "| Number of tags__"
        #     threads.append(txt)
        # else:
        #     threads.append("### __Name | Number of tags__")

        for i in threads_tup:
            name = i[0]
            num_tags = str(i[1])
            # if len(name) != max_name_len:
            #     name += "\_" * (max_name_len - len(name))
            #channel = " | ".join([name, num_tags])
            threads.append(" | ".join([name, num_tags]))

    threads = "\n".join(threads) 
    await ctx.send(f"{threads}")

@bot.tree.command()
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

@bot.tree.command()
async def search(ctx):
    msg = ctx.message.content[8:].strip().lower().split("|")
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
                j = i.replace('"', '\"').replace("'", "\'").replace("_", "\_").replace("%", "\%")
                srch.append(f"'{j}' LIKE Name_{col_value}")
                slct.append(f"Name_{col_value}")
                col_value += 1
        if len(cat) > 0:
            col_value = 1
            for i in cat:
                j = i.replace('"', '\"').replace("'", "\'").replace("_", "\_").replace("%", "\%")
                srch.append(f"'{j}' LIKE Category_{col_value}")
                slct.append(f"Category_{col_value}")
                col_value += 1
        if len(c_type) > 0:
            srch.append(f"'{c_type[0]}' LIKE Type")
            slct.append("Type")
       
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
            cnx.close()

            list_tags = ["### __ID | Name | Category | Type | Link__"]

            if len(tags) != 0:
                print(tags)
                for i in tags:
                    name_sum = sum(j != None for j in i[1:25])
                    cat_sum = sum(j != None for j in i[25:-2])

                    k = [j for j in i if j != None]
                    for l in range(1, len(k)-1):
                        k[l] = k[l].replace("_", "\_")
                    k[-1] = f"[Link](<{k[-1]}>)"
                    k[0] = str(k[0]) + " |"
                    
                    k[name_sum] = k[name_sum] + " |"
                    if cat_sum > 0:
                        k[name_sum + cat_sum] = k[name_sum + cat_sum] + " |"
                    else:
                        k.insert(name_sum + 1, "  |")
                    k[-2] = k[-2] + " |"
                    list_tags.append(' '.join(k))

                id_max  = max(len(i.split("|")[0]) for i in list_tags[1:])
                name_max = max(len(i.split("|")[1]) for i in list_tags[1:])
                category_max = max(len(i.split("|")[2]) for i in list_tags[1:])
                type_max = max(len(i.split("|")[3]) for i in list_tags[1:])

                
                for i in range(0, len(list_tags)):
                    cols = list_tags[i].split("|")
                    if len(cols[0]) < id_max:
                        cols[0] += "\_" * (id_max - len(cols[0]))
                    if len(cols[1]) < name_max:
                        cols[1] = "\_" * math.ceil((name_max - len(cols[1])) / 2) + cols[1] + "\_" * math.floor((name_max - len(cols[1])) / 2)
                    if len(cols[2]) < category_max:
                        cols[2] = "\_" * math.ceil((category_max - len(cols[2])) / 2) + cols[2] + "\_" * math.floor((category_max - len(cols[2])) / 2)
                    if len(cols[3]) < type_max:
                        cols[3] = "\_" * math.ceil((type_max - len(cols[3])) / 2) + cols[3] + "\_" * math.floor((type_max - len(cols[3])) / 2)
                    list_tags[i] = '|'.join(cols)

                fnd_tags = '\n'.join(list_tags)
                await ctx.send(f"{fnd_tags}")
            else:
                await ctx.send("I could not find anything on this search. If you need an example on how to search, use the /howToSearchandSelect command")

@bot.tree.command()
async def select(ctx):
    # add if database is not up and if nothing shows up in search
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    msg = ctx.message.content[8:].strip().split()
    channel_name = msg[0].lower()

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        channels = cursor.fetchall()
        channel_names = [i[1] for i in channels]

        if channel_name in channel_names:
            channel_fnd = channels[channel_names.index(channel_name)]
            sql = f"SELECT ID, Name, Link FROM channel_{channel_fnd[0]}"
            cursor.execute(sql)
            tags = cursor.fetchall()

            if msg[1].isnumeric():
                tag_id = int(msg[1])
                tag_ids = [i[0] for i in tags]

                if tag_id not in tag_ids:
                    cursor.execute(f"USE safebooru_info;")
                    sql = f"SELECT * FROM safebooru_tags WHERE Tag_Id LIKE {tag_id}"
                    cursor.execute(sql)
                    tag = cursor.fetchone()
                    
                    if tag != None:
                        tag_id = tag[0]
                        tag_name = ' '.join([i for i in tag[1:25] if i != None])
                        tag_category = ' '.join([i for i in tag[25:-2] if i != None])
                        tag_type = tag[-2]
                        tag_link = tag[-1]
                        clean_tag = (tag_id, tag_name, tag_category, tag_type, tag_link, "")

                        cursor.execute(f"USE server_{ctx.guild.id};")
                        sql = "INSERT INTO channel_" + channel_fnd[0] + " VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, clean_tag)
                        
                        sql = f"UPDATE channels SET Amount_of_tags_selected = {channel_fnd[2] + 1} WHERE Channel_ID = {channel_fnd[0]}"
                        cursor.execute(sql)

                        cnx.commit()
                        cursor.close()
                        cnx.close()
                        await ctx.send(f"The tag **{tag_name}** has been added to **{channel_name}**. I hope you enjoy the art it brings!")
                    else:
                        await ctx.send(f"It would appear that there is no tag under **{tag_id}**")

                else:
                    cursor.close()
                    cnx.close()
                    tag = tags[tag_ids.index(tag_id)]
                    await ctx.send(f"It would appear that **{tag[1]}** has already been added to **{channel_name}**")
            else:
                srch_link = msg[1].lower().replace("(", "%28").replace(")", "%29").replace("www.", "")
                tag_links = [i[2] for i in tags]

                if "safebooru.org/index.php?page=post&s=list&tags=" in srch_link:
                    link_fnd = []
                    if srch_link.startswith("https://"):
                        link_fnd = [i for i in tag_links if srch_link == i]
                    else:
                        srch_link = "https://" + srch_link
                        link_fnd = [i for i in tag_links if srch_link == i]

                    if len(link_fnd) < 1:
                        link = srch_link.replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")
                        cursor = cnx.cursor()
                        cursor.execute(f"USE safebooru_info;")
                        sql = f"SELECT * FROM safebooru_tags WHERE LOWER(Link) LIKE '%{link}'"
                        cursor.execute(sql)
                        tag = cursor.fetchone()

                        if tag != None:
                            tag_id = tag[0]
                            tag_name = ' '.join([i for i in tag[1:25] if i != None])
                            tag_category = ' '.join([i for i in tag[25:-2] if i != None])
                            tag_type = tag[-2]
                            tag_link = tag[-1]
                            clean_tag = (tag_id, tag_name, tag_category, tag_type, tag_link, "")

                            cursor.execute(f"USE server_{ctx.guild.id};")
                            sql = "INSERT INTO channel_" + channel_fnd[0] + " VALUES (%s, %s, %s, %s, %s, %s)"
                            cursor.execute(sql, clean_tag)

                            sql = f"UPDATE channels SET Amount_of_tags_selected = {channel_fnd[2] + 1} WHERE Channel_ID = {channel_fnd[0]}"
                            cursor.execute(sql)

                            cnx.commit()
                            cursor.close()
                            cnx.close()
                            await ctx.send(f"The tag **{tag_name}** has been added to **{channel_name}**. I hope you enjoy the art it brings!")
                        else:
                            await ctx.send(f"The [link](<{link}>) does not appear to have a tag connected to it. Make sure to check if it is the correct link")
                    else:
                        cursor.close()
                        cnx.close()
                        tag = tags[tag_links.index(link_fnd[0])]
                        await ctx.send(f"It would appear that **{tag[1]}** has already been added to **{channel_name}**")
                else:
                    await ctx.send(f"Make sure the link you provided is the full url, spelt correctly, and from safebooru posts")
        else:
            await ctx.send(f"It would appear **{channel_name}** does not exist in our file. Make sure to either set that channel as an art thread or to check the spelling")

@bot.tree.command()
async def selectHere(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    msg = ctx.message.content[12:].lower().strip().split()
    channel_id = str(ctx.channel.id)

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        channels = cursor.fetchall()
        channel_ids = [i[0] for i in channels]

        if channel_id in channel_ids:
            channel_fnd = channels[channel_ids.index(channel_id)]
            sql = f"SELECT ID, Name, Link FROM channel_{channel_fnd[0]}"
            cursor.execute(sql)
            tags = cursor.fetchall()

            if msg[0].isnumeric():
                tag_id = int(msg[0])
                tag_ids = [i[0] for i in tags]

                if tag_id not in tag_ids:
                    cursor.execute(f"USE safebooru_info;")
                    sql = f"SELECT * FROM safebooru_tags WHERE Tag_Id LIKE {tag_id}"
                    cursor.execute(sql)
                    tag = cursor.fetchone()
                    
                    if tag != None:
                        tag_id = tag[0]
                        tag_name = ' '.join([i for i in tag[1:25] if i != None])
                        tag_category = ' '.join([i for i in tag[25:-2] if i != None])
                        tag_type = tag[-2]
                        tag_link = tag[-1]
                        clean_tag = (tag_id, tag_name, tag_category, tag_type, tag_link, "")

                        cursor.execute(f"USE server_{ctx.guild.id};")
                        sql = "INSERT INTO channel_" + channel_fnd[0] + " VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, clean_tag)
                        
                        sql = f"UPDATE channels SET Amount_of_tags_selected = {channel_fnd[2] + 1} WHERE Channel_ID = {channel_fnd[0]}"
                        cursor.execute(sql)

                        cnx.commit()
                        cursor.close()
                        cnx.close()
                        await ctx.send(f"The tag **{tag_name}** has been added to **{channel_fnd[1]}**. I hope you enjoy the art it brings!")
                    else:
                        await ctx.send(f"It would appear that there is no tag under **{tag_id}**")

                else:
                    cursor.close()
                    cnx.close()
                    tag = tags[tag_ids.index(tag_id)]
                    await ctx.send(f"It would appear that **{tag[1]}** has already been added to **{channel_fnd[1]}**")
            else:
                srch_link = msg[0].lower().replace("(", "%28").replace(")", "%29").replace("www.", "")
                tag_links = [i[2] for i in tags]

                if "safebooru.org/index.php?page=post&s=list&tags=" in srch_link:
                    link_fnd = []
                    if srch_link.startswith("https://"):
                        link_fnd = [i for i in tag_links if srch_link == i]
                    else:
                        srch_link = "https://" + srch_link
                        link_fnd = [i for i in tag_links if srch_link == i]

                    if len(link_fnd) < 1:
                        link = srch_link.replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")
                        cursor = cnx.cursor()
                        cursor.execute(f"USE safebooru_info;")
                        sql = f"SELECT * FROM safebooru_tags WHERE LOWER(Link) LIKE '%{link}'"
                        cursor.execute(sql)
                        tag = cursor.fetchone()

                        if tag != None:
                            tag_id = tag[0]
                            tag_name = ' '.join([i for i in tag[1:25] if i != None])
                            tag_category = ' '.join([i for i in tag[25:-2] if i != None])
                            tag_type = tag[-2]
                            tag_link = tag[-1]
                            clean_tag = (tag_id, tag_name, tag_category, tag_type, tag_link, "")

                            cursor.execute(f"USE server_{ctx.guild.id};")
                            sql = "INSERT INTO channel_" + channel_fnd[0] + " VALUES (%s, %s, %s, %s, %s, %s)"
                            cursor.execute(sql, clean_tag)

                            sql = f"UPDATE channels SET Amount_of_tags_selected = {channel_fnd[2] + 1} WHERE Channel_ID = {channel_fnd[0]}"
                            cursor.execute(sql)

                            cnx.commit()
                            cursor.close()
                            cnx.close()
                            await ctx.send(f"The tag **{tag_name}** has been added to **{channel_fnd[1]}**. I hope you enjoy the art it brings!")
                        else:
                            await ctx.send(f"The [link](<{link}>) does not appear to have a tag connected to it. Make sure to check if it is the correct link")
                    else:
                        cursor.close()
                        cnx.close()
                        tag = tags[tag_links.index(link_fnd[0])]
                        await ctx.send(f"It would appear that **{tag[1]}** has already been added to **{channel_fnd[1]}**")
                else:
                    await ctx.send(f"Make sure the link you provided is the full url, spelt correctly, and from safebooru posts")
        else:
            await ctx.send(f"It would appear **{ctx.channel.name}** does not exist in our file. Make sure to set this channel as an art thread before you add to it")

@bot.tree.command()
async def howToSearchAndSelect(ctx):
    await ctx.send("")

@bot.tree.command()
async def seeTagsInThread(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    channel_name = ctx.message.content[17:].lower().strip()
    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Channel_ID, Name FROM channels"
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        row_ids = [i[1] for i in artThreads]

        if channel_name in row_ids:
            channel = artThreads[row_ids.index(channel_name)]
            sql = f"SELECT ID, Name, Category, Type, Link FROM channel_{channel[0]}"
            cursor.execute(sql)
            tags = cursor.fetchall()
            cursor.close()
            cnx.close()

            list_tags = [["### __ID", "Name", "Category", "Type", " Link__"]]
            
            list_tags.extend([[str(j) for j in i] for i in tags])
            id_max  = max(len(i[0]) for i in list_tags[1:]) + 1
            name_max = max(len(i[1]) for i in list_tags[1:]) + 2
            category_max = max(len(i[2]) for i in list_tags[1:]) + 2
            type_max = max(len(i[3]) for i in list_tags[1:]) + 2
            x = 0

            for i in list_tags:
                i[0] = f"{i[0]} "
                i[1] = f" {i[1]} "
                i[2] = f" {i[2]} "
                i[3] = f" {i[3]} "
                if len(i[0]) < id_max:
                    i[0] += "\_" * (id_max - len(i[0]))
                if len(i[1]) < name_max:
                    i[1] = "\_" * math.ceil((name_max - len(i[1])) / 2) + i[1] + "\_" * math.floor((name_max - len(i[1])) / 2)
                if len(i[2]) < category_max:
                    i[2] = "\_" * math.ceil((category_max - len(i[2])) / 2) + i[2] + "\_" * math.floor((category_max - len(i[2])) / 2)
                if len(i[3]) < type_max:
                    i[3] = "\_" * math.ceil((type_max - len(i[3])) / 2) + i[3] + "\_" * math.floor((type_max - len(i[3])) / 2)
                if x != 0:
                    i[4] = " [Link](<" + i[4].replace('_', '\_') + ">)"
                list_tags[x] = "|".join(i)
                x += 1
                

            all_tags = '\n'.join(list_tags)
            await ctx.send(f"{all_tags}")
        else:
            cursor.close()
            cnx.close()
            if len(channel_name) > 0:
                await ctx.send(f"The channel **{channel_name}** does not exist in our file. Make sure to check the spelling or the file to see if the name is different from what it is now")
            else:
                await ctx.send(f"Make sure when using this command to input the channel's name you are looking for. If you are trying to see the tags in the current channel, use the /seeTagsInHere command to see the tags in the current channel")

@bot.tree.command()
async def seeTagsInHere(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    channel_name = ctx.channel.name
    channel_id = str(ctx.channel.id)

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Channel_ID, Name FROM channels"
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        row_ids = [i[0] for i in artThreads]

        if channel_id in row_ids:
            channel = artThreads[row_ids.index(channel_id)]
            sql = f"SELECT ID, Name, Category, Type, Link FROM channel_{channel[0]}"
            cursor.execute(sql)
            tags = cursor.fetchall()
            cursor.close()
            cnx.close()

            list_tags = [["### __ID", "Name", "Category", "Type", " Link__"]]
            
            list_tags.extend([[str(j) for j in i] for i in tags])
            id_max  = max(len(i[0]) for i in list_tags[1:]) + 1
            name_max = max(len(i[1]) for i in list_tags[1:]) + 2
            category_max = max(len(i[2]) for i in list_tags[1:]) + 2
            type_max = max(len(i[3]) for i in list_tags[1:]) + 2
            x = 0

            for i in list_tags:
                i[0] = f"{i[0]} "
                i[1] = f" {i[1]} "
                i[2] = f" {i[2]} "
                i[3] = f" {i[3]} "
                if len(i[0]) < id_max:
                    i[0] += "\_" * (id_max - len(i[0]))
                if len(i[1]) < name_max:
                    i[1] = "\_" * math.ceil((name_max - len(i[1])) / 2) + i[1] + "\_" * math.floor((name_max - len(i[1])) / 2)
                if len(i[2]) < category_max:
                    i[2] = "\_" * math.ceil((category_max - len(i[2])) / 2) + i[2] + "\_" * math.floor((category_max - len(i[2])) / 2)
                if len(i[3]) < type_max:
                    i[3] = "\_" * math.ceil((type_max - len(i[3])) / 2) + i[3] + "\_" * math.floor((type_max - len(i[3])) / 2)
                if x != 0:
                    i[4] = " [Link](<" + i[4].replace('_', '\_') + ">)"
                list_tags[x] = "|".join(i)
                x += 1

            all_tags = '\n'.join(list_tags)
            await ctx.send(f"{all_tags}")
        else:
            cursor.close()
            cnx.close()
            await ctx.send(f"The channel **{channel_name}** does not exist in our file. If there is a mistake, make sure this channel is the orginal one that was set as an art thread")

@bot.tree.command()
async def deleteTagInThread(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    dlt_info = ctx.message.content[19:].lower().split()
    channel_name = dlt_info[0]
    dlt_tag = dlt_info[1]

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        row_names = [i[1] for i in artThreads]
        
        if channel_name in row_names:
            channel = artThreads[row_names.index(channel_name)]
            if dlt_tag.isnumeric(): 
                sql = f"SELECT ID, Name FROM channel_{channel[0]}"
                cursor.execute(sql)
                tags = cursor.fetchall()
                tag_ids = [str(i[0]) for i in tags]

                if dlt_tag in tag_ids:
                    dlt_fnd = tags[tag_ids.index(dlt_tag)]
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel

                    await ctx.send(f"Are you sure you want to delete **{dlt_fnd[1]}** from **{channel[1]}**?")
                    response = await ctx.bot.wait_for('message', check=check)
                    if (response.content.lower() == 'yes') | (response.content.lower() == 'yeah') | (response.content.lower() == 'sure') | (response.content.lower() == 'y'):
                        dlt_name = dlt_fnd[1].replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")

                        sql = f"DELETE FROM channel_{channel[0]} WHERE Name LIKE '{dlt_name}'"
                        cursor.execute(sql)

                        sql = f"UPDATE channels SET Amount_of_tags_selected = {channel[2] - 1} WHERE Channel_ID = {channel[0]}"
                        cursor.execute(sql)
                        cnx.commit()

                        cursor.close()
                        cnx.close()
                        await ctx.send(f"The tag **{dlt_name}** has been removed from **{channel[1]}**. Changes may take a moment to take affect")
                    else:
                        cursor.close()
                        cnx.close()
                        await ctx.send(f"Since you did not verify, **{dlt_fnd[1]}** will be kept")
                else:
                    await ctx.send(f"The tag under **{dlt_tag}** does not exist in **{channel[1]}**. Make sure to check whether the tag is in another channel or if its the correct number associated")
            else:
                sql = f"SELECT ID, Name, Link FROM channel_{channel[0]}"
                cursor.execute(sql)
                tags = cursor.fetchall()
                tag_ids = [i[2] for i in tags]

                link = dlt_tag.replace("(", "%28").replace(")", "%29")

                if link in tag_ids:
                    dlt_fnd = tags[tag_ids.index(link)]
                    
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel

                    await ctx.send(f"Are you sure you want to delete **{dlt_fnd[1]}** from **{channel[1]}**?")
                    response = await ctx.bot.wait_for('message', check=check)
                    if (response.content.lower() == 'yes') | (response.content.lower() == 'yeah') | (response.content.lower() == 'sure') | (response.content.lower() == 'y'):
                        dlt_name = dlt_fnd[1].replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")

                        sql = f"DELETE FROM channel_{channel[0]} WHERE Name LIKE '{dlt_name}'"
                        cursor.execute(sql)

                        sql = f"UPDATE channels SET Amount_of_tags_selected = {channel[2] - 1} WHERE Channel_ID = {channel[0]}"
                        cursor.execute(sql)
                        cnx.commit()

                        cursor.close()
                        cnx.close()
                        await ctx.send(f"The tag **{dlt_name}** has been removed from **{channel[1]}**. Changes may take a moment to take affect")
                    else:
                        cursor.close()
                        cnx.close()
                        await ctx.send(f"Since you did not verify, **{dlt_fnd[1]}** will be kept")
                else:
                    await ctx.send(f"The [link](<{dlt_tag}>) provided does not exist in **{channel[1]}**. Make sure to check whether the link is in another channel or that the full url was used")
        else:
            cursor.close()
            cnx.close()
            await ctx.send(f"The channel **{channel_name}** does not exist in our file. Make sure to check the spelling or check the file to see if the name is different from what it is now")

@bot.tree.command()
async def deleteTagHere(ctx):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    dlt_info = ctx.message.content[15:].lower().split()
    channel_name = ctx.channel.name
    channel_id = str(ctx.channel.id)
    dlt_tag = dlt_info[0]

    if cnx.is_connected():
        # txt = deleteTagInThread(cnx=cnx, ctx=ctx, channel_name=channel_name, dlt_tag=dlt_tag)
        # await ctx.send(txt)
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{ctx.guild.id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        row_ids = [i[0] for i in artThreads]
        
        if channel_id in row_ids:
            channel = artThreads[row_ids.index(channel_id)]
            if dlt_tag.isnumeric(): 
                sql = f"SELECT ID, Name FROM channel_{channel[0]}"
                cursor.execute(sql)
                tags = cursor.fetchall()
                tag_ids = [str(i[0]) for i in tags]

                if dlt_tag in tag_ids:
                    dlt_fnd = tags[tag_ids.index(dlt_tag)]

                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel

                    await ctx.send(f"Are you sure you want to delete **{dlt_fnd[1]}** from **{channel[1]}**?")
                    response = await ctx.bot.wait_for('message', check=check)
                    if (response.content.lower() == 'yes') | (response.content.lower() == 'yeah') | (response.content.lower() == 'sure') | (response.content.lower() == 'y'):
                        dlt_name = dlt_fnd[1].replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")

                        sql = f"DELETE FROM channel_{channel[0]} WHERE Name LIKE '{dlt_name}'"
                        cursor.execute(sql)

                        sql = f"UPDATE channels SET Amount_of_tags_selected = {channel[2] - 1} WHERE Channel_ID = {channel[0]}"
                        cursor.execute(sql)
                        cnx.commit()

                        cursor.close()
                        cnx.close()
                        await ctx.send(f"The tag **{dlt_name}** has been removed from **{channel[1]}**. Changes may take a moment to take affect")
                    else:
                        cursor.close()
                        cnx.close()
                        await ctx.send(f"Since you did not verify, **{dlt_fnd[1]}** will be kept")
                else:
                    await ctx.send(f"The tag under **{dlt_tag}** does not exist in **{channel[1]}**. Make sure to check whether the tag is in another channel or if its the correct number associated")
            else:
                sql = f"SELECT ID, Name, Link FROM channel_{channel[0]}"
                cursor.execute(sql)
                tags = cursor.fetchall()
                tag_ids = [i[2] for i in tags]

                link = dlt_tag.replace("(", "%28").replace(")", "%29")

                if link in tag_ids:
                    dlt_fnd = tags[tag_ids.index(link)]
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel

                    await ctx.send(f"Are you sure you want to delete **{dlt_fnd[1]}** from **{channel[1]}**?")
                    response = await ctx.bot.wait_for('message', check=check)
                    if (response.content.lower() == 'yes') | (response.content.lower() == 'yeah') | (response.content.lower() == 'sure') | (response.content.lower() == 'y'):
                        dlt_name = dlt_fnd[1].replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")

                        sql = f"DELETE FROM channel_{channel[0]} WHERE Name LIKE '{dlt_name}'"
                        cursor.execute(sql)

                        sql = f"UPDATE channels SET Amount_of_tags_selected = {channel[2] - 1} WHERE Channel_ID = {channel[0]}"
                        cursor.execute(sql)
                        cnx.commit()

                        cursor.close()
                        cnx.close()
                        await ctx.send(f"The tag **{dlt_name}** has been removed from **{channel[1]}**. Changes may take a moment to take affect")
                    else:
                        cursor.close()
                        cnx.close()
                        await ctx.send(f"Since you did not verify, **{dlt_fnd[1]}** will be kept")
                else:
                    await ctx.send(f"The [link](<{dlt_tag}>) provided does not exist in **{channel[1]}**. Make sure to check whether the link is in another channel or that the full url was used")
        else:
            cursor.close()
            cnx.close()
            await ctx.send(f"It appears **{channel_name}** does not exist in our file. Make sure to check the spelling or check the file to see if the name is different from what it is now")

#@bot.command(help='Sets the current channel as the location of new images to be sent in from the provided Safebooru link')
#async def setArtThread(ctx, link):
#    await db.collection('character_threads').add({'thread_id': ctx.channel.id, 'link': link, 'image': 'jpg'})

@bot.tree.command()#help='Starts displaying the latest new images from the given links')
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

@bot.tree.command()#help='Stops the bot from searching for new images to post')
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
        sql = f"UPDATE settings SET In_process = 0 WHERE ID = 1"
        cursor.execute(sql)
        cnx.commit()

        cursor.close()
    cnx.close()

    await ctx.send("Ending the show")

async def artShow(ctx):
    await print("This is where the art grabbing will start")

bot.run(safebooru_bot)


# async def deleteTagInThread(cnx, ctx, channel_name, dlt_tag):
#     cursor = cnx.cursor()
#     cursor.execute(f"USE server_{ctx.guild.id};")
#     sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
#     cursor.execute(sql)
#     artThreads = cursor.fetchall()
#     row_names = [i[1] for i in artThreads]

#     if channel_name in row_names:
#         channel = artThreads[row_names.index(channel_name)]
#         if dlt_tag.isnumeric(): 
#             sql = f"SELECT ID, Name FROM channel_{channel[0]}"
#             cursor.execute(sql)
#             tags = cursor.fetchall()
#             tag_ids = [str(i[0]) for i in tags]

#             if dlt_tag in tag_ids:
#                 dlt_fnd = tags[tag_ids.index(dlt_tag)]

#                 def check(m):
#                      return m.author == ctx.author and m.channel == ctx.channel
                
#                 await ctx.send(f"Are you sure you want to delete **{dlt_fnd[1]}** from **{channel[1]}**?")
#                 response = await ctx.bot.wait_for('message', check=check)
#                 return delete(1, cnx, cursor, response, channel, dlt_fnd)
#             else:
#                 txt = f"The tag under **{dlt_tag}** does not exist in **{channel[1]}**. Make sure to check whether the tag is in another channel or if its the correct number associated"
#                 return txt
#         else:
#                 sql = f"SELECT ID, Name, Link FROM channel_{channel[0]}"
#                 cursor.execute(sql)
#                 tags = cursor.fetchall()
#                 tag_ids = [i[2] for i in tags]

#                 link = dlt_tag.replace("(", "%28").replace(")", "%29")

#                 if link in tag_ids:
#                     dlt_fnd = tags[tag_ids.index(link)]

#                     def check(m):
#                        return m.author == ctx.author and m.channel == ctx.channel
                    
#                     await ctx.send(f"Are you sure you want to delete **{dlt_fnd[1]}** from **{channel[1]}**?")
#                     response = await ctx.bot.wait_for('message', check=check)
#                     return delete(1, cnx, cursor, response, channel, dlt_fnd)
#                 else:
#                     txt = f"The [link](<{dlt_tag}>) provided does not exist in **{channel[1]}**. Make sure to check whether the link is in another channel or that the full url was used"
#                     return txt
#     else:
#         cursor.close()
#         cnx.close()
#         txt = f"The channel **{channel_name}** does not exist in our file. Make sure to check the spelling or check the file to see if the name is different from what it is now"
#         return txt


# def delete(fct, cnx, cursor, response, channel, dlt_fnd):
#     if fct == 0: 
#         if (response.content.lower() == 'yes') | (response.content.lower() == 'yeah') | (response.content.lower() == 'sure') | (response.content.lower() == 'y'):
#             dlt_name = dlt_fnd[1].replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")

#             sql = f"DROP TABLE IF EXISTS channel_{dlt_fnd[0]}"
#             cursor.execute(sql)

#             sql = f"DELETE FROM channels WHERE Name LIKE '{dlt_name}'"
#             cursor.execute(sql)
#             cnx.commit()

#             cursor.close()
#             cnx.close()
#             txt = f"The channel **{dlt_name}** is no longer an art thread. Changes may take a moment to take affect"
#             return txt
#         else:
#             cursor.close()
#             cnx.close()
#             txt = f"Since you did not verify, **{dlt_fnd[1]}** will be kept as an art thread"
#             return txt
#     elif fct == 1:
#         if (response.content.lower() == 'yes') | (response.content.lower() == 'yeah') | (response.content.lower() == 'sure') | (response.content.lower() == 'y'):
#             dlt_name = dlt_fnd[1].replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")

#             sql = f"DELETE FROM channel_{channel[0]} WHERE Name LIKE '{dlt_name}'"
#             cursor.execute(sql)

#             sql = f"UPDATE channels SET Amount_of_tags_selected = {channel[2] - 1} WHERE Channel_ID = {channel[0]}"
#             cursor.execute(sql)
#             cnx.commit()

#             cursor.close()
#             cnx.close()
#             txt = f"The tag **{dlt_name}** has been removed from **{channel[1]}**. Changes may take a moment to take affect"
#             return txt
#         else:
#             cursor.close()
#             cnx.close()
#             txt = f"Since you did not verify, **{dlt_fnd[1]}** will be kept"
#             return txt
#     elif fct == 2:
#         None