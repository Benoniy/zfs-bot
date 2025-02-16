import discord
import subprocess

class ZFS():
    def __init__(self, discord_client):
        self.discord_client = discord_client
        self.STATUS_QUO = "Setup"

    def zfs_pool_status(self):
        try:
            state_result = subprocess.run("zpool status", capture_output=True, shell=True, text=True,)
            
            lines = state_result.stdout.split("\n")

            for line in lines:
                if "state" in line:
                    pool_state = line.replace("state:", "").strip().capitalize()

            status_flag = discord.Status.online

            match pool_state:
                case "Online":
                    status_flag = discord.Status.online
                case "Degraded":
                    status_flag = discord.Status.idle
                case _:
                    status_flag = discord.Status.do_not_disturb

            message = pool_state


            scan_result = subprocess.run("zpool status | grep scan:", capture_output=True, shell=True, text=True)
            pool_scan = scan_result.stdout.replace("scan:", "").strip().capitalize()

            match pool_scan:
                case "Resilvering":
                    status_flag = discord.Status.idle
                    message = pool_scan
            
            self.discord_client.log_print("ZFS reports state: {}, scan: {}".format(pool_state, pool_scan))
            return {"status_flag" : status_flag, "status_message" : message, "raw_output" : state_result.stdout}
        except UnboundLocalError:
            self.discord_client.log_print("No ZFS Available")
            return {"status_flag" : discord.Status.online, "status_message" : "No ZFS Available", "raw_output" : state_result.stdout}
    
    async def presence_task(self):
        zfs_status = self.zfs_pool_status()

        if zfs_status["status_message"] != self.STATUS_QUO and self.STATUS_QUO != "Setup":
            self.discord_client.log_print("ZFS State changed from {} to {}".format(self.STATUS_QUO, zfs_status["status_message"]))
            await self.discord_client.send_bot_alert("```Zfs Status Change\n----------------\n{}```".format(zfs_status["status_message"]))
        
        return zfs_status
    
    async def on_message(self, user_is_admin, command,  args):
        if user_is_admin and command == "zfs":
            arg = args[1].lower()
            match arg:
                case "status":
                    zfs_status = self.zfs_pool_status()
                    await self.discord_client.send_bot_alert("```Zfs Status\n----------------\n{}```".format(zfs_status["raw_output"]))
                    return True
        return False

    def help_string(self):
        return ""
    
    def admin_help_string(self):
        return """
    zfs [argument]
        status - Reports the state of all zfs pools
"""

