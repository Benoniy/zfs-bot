import discord
import subprocess

class Vintage():
    def __init__(self, discord_client):
        self.discord_client = discord_client
        self.container_name = "vintage-story-vs-server-1"

    async def presence_task(self):
        return {"status_flag" : discord.Status.online, "status_message" : "", "raw_output" : ""}
    
    async def is_running(self):
        return subprocess.run("docker inspect {} | jq .[0].State.Status".format(self.container_name), capture_output=True, shell=True, text=True).stdout

    async def start(self):
        return subprocess.run("docker start {}".format(self.container_name), capture_output=True, shell=True, text=True).stdout

    async def stop(self):
        return subprocess.run("docker stop {}".format(self.container_name), capture_output=True, shell=True, text=True).stdout


    async def on_message(self, user_is_admin, command,  args):
        if user_is_admin and command == "vintage":
            arg = args[1].lower()
            match arg:
                case "status":
                    status = await self.is_running()
                    await self.discord_client.send_bot_alert("```Vintage Story Status\n--------------------------\n{}```".format(status))
                    return True
                case "start":
                    await self.discord_client.send_bot_alert("```Starting```")
                    await self.start()
                    return True
                case "stop":
                    await self.discord_client.send_bot_alert("```Stopping```")
                    await self.stop()
                    return True
        return False

    def help_string(self):
        return """
    vintage [argument]
        status - Reports the status of the vintage story server
        start - starts the server
        stop - stops the server
"""

    def admin_help_string(self):
        return ""

