from service import Service

class Vintage(Service):
    def __init__(self, discord_client):
        super().__init__(discord_client)
        self.docker_interface = discord_client.services["docker"]
        self.container_name = "vintage-story-vs-server-1"

    async def on_message(self, user_is_admin, command,  args):
        if command == "vintage":
            arg = args[0].lower()
            print(arg)
            match arg:
                case "status":
                    await self.docker_interface.on_message(True, "docker", ["status", self.container_name])
                    return True
                case "start":
                    await self.docker_interface.on_message(True, "docker", ["start", self.container_name], False)
                    await self.discord_client.send_bot_alert("```Game Started!```")
                    return True
                case "stop":
                    await self.docker_interface.on_message(True, "docker", ["exec", self.container_name, "sh -c \"/var/vintage_story/server/server.sh command autosavenow\""], False)
                    await self.docker_interface.on_message(True, "docker", ["stop", self.container_name], False)

                    await self.discord_client.send_bot_alert("```Game Saved and Stopped!```")
                    return True
                case "save":
                    await self.docker_interface.on_message(True, "docker", ["exec", self.container_name, "sh -c \"/var/vintage_story/server/server.sh command autosavenow\""], False)
                    await self.discord_client.send_bot_alert("```Game Saved!```")
                    return True
        return False

    def help_string(self):
        return """
    vintage [argument]
        status - Reports the status of the vintage story server
        start - starts the server
        stop - stops the server
        save - saves the server state
"""

