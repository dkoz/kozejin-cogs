import base64
import os
import discord
from mcstatus import JavaServer
from redbot.core import commands
import re

class MinecraftServerInfo:
    @staticmethod
    def clean_motd(motd):
        return re.sub(r'§.', '', motd)

    @staticmethod
    def icon_handler(server_ip: str, icon_b64: str) -> str:
        if icon_b64.startswith("data:image/png;base64,"):
            icon_data = base64.b64decode(icon_b64.removeprefix("data:image/png;base64,"))
            directory = os.path.join(os.path.dirname(__file__), "server_icons")
            os.makedirs(directory, exist_ok=True)
            file_path = os.path.join(directory, f"{server_ip}_icon.png")
            with open(file_path, "wb") as f:
                f.write(icon_data)
            return file_path
        return None

    @staticmethod
    async def server_info(ctx, server_ip: str):
        try:
            await ctx.defer()
            server = JavaServer.lookup(server_ip)
            status = server.status()
            motd_cleaned = MinecraftServerInfo.clean_motd(status.description)
            online_players = status.players.online
            max_players = status.players.max

            embed = discord.Embed(
                title=f"Server Info: {server_ip}",
                description=motd_cleaned,
                color=discord.Color.green()
            )

            if online_players is not None and max_players is not None:
                embed.add_field(name="Online", value=f"{online_players}/{max_players}", inline=False)
            else:
                embed.add_field(name="Online", value="Data not available", inline=False)

            if status.players.sample:
                player_list = ", ".join([player.name for player in status.players.sample])
                embed.add_field(name="Players", value=player_list, inline=False)

            latency = server.ping()
            embed.add_field(name="Latency", value=f"{latency:.2f} ms", inline=False)

            if status.icon and status.icon.startswith("data:image"):
                icon_path = MinecraftServerInfo.icon_handler(server_ip, status.icon)
                if icon_path:
                    file = discord.File(icon_path, filename=f"{server_ip}_icon.png")
                    embed.set_thumbnail(url=f"attachment://{server_ip}_icon.png")
                    await ctx.send(embed=embed, file=file)
                    os.remove(icon_path)
            else:
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
