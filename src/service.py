import discord

class Service():
    def __init__(self, discord_client):
        self.discord_client = discord_client

    async def presence_task(self):
        return {"status_flag" : discord.Status.online, "status_message" : "", "raw_output" : ""}
    
    async def on_message(self, user_is_admin, command,  args):
        return False

    def help_string(self):
        return ""

    def admin_help_string(self):
        return ""

