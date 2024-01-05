import discord
from redbot.core import commands, Config
from discord.ext import tasks
from .lib import battlemetrics

class BattleMetricsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=3859612489, force_registration=True)
        default_guild = {
            "servers": []
        }
        self.config.register_guild(**default_guild)
        self.update_server_info.start()

    async def send_debug_message(self, message):
        debug_channel = self.bot.get_channel(CHANNEL_ID)
        if debug_channel:
            await debug_channel.send(message)

    @tasks.loop(minutes=30)
    async def update_server_info(self):
        for guild in self.bot.guilds:
            async with self.config.guild(guild).servers() as servers:
                if not servers:
                    continue
            
                for server in servers:
                    try:
                        bmapi = battlemetrics
                        await bmapi.setup(server['bearer_token'])

                        response = await bmapi.server_info(server['battlemetrics_server_id'])
                        if 'data' in response:
                            server_info = response['data']['attributes']
                            online_status = server_info.get('status', 'N/A')

                            embed = discord.Embed(title="Server Info", color=0xF3A316)
                            embed.add_field(name="Server Name", value=server_info.get('name', 'N/A'))
                            embed.add_field(name="Players Online", value=f"{server_info.get('players', 0)}/{server_info.get('maxPlayers', 0)}")
                            embed.add_field(name="Map", value=server_info.get('details', {}).get('map', 'N/A'))
                            embed.add_field(name="Status", value=online_status)
                            embed.set_image(url=server['embed_image_url'])

                            if 'modNames' in server_info.get('details', {}) and 'modLinks' in server_info.get('details', {}):
                                mod_strings = [f"[{mod_name}]({mod_link})" for mod_name, mod_link in zip(server_info['details']['modNames'], server_info['details']['modLinks'])]
                                mod_text = ""
                                field_count = 0
                                for mod_string in mod_strings:
                                    if len(mod_text) + len(mod_string) + 1 > 1024:
                                        embed.add_field(name=f"Mods (Part {field_count + 1})", value=mod_text, inline=False)
                                        mod_text = mod_string + "\n"
                                        field_count += 1
                                    else:
                                        mod_text += mod_string + "\n"
                                if mod_text:
                                    embed.add_field(name=f"Mods (Part {field_count + 1})", value=mod_text, inline=False)
                            else:
                                embed.add_field(name="Mods", value="No mod information available", inline=False)

                            channel = self.bot.get_channel(server['discord_channel_id'])
                            if channel is None:
                                await self.send_debug_message("Channel not found!")
                                continue

                            if server.get('message_id'):
                                try:
                                    message = await channel.fetch_message(server['message_id'])
                                    await message.edit(embed=embed)
                                except discord.NotFound:
                                    message = await channel.send(embed=embed)
                                    server['message_id'] = message.id
                            else:
                                message = await channel.send(embed=embed)
                                server['message_id'] = message.id

                    except Exception as e:
                        await self.send_debug_message(f"Error updating server info: {e}")
                        
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def setserver(self, ctx, battlemetrics_server_id: str, discord_channel_id: int, bearer_token: str, embed_image_url: str):
        """Sets the server configuration."""
        new_server = {
            "battlemetrics_server_id": battlemetrics_server_id,
            "discord_channel_id": discord_channel_id,
            "bearer_token": bearer_token,
            "embed_image_url": embed_image_url,
            "message_id": None
        }
        async with self.config.guild(ctx.guild).servers() as servers:
            servers.append(new_server)
        await ctx.send("Server configuration added.")
            
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def rcon(self, ctx, server_id: str, *, command: str):
        """Sends an RCON command to the specified server."""
        bmapi = battlemetrics

        servers = await self.config.guild(ctx.guild).servers()
        server_config = next((s for s in servers if s['battlemetrics_server_id'] == server_id), None)

        if server_config is None:
            await ctx.send("Server configuration not found.")
            return

        await bmapi.setup(server_config['bearer_token'])
        response = await bmapi.server_send_console_command(server_id=server_id, command=command)

        if 'errors' in response:
            error_message = f"There was an error with that command!\n**RESPONSE**\n{response['errors'][0]['detail']}"
            await ctx.send(f"{ctx.author.mention} something went wrong:\n{error_message}")
        else:
            result_message = f"Successfully ran the command!\n**RESULTS**\n{response['data']['attributes']['result']}"
            await ctx.send(result_message)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def banlist(self, ctx, battlemetrics_server_id: str):
        """Fetches and displays the ban list for the specified server."""
        servers = await self.config.guild(ctx.guild).servers()
        server_config = next((s for s in servers if s['battlemetrics_server_id'] == battlemetrics_server_id), None)

        if server_config is None:
            await ctx.send("Server configuration not found.")
            return

        try:
            bmapi = battlemetrics
            await bmapi.setup(server_config['bearer_token'])
            response = await bmapi.ban_list(battlemetrics_server_id)

            if 'data' in response:
                ban_list = response['data']
                response_message = "Ban List:\n"
                for ban in ban_list:
                    reason = ban['attributes'].get('reason', 'No reason provided')
                    response_message += f"- {reason}\n"

                await ctx.send(response_message)
            else:
                await ctx.send("No ban list data found.")
        except Exception as e:
            await ctx.send(f"Error fetching ban list: {e}")
            
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def clearservers(self, ctx):
        """Clears all server configurations."""
        await self.config.guild(ctx.guild).servers.set([])
        await ctx.send("All server configurations have been cleared.")


    @update_server_info.before_loop
    async def before_update_server_info(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.update_server_info.cancel()