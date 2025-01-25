# BasicBot
# Code lifted from StockImage bot by meed223 with other minor contributors

import logging
import asyncio
import subprocess

import discord
import re

import Commands

logging.basicConfig(filename="log.txt", level=logging.DEBUG, filemode="w")

# Global Variables

intents = discord.Intents.all()
client = discord.Client(intents=intents)
TOKEN = ""
BOT_PREFIX = ""
BOT_CHANNEL = ""
STATUS_QUO = "Setup"

def get_file_var(var, content):
    find = re.findall("{}=.*$".format(var),content,re.MULTILINE)[0].replace("{}=".format(var), "")
    return find


def setup():
    """ Get token & prefix from file and assigns to variables """
    
    global TOKEN
    global BOT_PREFIX
    global BOT_CHANNEL

    file = open("config.cfg", "r")
    content = '\r'.join(file.readlines())
    file.close()
    TOKEN = get_file_var("TOKEN", content)
    BOT_PREFIX = get_file_var("BOT_PREFIX", content)
    BOT_CHANNEL = get_file_var("BOT_CHANNEL", content)

    logging.info(f"Bot token '{TOKEN}' and prefix '{BOT_PREFIX}' are set")


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
        result = subprocess.run("zpool status | grep state:", capture_output=True, shell=True, text=True)
        message = result.stdout.replace("state:", "").strip().capitalize()
        print(message)

        status_flag = discord.Status.online

        match message:
            case "Online":
                status_flag = discord.Status.online
            case "Degraded":
                status_flag = discord.Status.idle
            case _:
                status_flag = discord.Status.do_not_disturb

        if message != STATUS_QUO and STATUS_QUO != "Setup":
            print("state change")
            await send_bot_alert("```Zfs State Change\n----------------\n{}```".format(status_flag))

        STATUS_QUO = message

        await client.change_presence(status=status_flag,
                                        activity=discord.Activity(
                                            type=discord.ActivityType.playing,
                                            name="Status: {}".format(message)))

        await asyncio.sleep(15)

async def send_bot_alert(message):
    channel = await client.fetch_channel(BOT_CHANNEL)
    await channel.send(message)

@client.event
async def on_message(message):
    """  This is run when a message is received on any channel """
    author = message.author
    args = message.content.split(' ')

    if author != client.user and args[0].lower() == BOT_PREFIX:

        del args[0]

        command = "help"

        if len(args) > 0:
            command = args[0].lower()
            del args[0]

        if command == "help":
            await Commands.bot_help(message)
        else:
            await Commands.unrecognized_command(message)

def is_authorized(message):
    """ Checks user privileges """
    authorized = False
    for member in message.guild.members:
        if member.id == message.author.id:
            # Check this ID specifically
            for r in member.roles:
                if r.permissions.manage_guild:
                    authorized = True
                    break
    return authorized

if __name__ == "__main__":
    try:
        setup()
        client.run(TOKEN)
    except FileNotFoundError:
        logging.error("File was not found, "
                      "are you sure that 'token.txt' exists?")
