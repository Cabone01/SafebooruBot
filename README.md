# Safebooru

## Introduction

The goal of this project was to create a Discord bot that could be used on any server to send art based on a tag from the Safebooru website in the server’s channels. This will be done by having a database of tags the user can select from and add to their server’s database.    

**Languages/Tools**
* Python
* MySQL
* AWS RDS
* Selenium
* Beautiful Soup
* urllib
* Typing
* Discord

## Acquiring the data
Before I could begin making the Discord bot, I first had to have the data ready. The link for the data collected can be seen below. Since the data could not be downloaded, I created a script to scrape the data from the website. The values extracted from each tag were the main_category, name, and link associated with the tag. At the time of the scraping, the script acquired over 650,000 rows of data based on the previous values for the database. This was then made into a data frame for the next step.

## Transforming the data
This step was repeated several times as the project went through as new implementations or issues were found that were crucial to have fixed in this step. For example, the Discord bot had a command that allowed the user to search for the tag. This might not seem like an issue but how the names were stored was like this “jun_(pokemon)_(cosplay).” This looks to be a simple solution and to simply allow the query to select every record that had “jun" anywhere in it. The issue is that the intention is to have multiple servers be able to do this at the same time and to have the database be in the cloud using AWS RDS. As the bot gets added to more servers, this likely would slow the bot down and increase the costs of the database along with other issues.    
To minimize some of these issues, I separated the names into two parts. The first was the name which using the previous example would be “jun.” The second part was the category which would be any words within a parenthesis like “pokemon” and “cosplay.” A script was made that did this to the whole dataframe collected from the scrape. Once completed, a dataframe with columns of names from 1-24, categories from 1-4, type from the main_category, and the link was created.    

## Loading the data
So before the data could be loaded, a database was first made called safebooru_info. This database will be separate from all the servers' databases. Then a table was created with safebooru_tags using the same column names as before along with a primary ID which will be used later. Once the table was made, the dataframe was loaded into there. This table will remain unchanged with each month having new records added. The bot will use only this table to grab from to add to the server’s databases.    

## Creation of the Safebooru Bot
A lot can be said in this part of the process but to more easily understand it, I will explain how each part works and why it was implemented. The bot supports slash commands, allowing the user to more easily view all the available commands and see what values they have to or do not have to put to use. The bot has 11 commands, 2 events, and 1 task that will be discussed.    

**Event**
* on_ready: This event begins when the bot is booted up and makes sure the commands are synced and correct.
* on_guild_join: Discord servers are given the name guild. Each guild has a unique ID which I made full use of. When the bot joined a server, it created a database called server_ + the guild’s ID. Since the name of the server could change, I had to use the ID since that never changed. Then two extra tables were created called settings and channels. The settings table would hold a column called List_Limit which was a number limit of the amount of records that could be pulled from any table. A limit was made because the discord bot has a smaller maximum amount of characters it can send in a message. So the solution was to put a limit to prevent that error from occurring. Then the channel table would keep the channels that the users intend for the images to be sent to. The columns for this table were channel_id, name, and amount_of_tags_selected.     

**Commands**
* set_art_thread: The command sets the current channel as a location for the tags to be added to. In more specific details, it created a table within the server’s database labeled as channel_ + channel ID. Any tags grabbed from the main database can then be added to this table. This would also allow the bot to send only the images from the tags in the channel’s table into that channel. It was not possible to redo this command if a table was already up so that no duplicates or errors occurred.
* delete_art_thread: If a channel had a table in the server’s database, it was possible to delete it with this command. This would drop the table which would in turn remove all records within it. 
* see_art_threads: Now this is where the channels table is used. When this command is done, the columns name and amount_of_tags_selected are used to create a nicely formatted list for the user to view.
* change_limit: This command allows the user to change the amount of records that can be selected from the query. The max the user can put was 25 since that was around the point that errors were not being seen as much.
* search: For this command, the user was requested to put a value for one or all of the following: name, category, and type. It did not matter what was and not used as long as one of them was. Then with that value given, the bot would attempt to select any records based on the values. Once all the records were selected, it would nicely format the list from ID, name, category, type, and link. This list would then be shown to the user and they were able to click the link to verify it was the correct one and use either that or the ID to select the tag in another command.
* select: Using the ID or link, the user can add the tag to a channel’s table. Why only these two values can be used is easy to explain. Both the ID and link are unique which will prevent multiple similar named records from being added. 
* what_to_do: This simply gives the user a basic step-by-step of what they need to do to at least get the bot to grab tags and send images to the channels.
* see_tags_in_thread: This command would show the ID, names, category, type, and link of all the tags in a specific channel. This like before would be nicely formatted.
* delete_tag_in_thread: Since the user might want to remove a tag, this allows the user to delete a record of the tag from a channel’s table.
* start_art_show: This command shows the fruition of the work the bot has done and begins its primary function. Once done, the bot will begin a task called art_show which runs every 2 hrs. This task will be explained more below but to put it simply, the images from the tags will start to be sent into the server’s channels.
* stop_art_show: This command stops the art_show task and does not allow it to run anymore until the start_art_show is begun again.    

**Task**
* art_show: When this task is begun, it will grab every channel’s table created inside the server’s database and run through each one. It will open a browser using Selenium and BeautifulSoup scrape the latest images’ link of each record and store it in an array. Once all the image links are grabbed from a channel’s table, duplicates are removed and the latest image is used as the new placeholder for the next runs. Then using urllib, a request is made to retrieve the image and is then sent into the channel. This is done for each table until there is none left. This repeats every two hours until it is halted.

## Conclusion
With the bot completed and functioning properly, the bot is ready to be used in servers. It has already been added to a server and is regularly being used by the users with satisfactory results. This does not however mean the bot is done as more features or improvements are intended to be made in the future. As it is now, it is a significant improvement to what it once was before.

## Video Demo
https://github.com/Cabone01/SafebooruBot/assets/89541481/41fb4d73-2bed-4c76-9c76-a09acd899f1f    

## Links
[Safebooru Tags](https://safebooru.org/index.php?page=tags&s=list)

