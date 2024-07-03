import os
import math
import asyncio
from urllib.error import HTTPError
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
from paginator import PaginatorView
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, JavascriptException
from selenium.webdriver.support import expected_conditions as EC
import discord
import typing
from typing import List, Optional 
from bot_token import safebooru_bot
from discord import app_commands
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
art_shows = []

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!") 
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    
    # if artShow.is_running() != True: 
    #     for guild in bot.guilds:
    #         print(guild.id)
    #         asyncio.create_task(artShow.start(guild.id))

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
        cursor.execute("DROP TABLE IF EXISTS channels;")
        cursor.execute("Create TABLE channels(Row_ID INT NOT NULL AUTO_INCREMENT, Channel_ID VARCHAR(32), Name VARCHAR(48), Amount_of_tags_selected INT, PRIMARY KEY (Row_ID));")
        cursor.close()
    cnx.commit()
    cnx.close()

@bot.tree.command(description="Sets the current channel as an art thread")
async def set_art_thread(interaction: discord.Interaction):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )
    channel_id = "channel_" + str(interaction.channel_id)
    
    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{interaction.guild_id};")
        cursor.execute('SHOW TABLES')
        table_names = [table[0] for table in cursor.fetchall()]

        if channel_id in table_names:
            await interaction.response.send_message("Silly. This channel is already a designated place for art", ephemeral=True)
        else:
            cursor.execute(f"Create TABLE {channel_id}(ID INT NOT NULL, Name VARCHAR(256), Category VARCHAR(256), Type VARCHAR(16), Link VARCHAR(2400), Latest_art VARCHAR(240), PRIMARY KEY(ID));")
            sql = "INSERT INTO channels (Channel_ID, Name, Amount_of_tags_selected) VALUES (%s, %s, %s)"
            row = (interaction.channel_id, interaction.channel.name, 0)
            cursor.execute(sql, row)
            cnx.commit()
            
            await interaction.response.send_message("This channel has been set as a location for art", ephemeral=True)
        cursor.close()
    cnx.close()

@bot.tree.command(description="Deletes an art thread that was created. Any tags in it will be lost as well")
@app_commands.describe(channel = "Enter the name of the channel that you no longer want as an art thread. If left empty, it will delete the current channel's art thread")
async def delete_art_thread(interaction: discord.Interaction, channel: Optional[str]):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    if channel == None:
        channel = interaction.channel.name
    dlt_channel = channel.lower()

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{interaction.guild_id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        row_ids = [i[1] for i in artThreads]
        dlt_fnd = []

        if dlt_channel in row_ids:
            dlt_fnd = artThreads[row_ids.index(dlt_channel)]
            dlt_name = dlt_fnd[1].replace("_", "\_")

            sql = f"DROP TABLE IF EXISTS channel_{dlt_fnd[0]}"
            cursor.execute(sql)

            sql = f"DELETE FROM channels WHERE Name LIKE '{dlt_name}'"
            cursor.execute(sql)
            cnx.commit()

            cursor.close()
            cnx.close()
            await interaction.response.send_message(f"The channel **{dlt_name}** is no longer an art thread. Changes may take a moment to take affect", ephemeral=True)

        else:
            cursor.close()
            cnx.close()
            await interaction.response.send_message(f"The channel **{dlt_channel}** does not exist in our file. Make sure to check the spelling or check the file to see if the name is different from what it is now", ephemeral=True)

@bot.tree.command(description="Shows all the art threads and the number of tags added to them")
async def see_art_threads(interaction: discord.Interaction):
    # Maybe keep the code that evens out the text (despite it not being by much or at all)
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )
    
    threads = []#["### __Channel Name | Number of tags added__"] #[]
    #max_name_len = 0
    if cnx.is_connected():
        cursor = cnx.cursor()  
        cursor.execute(f"USE server_{interaction.guild_id};")
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

    thread_chunks = [threads[i * 5:(i + 1) * 5] for i in range((len(threads) + 5 - 1) // 5)]
    embeds = []

    for i in discord.utils.as_chunks(thread_chunks, 1):
        embed = discord.Embed()

        for j in i:
            k = "\n".join(j)
            embed.add_field(name="__Channel Name | Number of tags added__", value=f"{k}")

        embeds.append(embed)

    view = PaginatorView(embeds)
    await interaction.response.send_message(embed=view.initial, view=view)

@bot.tree.command(description="Changes the amount of tags collected from the search")
@app_commands.describe(value = "Enter a number from 5-25")
async def change_limit(interaction: discord.Interaction, value: app_commands.Range[int, 5, 25]):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )
    
    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{interaction.guild_id};")
        sql = f"UPDATE settings SET List_limit = {value} WHERE ID = 1"
        cursor.execute(sql)
        cnx.commit()

        cursor.close()
        cnx.close()
    await interaction.response.send_message(f"The amount of tags found from the search command is now set to {value}", ephemeral=True)                   

async def type_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    for type_choice in ["general", "artist", "character", "copyright", "metadata"]:
        if current.lower() in type_choice.lower():
            data.append(app_commands.Choice(name = type_choice, value = type_choice))
    return data

@bot.tree.command(description="Search for the tag you want to possibly add") #
@app_commands.autocomplete(type=type_autocomplete)
@app_commands.describe(name = "The name of the tag you are looking for. Avoid using underscores(_)", category = "Dont recommend using this till you have a solid understanding of how it works. Use underscores to connect titles. Ex. one_piece fate_zero", type = "What the tag is based on")
async def search(interaction: discord.Interaction, name: Optional[str], category: Optional[str], type: Optional[str]):#ctx):
    c_type = []

    if name != None:
        name = name.lower().split()
    else:
        name = []
    if category != None:
        category = category.lower().split()
    else:
        category = []
    if type != None:
        c_type = type.lower().split()

    error_text = []

    if len(name) > 24:
        error_text.append(f"You exceeded the amount of words for the **name** by {len(name) - 24}. Make sure to use at most 24 words when searching with the **name**")
    if len(category) > 4:
        error_text.append(f"You exceeded the amount of words for the **category** by {len(category) - 4}. Make sure to use at most 4 words when searching with the **category**")
    if len(c_type) > 1:
        error_text.append(f"You exceeded the amount of words for the **type** by {len(c_type) - 1}. Make sure to use only 1 word when searching the **type**")

    if len(error_text) > 0:
        await interaction.response.send_message('\n \n'.join(error_text), ephemeral=True)
    else:
        srch = []
        slct = []

        if len(name) > 0:
            col_value = 1
            for i in name:
                j = i.replace('"', '\"').replace("'", "\'").replace("_", "\_").replace("%", "\%")
                srch.append(f"'{j}' LIKE Name_{col_value}")
                slct.append(f"Name_{col_value}")
                col_value += 1
        if len(category) > 0:
            col_value = 1
            for i in category:
                j = i.replace('"', '\"').replace("'", "\'").replace("_", "\_").replace("%", "\%")
                srch.append(f"Category_{col_value} LIKE '{j}' ")
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
            cursor.execute(f"USE server_{interaction.guild_id};")
            sql = f"SELECT List_limit FROM settings"
            cursor.execute(sql)
            limit = cursor.fetchone()[0]
            
            #print(srch)
            #print(' AND '.join(srch))
            cursor.execute(f"USE safebooru_info;")
            sql = f"SELECT * FROM safebooru_tags WHERE {' AND '.join(srch)} LIMIT {limit}"
            cursor.execute(sql)
            tags = cursor.fetchall()
            cursor.close()
            cnx.close()
            
            #print(tags)
            list_tags = []#["### __ID | Name | Category | Type | Link__"]

            if len(tags) != 0:
                #print(tags)
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

                # Here is where the embed will need to take affect
                list_title = "__ID | Name | Category | Type | Link__"
                tag_chunks = [list_tags[i * 5:(i + 1) * 5] for i in range((len(list_tags) + 5 - 1) // 5)]
                # print(tag_chunks)
                embeds = []
                for chunk in discord.utils.as_chunks(tag_chunks, 1):
                    embed = discord.Embed()
                    
                    
                    for tags in chunk:
                        #print(len(tags))
                        #  for tag in tags:
                        #tags = tags.split("|")
                        #print(tags)

                        id_max  = max(len(i.split("|")[0]) for i in tags)
                        name_max = max(len(i.split("|")[1]) for i in tags)
                        category_max = max(len(i.split("|")[2]) for i in tags)
                        type_max = max(len(i.split("|")[3]) for i in tags)
                        # id_max  = max(len(i[0]) for i in tags)
                        # name_max = max(len(i[1]) for i in tags)
                        # category_max = max(len(i[2]) for i in tags)
                        # type_max = max(len(i[3]) for i in tags)
                        #title = list_title[:]
                        tags.insert(0, list_title)
                        #print(tags)
                        x = 0
                        #print(len(tags))
                        #tags_splt = tags.split("|")
                        for tag in tags:
                        # for i in range(0, len(list_tags)):
                        #     cols = list_tags[i].split("|")
                        #     if len(cols[0]) < id_max:
                        #         cols[0] += "\_" * (id_max - len(cols[0]))
                        #     if len(cols[1]) < name_max:
                        #         cols[1] = "\_" * math.ceil((name_max - len(cols[1])) / 2) + cols[1] + "\_" * math.floor((name_max - len(cols[1])) / 2)
                        #     if len(cols[2]) < category_max:
                        #         cols[2] = "\_" * math.ceil((category_max - len(cols[2])) / 2) + cols[2] + "\_" * math.floor((category_max - len(cols[2])) / 2)
                        #     if len(cols[3]) < type_max:
                        #         cols[3] = "\_" * math.ceil((type_max - len(cols[3])) / 2) + cols[3] + "\_" * math.floor((type_max - len(cols[3])) / 2)
                        #     list_tags[i] = '|'.join(cols)
                            #print(tag)
                            # tag[0] = f"{tag[0]} "
                            # tag[1] = f" {tag[1]} "
                            # tag[2] = f" {tag[2]} "
                            # tag[3] = f" {tag[3]} "
                            tag = tag.split("|")
                            if len(tag[0]) < id_max:
                                tag[0] += "\_" * (id_max - len(tag[0]))
                            if len(tag[1]) < name_max:
                                tag[1] = "\_" * math.ceil((name_max - len(tag[1])) / 2) + tag[1] + "\_" * math.floor((name_max - len(tag[1])) / 2)
                            if len(tag[2]) < category_max:
                                tag[2] = "\_" * math.ceil((category_max - len(tag[2])) / 2) + tag[2] + "\_" * math.floor((category_max - len(tag[2])) / 2)
                            if len(tag[3]) < type_max:
                                tag[3] = "\_" * math.ceil((type_max - len(tag[3])) / 2) + tag[3] + "\_" * math.floor((type_max - len(tag[3])) / 2)
                            #if x != 0:
                            #    tag[4] = " [Link](<" + tag[4].replace('_', '\_') + ">)"
                            tags[x] = "|".join(tag)
                            x += 1
                            #print(tag)
                            #print(x)
                        k = "\n".join(tags[1:])
                        embed.add_field(name=f"{tags[0]}", value=f"{k}")
                        #  tags
                    
                    
                    
                    
                    
                    #print(i)
                    # for tag in chunk:
                    #     print(f"\n \n{tag}")
                    #     k = "\n".join(tag)
                    #     embed.add_field(name=f"{list_title}", value=f"{k}")
                    #     print(len(k))
                        #print(embed)
                    #print(j)
                    embeds.append(embed)

                #print(len(embeds))
                view = PaginatorView(embeds)
                await interaction.response.send_message(embed=view.initial, view=view)




                # id_max  = max(len(i.split("|")[0]) for i in list_tags[1:])
                # name_max = max(len(i.split("|")[1]) for i in list_tags[1:])
                # category_max = max(len(i.split("|")[2]) for i in list_tags[1:])
                # type_max = max(len(i.split("|")[3]) for i in list_tags[1:])

                
                # for i in range(0, len(list_tags)):
                #     cols = list_tags[i].split("|")
                #     if len(cols[0]) < id_max:
                #         cols[0] += "\_" * (id_max - len(cols[0]))
                #     if len(cols[1]) < name_max:
                #         cols[1] = "\_" * math.ceil((name_max - len(cols[1])) / 2) + cols[1] + "\_" * math.floor((name_max - len(cols[1])) / 2)
                #     if len(cols[2]) < category_max:
                #         cols[2] = "\_" * math.ceil((category_max - len(cols[2])) / 2) + cols[2] + "\_" * math.floor((category_max - len(cols[2])) / 2)
                #     if len(cols[3]) < type_max:
                #         cols[3] = "\_" * math.ceil((type_max - len(cols[3])) / 2) + cols[3] + "\_" * math.floor((type_max - len(cols[3])) / 2)
                #     list_tags[i] = '|'.join(cols)

                # fnd_tags = '\n'.join(list_tags)
                # print(len(fnd_tags))
                # await interaction.response.send_message(f"{fnd_tags}")
            else:
                await interaction.response.send_message("I could not find anything on this search. If you need an example on how to search, use the /howToSearchandSelect command", ephemeral=True)

@bot.tree.command(description="Select the tag you want to add to an art thread")
@app_commands.describe(channel = "Enter the name of the channel you want to add the tag to. If left empty, it be added to the current channel", id_or_link = "Give the id or link of the tag you want to have added")
async def select(interaction: discord.Interaction, channel: Optional[str], id_or_link: str):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    if channel == None:
        channel = interaction.channel.name
    channel = channel.lower()

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{interaction.guild_id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        channels = cursor.fetchall()
        channel_names = [i[1] for i in channels]

        if channel in channel_names:
            channel_fnd = channels[channel_names.index(channel)]
            sql = f"SELECT ID, Name, Link FROM channel_{channel_fnd[0]}"
            cursor.execute(sql)
            tags = cursor.fetchall()

            if id_or_link.isnumeric():
                tag_id = int(id_or_link)
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

                        cursor.execute(f"USE server_{interaction.guild_id};")
                        sql = "INSERT INTO channel_" + channel_fnd[0] + " VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, clean_tag)
                        
                        sql = f"UPDATE channels SET Amount_of_tags_selected = {channel_fnd[2] + 1} WHERE Channel_ID = {channel_fnd[0]}"
                        cursor.execute(sql)

                        cnx.commit()
                        cursor.close()
                        cnx.close()
                        await interaction.response.send_message(f"The tag **{tag_name}** has been added to **{channel}**. I hope you enjoy the art it brings!", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"It would appear that there is no tag under **{tag_id}**", ephemeral=True)

                else:
                    cursor.close()
                    cnx.close()
                    tag = tags[tag_ids.index(tag_id)]
                    await interaction.response.send_message(f"It would appear that **{tag[1]}** has already been added to **{channel}**", ephemeral=True)
            else:
                srch_link = id_or_link.lower().replace("(", "%28").replace(")", "%29").replace("www.", "")
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

                            cursor.execute(f"USE server_{interaction.guild_id};")
                            sql = "INSERT INTO channel_" + channel_fnd[0] + " VALUES (%s, %s, %s, %s, %s, %s)"
                            cursor.execute(sql, clean_tag)

                            sql = f"UPDATE channels SET Amount_of_tags_selected = {channel_fnd[2] + 1} WHERE Channel_ID = {channel_fnd[0]}"
                            cursor.execute(sql)

                            cnx.commit()
                            cursor.close()
                            cnx.close()
                            await interaction.response.send_message(f"The tag **{tag_name}** has been added to **{channel}**. I hope you enjoy the art it brings!", ephemeral=True)
                        else:
                            await interaction.response.send_message(f"The [link](<{link}>) does not appear to have a tag connected to it. Make sure to check if it is the correct link", ephemeral=True)
                    else:
                        cursor.close()
                        cnx.close()
                        tag = tags[tag_links.index(link_fnd[0])]
                        await interaction.response.send_message(f"It would appear that **{tag[1]}** has already been added to **{channel}**", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Make sure the link you provided is the full url, spelt correctly, and from safebooru posts", ephemeral=True)
        else:
            await interaction.response.send_message(f"It would appear **{channel}** does not exist in our list of channels. Make sure to either set that channel as an art thread, check the spelling, or if the channel's name has not changed when it was set as an art thread", ephemeral=True)

@bot.tree.command(description="Gives a step by step summary of the bot to make it work")
async def what_to_do(interaction: discord.Interaction):
    await interaction.response.send_message("1. First thing you want to do is /set_art_thread in a channel so that you can start adding tags to it\n" +
                                            "2. If you do not have the full url of the tag you want to view, you can use /search to look for it and use the link or ID given to it\n" +
                                            "3. With the tag found, use the url or ID with /select to add it to a channel that has been made into an art thread through /set_art_thread\n" +
                                            "4. Once you have all the tags you want select, you can then /start_art_show which will initate the bot to send the images you seleceted\n" +
                                            "5. When it is not searching or sending images, you can use /stop_art_show to stop it", ephemeral=True)

@bot.tree.command(description="Shows the tags that have been added to an art thread")
@app_commands.describe(channel = "Enter the name of the channel that you want to see. If left empty, the current channel will be selected")
async def see_tags_in_thread(interaction: discord.Interaction, channel: Optional[str]):
    # to prevent character limit issues. One solution is asking users which list they want to see labeled from 1-20. The amount of rows pulled by the database will be consistent. Likely about 15 per list succession
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    if channel == None:
        channel = interaction.channel.name
    channel = channel.lower()

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{interaction.guild_id};")
        sql = f"SELECT Channel_ID, Name FROM channels"
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        channel_names = [i[1] for i in artThreads]

        if channel in channel_names:
            channel_fnd = artThreads[channel_names.index(channel)]
            sql = f"SELECT ID, Name, Category, Type, Link FROM channel_{channel_fnd[0]}"
            cursor.execute(sql)
            all_tags = cursor.fetchall()
            cursor.close()
            cnx.close()

            list_title = ["__ID", "Name", "Category", "Type", " Link__"]

            if len(all_tags) > 0:
                list_tags = [[str(j) for j in i] for i in all_tags]
                tag_chunks = [list_tags[i * 5:(i + 1) * 5] for i in range((len(list_tags) + 5 - 1) // 5)]
                embeds = []

                for chunk in discord.utils.as_chunks(tag_chunks, 1):
                    embed = discord.Embed()

                    for tags in chunk:

                        id_max  = max(len(i[0]) for i in tags) + 1
                        name_max = max(len(i[1]) for i in tags) + 2
                        category_max = max(len(i[2]) for i in tags) + 2
                        type_max = max(len(i[3]) for i in tags) + 2
                        
                        tags.insert(0, list_title[:])

                        x = 0
                        for tag in tags:
                            tag[0] = f"{tag[0]} "
                            tag[1] = f" {tag[1]} "
                            tag[2] = f" {tag[2]} "
                            tag[3] = f" {tag[3]} "
                            if len(tag[0]) < id_max:
                                tag[0] += "\_" * (id_max - len(tag[0]))
                            if len(tag[1]) < name_max:
                                tag[1] = "\_" * math.ceil((name_max - len(tag[1])) / 2) + tag[1] + "\_" * math.floor((name_max - len(tag[1])) / 2)
                            if len(tag[2]) < category_max:
                                tag[2] = "\_" * math.ceil((category_max - len(tag[2])) / 2) + tag[2] + "\_" * math.floor((category_max - len(tag[2])) / 2)
                            if len(tag[3]) < type_max:
                                tag[3] = "\_" * math.ceil((type_max - len(tag[3])) / 2) + tag[3] + "\_" * math.floor((type_max - len(tag[3])) / 2)
                            if x != 0:
                                tag[4] = " [Link](<" + tag[4].replace('_', '\_') + ">)"
                            tags[x] = "|".join(tag)
                            x += 1
                        k = "\n".join(tags[1:])
                        embed.add_field(name=f"{tags[0]}", value=f"{k}")

                    embeds.append(embed)

                view = PaginatorView(embeds)
                await interaction.response.send_message(embed=view.initial, view=view)

            else:
                await interaction.response.send_message(f"There were no tags found in **{channel}**", ephemeral=True)
        else:
            cursor.close()
            cnx.close()
            await interaction.response.send_message(f"It seems **{channel}** not on our list of channels. Make sure to check the spelling or the file to see if the name is different from what it is now", ephemeral=True)

@bot.tree.command(description="Remove a tag from an art thread")
@app_commands.describe(channel = "Enter the name of the channel that you want to delete a tag from. If left empty, the current channel will be selected", id_or_link = "Give the id or link of the tag you want to have deleted")
async def delete_tag_in_thread(interaction: discord.Interaction, channel: Optional[str], id_or_link: str):
    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    if channel == None:
        channel = interaction.channel.name
    channel = channel.lower()

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{interaction.guild_id};")
        sql = f"SELECT Channel_ID, Name, Amount_of_tags_selected FROM channels"
        cursor.execute(sql)
        artThreads = cursor.fetchall()
        channel_names = [i[1] for i in artThreads]
        
        if channel in channel_names:
            channel_fnd = artThreads[channel_names.index(channel)]
            
            if id_or_link.isnumeric(): 
                sql = f"SELECT ID, Name FROM channel_{channel_fnd[0]}"
                cursor.execute(sql)
                tags = cursor.fetchall()
                tag_ids = [str(i[0]) for i in tags]

                if id_or_link in tag_ids:
                    dlt_fnd = tags[tag_ids.index(id_or_link)]
                    dlt_name = dlt_fnd[1].replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")

                    sql = f"DELETE FROM channel_{channel_fnd[0]} WHERE ID LIKE '{dlt_fnd[0]}'"
                    cursor.execute(sql)

                    sql = f"UPDATE channels SET Amount_of_tags_selected = {channel_fnd[2] - 1} WHERE Channel_ID = {channel_fnd[0]}"
                    cursor.execute(sql)
                    cnx.commit()

                    cursor.close()
                    cnx.close()
                    await interaction.response.send_message(f"The tag **{dlt_name}** has been removed from **{channel_fnd[1]}**. Changes may take a moment to take affect", ephemeral=True)
                else:
                    await interaction.response.send_message(f"The tag under **{id_or_link}** does not exist in **{channel_fnd[1]}**. Make sure to check whether the tag is in another channel or if its the correct number associated", ephemeral=True)
            else:
                sql = f"SELECT ID, Name, Link FROM channel_{channel_fnd[0]}"
                cursor.execute(sql)
                tags = cursor.fetchall()
                tag_ids = [i[2] for i in tags]

                link = id_or_link.replace("(", "%28").replace(")", "%29")

                if link in tag_ids:
                    dlt_fnd = tags[tag_ids.index(link)]
                    dlt_name = dlt_fnd[1].replace("_", "\_").replace("%", "\%").replace('"', '\"').replace("'", "\'")

                    sql = f"DELETE FROM channel_{channel_fnd[0]} WHERE ID LIKE '{dlt_fnd[0]}'"
                    cursor.execute(sql)

                    sql = f"UPDATE channels SET Amount_of_tags_selected = {channel_fnd[2] - 1} WHERE Channel_ID = {channel_fnd[0]}"
                    cursor.execute(sql)
                    cnx.commit()

                    cursor.close()
                    cnx.close()
                    await interaction.response.send_message(f"The tag **{dlt_name}** has been removed from **{channel_fnd[1]}**. Changes may take a moment to take affect", ephemeral=True)
                else:
                    await interaction.response.send_message(f"The [link](<{id_or_link}>) provided does not exist in **{channel_fnd[1]}**. Make sure to check whether the link is in another channel or that the full url was used", ephemeral=True)
        else:
            cursor.close()
            cnx.close()
            await interaction.response.send_message(f"The channel **{channel}** does not exist in our file. Make sure to check the spelling or check the file to see if the name is different from what it is now", ephemeral=True)

@bot.tree.command(description="Starts art_show. Runs every 2 hr once started. During the runs, other commands are not available")
async def start_art_show(interaction: discord.Interaction):
    await interaction.response.send_message("Starting the show", ephemeral=True)
    art_show.start(interaction.guild_id)

@bot.tree.command(description="Stops the art_show loop but has to be done while the art_show is sleeping")
async def stop_art_show(interaction: discord.Interaction):
    art_show.cancel()
    await interaction.response.send_message("Ending the show", ephemeral=True)

@tasks.loop(seconds=7200)
async def art_show(guild):
    await bot.fetch_guild(guild)

    cnx = mysql.connector.connect(
    host=host,
    user=user_2,
    password=password
    )

    if cnx.is_connected():
        cursor = cnx.cursor()
        cursor.execute(f"USE server_{guild};")
        sql = f"SELECT Channel_ID FROM channels"
        cursor.execute(sql)
        dirty_threads = cursor.fetchall()
        art_threads = [int(i[0]) for i in dirty_threads]
        
        for channel in art_threads:
            sql = f"SELECT ID, Link, Latest_art FROM channel_{channel}"
            cursor.execute(sql)
            tags = cursor.fetchall()
            tag_id = [i[0] for i in tags]
            link = [i[1] for i in tags]
            latest_art = [i[2] for i in tags]
        
            opt = webdriver.ChromeOptions()
            opt.add_argument("--incognito")
            opt.add_argument("disable-infobars")
            opt.add_argument("--disable-extensions")
            opt.add_argument("--disable-gpu")
            opt.add_argument("--disable-dev-shm-usage")
            opt.add_argument("--no-sandbox")
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
            opt.add_argument(f'user-agent={user_agent}')
            opt.add_argument("--headless=new")
            driver = webdriver.Chrome(options=opt)

            img_links = []
            latest_art_id = []
            for i in range(len(link)):
                driver.get(f"{link[i]}")
                wait = WebDriverWait(driver, 20)

                try:
                    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "content")))
                    page = driver.page_source
                    soup = BeautifulSoup(page, "lxml")
                    content = soup.find(class_="content")
                    if ("Search is overloaded" in content.text) | ("Nothing found" in content.text):
                        latest_art_id.append(latest_art[i])
                    else:
                        if latest_art[i] == "":
                            art = content.select("span")[0]
                            art_img = art.find("img")
                            latest_art_id.append(art.get("id"))
                            img_links.append(art_img["src"])
                        else:
                            art = content.select("span")[0]

                            if latest_art[i] != art.get("id"):
                                art = content.find_all("span")
                                art_ids = [k.get("id") for k in art]
                                lastest_arts = []

                                if latest_art[i] in art_ids:
                                    last_art_position = art_ids.index(latest_art[i])
                                    lastest_arts = art[:last_art_position]
                                else:
                                    lastest_arts = art[:]
                                for k in lastest_arts:
                                    art_img = k.find("img")
                                    img_links.append(art_img["src"])
                                latest_art_id.append(art_ids[0])
                            else:
                                latest_art_id.append(latest_art[i])
                except TimeoutException:
                    pass
            
            driver.close()
            driver.quit()

            img_links_no_dup = list(set(img_links))
            for k in img_links_no_dup:
                try:
                    urllib.request.urlretrieve(k.replace("thumbnails", "images").replace("thumbnail_", ""), os.getcwd() + "/image.png")
                    await bot.get_channel(channel).send("", file=discord.File("image.png"))
                except HTTPError:
                    try:
                        urllib.request.urlretrieve(k.replace("thumbnails", "samples").replace("thumbnail_", "sample_"), os.getcwd() + "/image.png")
                        await bot.get_channel(channel).send("", file=discord.File("image.png"))
                    except HTTPError:
                        try:
                            urllib.request.urlretrieve(k.replace("thumbnails", "images").replace("thumbnail_", "").replace("jpg", "png"), os.getcwd() + "/image.png")
                            await bot.get_channel(channel).send("", file=discord.File("image.png"))
                        except HTTPError:
                            urllib.request.urlretrieve(k.replace("thumbnails", "images").replace("thumbnail_", "").replace("jpeg", "png"), os.getcwd() + "/image.png")
                            await bot.get_channel(channel).send("", file=discord.File("image.png"))

            for x in range(len(tag_id)):
                sql = f"UPDATE channel_{channel} SET Latest_art = '{latest_art_id[x]}' WHERE ID = {tag_id[x]}"
                cursor.execute(sql)

            cnx.commit()
            
        cursor.close()
        cnx.close()

        
@bot.event 
async def on_message(ctx):
    if ctx.author == bot.user:
        return
    
# @artShow.before_loop
# async def before():
#         print('waiting...')
#         #await asyncio.sleep(60)
#         await bot.wait_until_ready()
#         print("done")

bot.run(safebooru_bot)