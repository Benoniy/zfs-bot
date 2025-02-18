import discord
import subprocess

class Docker():
    def __init__(self, discord_client):
        self.discord_client = discord_client

    async def presence_task(self):
        return {"status_flag" : discord.Status.online, "status_message" : "", "raw_output" : ""}
    
    async def interpret_command(self, command, args=[], additions=""):
        command_args = " ".join(args)
        print("docker {} {} {}".format(command, command_args, additions))
        return subprocess.run("docker {} {} {}".format(command, command_args, additions), capture_output=True, shell=True, text=True).stdout

    async def on_message(self, user_is_admin, command,  args):
        if command == "docker" and user_is_admin:
            arg = args[0].lower()
            match arg:
                case "status":
                    print("status")
                    output = await self.interpret_command("inspect", args[1], "| jq .[0].State.Status")
                    await self.discord_client.send_bot_alert("```Container Status\n--------------------------\n{}```".format(output))
                    return True
                case "start":
                    await self.discord_client.send_bot_alert("```Starting```")
                    output = await self.interpret_command("start", args[1])
                    await self.discord_client.send_bot_alert("```Started```")
                    return True
                case "stop":
                    await self.discord_client.send_bot_alert("```Stopping```")
                    output = await self.interpret_command("stop", args[1])
                    await self.discord_client.send_bot_alert("```Stopped```")
                    return True
        return False

    def help_string(self):
        return ""

    def admin_help_string(self):
        return """
    docker [argument]
        status [container_name] - Reports the status of a container
        start [container_name] - starts a container
        stop [container_name] - stops a container
"""

