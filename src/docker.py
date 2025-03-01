from service import Service
import subprocess

class Docker(Service):
    def __init__(self, discord_client):
        super().__init__(discord_client)
    
    async def interpret_command(self, command, args=[], additions=""):
        command_args = " ".join(args)
        return subprocess.run("docker {} {} {}".format(command, command_args, additions), capture_output=True, shell=True, text=True).stdout.strip()

    async def on_message(self, user_is_admin, command,  args, send_notifications=True):
        if command == "docker" and user_is_admin:
            arg = args[0].lower()
            match arg:
                case "status":
                    output = await self.interpret_command("inspect", args[1:], "| jq .[0].State.Status")
                    if send_notifications:
                        await self.discord_client.send_bot_alert("```\"{}\" status: {}```".format(args[1], output))
                    return True
                case "start":
                    output = await self.interpret_command("start", args[1:])

                    if output == " ".join(args[1:]).strip():
                        if send_notifications:
                            await self.discord_client.send_bot_alert("```'{}' Started```".format(args[1]))
                    else:
                        await self.discord_client.send_bot_alert("```Error starting container\n{}```".format(output))
                    
                    return True
                case "stop":
                    output = await self.interpret_command("stop", args[1:])

                    if output == " ".join(args[1:]).strip():
                        if send_notifications:
                            await self.discord_client.send_bot_alert("```'{}' Stopped```".format(args[1]))
                    else:
                        await self.discord_client.send_bot_alert("```Error stopping container\n{}```".format(output))
                   
                    return True
                case "exec":
                    output = await self.interpret_command("exec -d", args[1:])
                    if send_notifications:
                        await self.discord_client.send_bot_alert("```Executing command on {}: {}\n```".format(args[1], args[2:]))
                    return True
        return False

    def admin_help_string(self):
        return """
    docker [argument]
        status [container_name] - Reports the status of a container
        start [container_name] - starts a container
        stop [container_name] - stops a container
        exec [container_name] [commands] - Run a command on a container 
"""
