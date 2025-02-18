import logging
from logging import handlers
import discord
import asyncio
import json

import zfs
import docker
import vintage

class Bot (discord.Client):

    def __init__(self, discord_intents):
        super().__init__(intents=discord_intents)
        # Global Variables
        self.CLIENT_SETTINGS = {}
        self.DEFAULT_SERVER_SETTINGS = {}
        self.SERVER_SETTINGS = {}

        # File Locations
        self.CONFIG_DIR = "config/"
        self.APP_SETTINGS_FILE = "{}app.json".format(self.CONFIG_DIR)
        self.SERVER_SETTINGS_FILE = "{}servers.json".format(self.CONFIG_DIR)
        self.USER_PERMISSIONS_FILE = "{}users.json".format(self.CONFIG_DIR)
        self.LOGGING_FILE = "{}log.txt".format(self.CONFIG_DIR)

        # Open Logging File
        root_logger = logging.getLogger()
        formatter   = logging.Formatter('%(asctime)s :%(levelname)s: %(message)s')
        log_handler = handlers.TimedRotatingFileHandler(filename="{}".format(self.LOGGING_FILE), when='midnight', interval=1, backupCount=7)
        log_handler.setFormatter(formatter)
        root_logger.addHandler(log_handler)
        root_logger.setLevel(logging.INFO)

        # Load and Create Settings
        self.CLIENT_SETTINGS = self.load_json(self.APP_SETTINGS_FILE)["client_settings"]
        self.DEFAULT_SERVER_SETTINGS = self.load_json(self.APP_SETTINGS_FILE)["default_server_settings"]
        
        self.SERVER_SETTINGS = self.collect_config(self.SERVER_SETTINGS_FILE)
        self.USER_PERMISSIONS = self.collect_config(self.USER_PERMISSIONS_FILE)

        self.log_print("Bot token '{}' is set".format(self.CLIENT_SETTINGS["TOKEN"]))

        # ADDITIONAL SERVICES
        self.services = {}
        self.services["zfs"] = zfs.ZFS(self)
        self.services["docker"] = docker.Docker(self)
        self.services["vintage"] = vintage.Vintage(self)


    def collect_config(self, file):
        try:
            return self.load_json(file)
        except FileNotFoundError:
            open(file, "x")
            self.save_json(file, {})
            return {}


    #######################
    # LOGGING
    #######################
    def log_print(self, message):
        print(message)
        logging.info(message)


    #######################
    # JSON FILES
    #######################
    def save_json(self, file_name, json_dict):
        json_data = json.dumps(json_dict, indent=4)
        file = open(file_name, "w")
        file.write(json_data)
        file.close()
        self.log_print("{} Saved json configuration".format(file_name))


    def load_json(self, file_name):
        file = open(file_name, "r")
        content = '\r'.join(file.readlines())
        json_data = json.loads(content)
        file.close()
        self.log_print("{} Loaded stored json configuration".format(file_name))
        return json_data
    

    # Set default per-server setting
    async def set_default_settings(self, server_id):
        if server_id not in self.SERVER_SETTINGS:
            self.SERVER_SETTINGS.update({str(server_id) : self.DEFAULT_SERVER_SETTINGS})
            self.save_json(self.SERVER_SETTINGS_FILE, self.SERVER_SETTINGS)


    # Set a per-server setting
    async def set_server_setting(self, server_id, setting, arg):
        allowed_settings = [ "bot_channel", "bot_prefix" ]

        if setting.lower() in allowed_settings:
            self.SERVER_SETTINGS[server_id].update({setting.upper() : arg})
        
        self.save_json(self.SERVER_SETTINGS_FILE, self.SERVER_SETTINGS)
    

    #######################
    # DISCORD EVENTS
    #######################
    async def on_ready(self):
        """ Set Discord Status """
        await self.change_presence(status=discord.Status.idle,
                                    activity=discord.Activity(
                                        type=discord.ActivityType.playing,
                                        name="Starting bot!"))
        
        await self.presence_task()


    async def presence_task(self):
        while True:
            final_flag = discord.Status.online
            final_message = "Online"

            for key in self.services:
                presence = await self.services[key].presence_task()
                if presence["status_flag"] == discord.Status.online:
                    pass
                else:
                    final_flag = presence["status_flag"]
                    final_message = presence["status_message"]
                    break

            await self.change_presence(status=final_flag,
                                            activity=discord.Activity(
                                                type=discord.ActivityType.playing,
                                                name="Status: {}".format(final_message)))

            await asyncio.sleep(15)
 

    async def on_message(self, message):
        """  This is run when a message is received on any channel """
        author = message.author
        
        server_id = str(message.guild.id)

        full_args = message.content.split(' ')
        init_command = full_args[0].lower()
        try:
            add_args = full_args[1:]
        except:
            add_args = []

        if author != self.user:
            await self.set_default_settings(server_id)

            if self.SERVER_SETTINGS[server_id]["BOT_PREFIX"] in init_command:
                command = init_command.replace(self.SERVER_SETTINGS[server_id]["BOT_PREFIX"], "")

                try:
                    user_is_admin = self.is_authorized(message)

                    # Admin Commands
                    if user_is_admin:
                        match command:
                            case "set":
                                try:
                                    await self.set_server_setting(server_id, add_args[0].lower(), add_args[1].lower())
                                    await message.channel.send("{} successfully changed!".format(add_args[0]))
                                except:
                                    await message.channel.send("Error changing setting: {}!".format(add_args[0]))
                                return
                            
                            case "userperm":

                                # Get arguments
                                try:
                                    user_name = add_args[1].lower()
                                    requested_permission = add_args[2].lower()

                                    if server_id not in self.USER_PERMISSIONS:
                                        self.USER_PERMISSIONS[server_id] = {}
                                    
                                    # Get user ID
                                    user_id = ""
                                    for member in message.guild.members:
                                        if str(member) == user_name:
                                            user_id = str(member.id)

                                    if user_id == "": raise IndexError # Prevents the creation of the "" user when an error occurs
                                    
                                    # Generate default user permissions
                                    if user_id not in self.USER_PERMISSIONS[server_id]:
                                        self.USER_PERMISSIONS[server_id][user_id] = []

                                except:
                                    user_name = ""
                                    requested_permission = ""


                                # handle commands that have arguments
                                match add_args[0]:
                                    case "add":
                                        if requested_permission not in self.USER_PERMISSIONS[server_id][user_id]:
                                            self.USER_PERMISSIONS[server_id][user_id].append(requested_permission)
                                    case "remove":
                                        if requested_permission in self.USER_PERMISSIONS[server_id][user_id]:
                                            self.USER_PERMISSIONS[server_id][user_id].remove(requested_permission)

                                    case "list":
                                        await self.send_bot_alert("```{}```".format(json.dumps(self.USER_PERMISSIONS[server_id], indent=4)))
                                        return
       
                                
                                self.save_json(self.USER_PERMISSIONS_FILE, self.USER_PERMISSIONS)
                                return

                            case "test_alert":
                                await self.send_bot_alert("test!")
                                return


                    # Service Commands
                    for key in self.services:
                        command_complete = await self.services[key].on_message(user_is_admin, command, add_args)
                        if command_complete:
                            return

                    if author.id == 191660743140048896:
                        await message.channel.send("https://media1.tenor.com/m/l-7hn0tafCgAAAAd/haha-you-have-no-power.gif")
                        return
                    
                    # User Commands
                    match command:
                        case _:
                            await self.send_help(message)



                except IndexError:
                    await message.channel.send("Argument not found!")


    #######################
    # HELPER METHODS
    #######################
    def is_authorized(self, message):
        """  Checks user privileges """
        authorized = False

        if message.author.id == message.guild.owner.id:
            authorized = True

        return authorized

    async def send_bot_alert(self, message):
        channel_ids = []
        for server in self.SERVER_SETTINGS:
            channel_ids.append(self.SERVER_SETTINGS[server]["BOT_CHANNEL"])

        set_channel_ids = set(channel_ids)
        for channel_id in set_channel_ids:
            channel = await self.fetch_channel(channel_id)
            await channel.send(message)


    async def send_help(self, message):

        # STANDARD COMMANDS
        command_string = """```
User Commands:
    help - Displays this guide
"""


        # ADMIN COMMANDS
        if self.is_authorized(message):
            command_string += """
Admin Commands:
    set [setting]
        bot_channel [channel_id] - Sets the location of bot alert messages
        bot_prefix [prefix]      - Sets the prefix used to access bot command, it's $ by default
    
    userperm [command]
        add [user] [permission]    - Adds a permission to a user
        remove [user] [permission] - Removes a permission from a user
        list                       - Lists all user ID's and their permissions

    test_alert - Simulates an alert
    """

        # SERVICE COMMANDS
        command_string += """
Service Commands:"""


        for key in self.services:
            if self.is_authorized(message):
                command_string += self.services[key].admin_help_string()
            print(self.services[key].help_string())
            command_string += self.services[key].help_string()
        command_string += """```"""
        await self.send_bot_alert(command_string)


if __name__ == "__main__":
    discord_intents = discord.Intents.all()
    MY_BOT = Bot(discord_intents)
    MY_BOT.run(MY_BOT.CLIENT_SETTINGS["TOKEN"])