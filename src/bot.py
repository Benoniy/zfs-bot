import logging
import discord
import asyncio
import json
import datetime

import zfs


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
        self.LOGGING_FILE = "{}log.txt".format(self.CONFIG_DIR)

        # Open Logging File
        logging.basicConfig(filename="{}".format(self.LOGGING_FILE), level=logging.DEBUG, filemode="w")

        # Load and Create Settings
        self.CLIENT_SETTINGS = self.load_json(self.APP_SETTINGS_FILE)["client_settings"]
        self.DEFAULT_SERVER_SETTINGS = self.load_json(self.APP_SETTINGS_FILE)["default_server_settings"]
        
        try:
            self.SERVER_SETTINGS = self.load_json(self.SERVER_SETTINGS_FILE)
        except FileNotFoundError:
            open(self.SERVER_SETTINGS_FILE, "x")
        except json.decoder.JSONDecodeError:
            pass

        self.log_print("Bot token '{}' is set".format(self.CLIENT_SETTINGS["TOKEN"]))

        # ADDITIONAL SERVICES
        self.zfs_service = zfs.ZFS(self)


    #######################
    # LOGGING
    #######################
    def log_print(self, message):
        current_time = datetime.datetime.now().isoformat()
        log_message = "{}: {}".format(current_time, message)

        print(log_message)
        logging.info(log_message)


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
            presence_list = []
            presence_list.append(await self.zfs_service.presence_task())

            final_flag = discord.Status.online
            final_message = "Online"

            for presence in presence_list:
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
        args = message.content.split(' ')
        server_id = str(message.guild.id)

        if author != self.user:
            await self.set_default_settings(server_id)

            if self.SERVER_SETTINGS[server_id]["BOT_PREFIX"] in args[0].lower():
                command = args[0].lower().replace(self.SERVER_SETTINGS[server_id]["BOT_PREFIX"], "")

                try:
                    is_admin_command = False
                    if self.is_authorized(message):
                        match command:
                            case "set":
                                try:
                                    await self.set_server_setting(server_id, args[1].lower(), args[2].lower())
                                    await message.channel.send("{} successfully changed!".format(args[1]))
                                except:
                                    await message.channel.send("Error changing setting: {}!".format(args[1]))
                                is_admin_command = True
                            
                            case "test_alert":
                                await self.send_bot_alert("test!")
                                is_admin_command = True

                            case "zfs":
                                self.zfs_service.on_message(args)
                                is_admin_command = True

                    if not is_admin_command:
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
        for member in message.guild.members:
            if member.id == message.author.id:
                # Check this ID specifically
                for r in member.roles:
                    if r.permissions.manage_guild:
                        authorized = True
                        break
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
    set [setting] [value]
        bot_channel [channel_id] - Sets the location of bot alert messages
        bot_prefix [prefix]      - Sets the prefix used to access bot command, it's $ by default

    test_alert - Simulates an alert
    """

        # SERVICE COMMANDS
        command_string += """
Service Commands:"""
        command_string += self.zfs_service.help_string()
        command_string += """```"""
        await self.send_bot_alert(command_string)


if __name__ == "__main__":
    discord_intents = discord.Intents.all()
    MY_BOT = Bot(discord_intents)
    MY_BOT.run(MY_BOT.CLIENT_SETTINGS["TOKEN"])