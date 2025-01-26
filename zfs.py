import discord
import subprocess

def zfs_pool_status():
    state_result = subprocess.run("zpool status | grep state:", capture_output=True, shell=True, text=True)
    pool_state = state_result.stdout.replace("state:", "").strip().capitalize()

    status_flag = discord.Status.online

    match pool_state:
        case "Online":
            status_flag = discord.Status.online
        case "Degraded":
            status_flag = discord.Status.idle
        case _:
            status_flag = discord.Status.do_not_disturb

    scan_result = subprocess.run("zpool status | grep scan:", capture_output=True, shell=True, text=True)
    pool_scan = scan_result.stdout.replace("scan:", "").strip().capitalize()

    message = pool_state

    match pool_scan:
        case "Resilvering":
            status_flag = discord.Status.idle
            message = pool_scan
    
    return {"status_flag" : status_flag, "status_message" : message}
            