import os
import re
from sys import platform
from datetime import datetime
from regex import regex

async def bot_help(message, op_userfile):
    """ Provides a list of commands to the user """
    response = "```yaml\n" \
               "Standard_Commands:\n" \
               "    status: Shows the status of " \
               "the server\n"
    
    response += "```"
    await message.channel.send(response)

