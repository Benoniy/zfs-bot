# BasicBot
# Code lifted from StockImage bot by meed223 with other minor contributors

import logging
import asyncio
import subprocess
import discord
import json

from settings import *
from zfs import *


# Global Variables
CLIENT_SETTINGS = {}
DEFAULT_SERVER_SETTINGS = {}
SERVER_SETTINGS = {}
STATUS_QUO = "Setup"

# File Locations
CONFIG_DIR = "config/"
APP_SETTINGS_FILE = "{}app.json".format(CONFIG_DIR)
SERVER_SETTINGS_FILE = "{}servers.json".format(CONFIG_DIR)
LOGGING_FILE = "{}log.txt".format(CONFIG_DIR)

intents = discord.Intents.all()
client = discord.Client(intents=intents)

logging.basicConfig(filename="{}".format(LOGGING_FILE), level=logging.DEBUG, filemode="w")

def setup():
    """ Get token & prefix from file and assigns to variables """
    
    global CLIENT_SETTINGS
    global DEFAULT_SERVER_SETTINGS
    global SERVER_SETTINGS

    CLIENT_SETTINGS = load_json(APP_SETTINGS_FILE)["client_settings"]
    DEFAULT_SERVER_SETTINGS = load_json(APP_SETTINGS_FILE)["default_server_settings"]
    
    try:
        SERVER_SETTINGS = load_json(SERVER_SETTINGS_FILE)
    except FileNotFoundError:
        open(SERVER_SETTINGS_FILE, "x")
    except json.decoder.JSONDecodeError:
        pass

    logging.info(f"Bot token '{CLIENT_SETTINGS["TOKEN"]}' is set")


# ---[ Bot Event Code ]---
@client.event
async def on_ready():
    """ Set Discord Status """
    logging.info("Bot is Ready")
    print("Bot is Ready")
    await client.change_presence(status=discord.Status.idle,
                                 activity=discord.Activity(
                                     type=discord.ActivityType.playing,
                                     name="Starting bot!"))
    
    
    await presence_task()


async def presence_task():
    global STATUS_QUO
    while True:
        zfs_status = zfs_pool_status()


        if zfs_status["status_message"] != STATUS_QUO and STATUS_QUO != "Setup":
            print("state change")
            await send_bot_alert("```Zfs State Change\n----------------\n{}```".format(zfs_status["status_flag"]))

        STATUS_QUO = zfs_status["status_message"]

        await client.change_presence(status=zfs_status["status_flag"],
                                        activity=discord.Activity(
                                            type=discord.ActivityType.playing,
                                            name="Status: {}".format(zfs_status["status_message"])))

        await asyncio.sleep(15)



async def send_bot_alert(message):
    channel_ids = []
    for server in SERVER_SETTINGS:
        channel_ids.append(SERVER_SETTINGS[server]["BOT_CHANNEL"])

    set_channel_ids = set(channel_ids)
    for channel_id in set_channel_ids:
        channel = await client.fetch_channel(channel_id)
        await channel.send(message)



# Set default per-server setting
async def set_default_settings(server_id):
    if server_id not in SERVER_SETTINGS:
        SERVER_SETTINGS.update({str(server_id) : DEFAULT_SERVER_SETTINGS})
        save_json(SERVER_SETTINGS_FILE, SERVER_SETTINGS)

# Set a per-server setting
async def set_server_setting(server_id, setting, arg):
    allowed_settings = [ "bot_channel", "bot_prefix" ]

    if setting.lower() in allowed_settings:
        SERVER_SETTINGS[server_id].update({setting.upper() : arg})
    
    save_json(SERVER_SETTINGS_FILE, SERVER_SETTINGS)



@client.event
async def on_message(message):
    """  This is run when a message is received on any channel """
    author = message.author
    args = message.content.split(' ')
    server_id = str(message.guild.id)

    if author != client.user:
        await set_default_settings(server_id)

        if SERVER_SETTINGS[server_id]["BOT_PREFIX"] in args[0].lower():
            command = args[0].lower().replace(SERVER_SETTINGS[server_id]["BOT_PREFIX"], "")

            try: 
                match command:
                    case "set":
                        try:
                            await set_server_setting(server_id, args[1].lower(), args[2].lower())
                            await message.channel.send("{} successfully changed!".format(args[1]))
                        except:
                            await message.channel.send("Error changing setting: {}!".format(args[1]))
                    case "test_alert":
                        await send_bot_alert("test!")

            except IndexError:
                await message.channel.send("Argument not found!")
        


if __name__ == "__main__":
    setup()
    client.run(CLIENT_SETTINGS["TOKEN"])
