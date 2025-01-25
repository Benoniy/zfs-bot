# BasicBot
# Code lifted from StockImage bot by meed223 with other minor contributors

import logging
import asyncio
import subprocess

import discord
from regex import regex

import Commands

logging.basicConfig(filename="log.txt", level=logging.DEBUG, filemode="w")

# Global Variables

intents = discord.Intents.all()
client = discord.Client(intents=intents)
TOKEN = ""
BOT_PREFIX = "£"


def setup():
    """ Get token & prefix from file and assigns to variables """
    file = open("token.txt", "r")
    global TOKEN
    TOKEN = file.readline().replace("\n", "")
    file.close()

    global BOT_PREFIX

    logging.info(f"Bot token '{TOKEN}' and prefix '{BOT_PREFIX}' are set")


# ---[ ZFS Checking Code ]---



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
    while True:
        result = subprocess.run("zpool status | grep state:", capture_output=True, shell=True, text=True)
        message = result.stdout.replace("state:", "").strip()
        print(message)

        status_flag = discord.Status.online

        match message:
            case "online":
                status_flag = discord.Status.online
            case "degraded":
                status_flag = discord.Status.idle
            case _:
                status_flag = discord.Status.do_not_disturb


        await client.change_presence(status=status_flag,
                                        activity=discord.Activity(
                                            type=discord.ActivityType.playing,
                                            name="Status: {}".format(message)))

        await asyncio.sleep(15)


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

        if command == "status":
            await Commands.server_status(message, True)
        elif command == "help":
            await Commands.bot_help(message)
        elif command == "start_server":
            await Commands.start_server(message)
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
