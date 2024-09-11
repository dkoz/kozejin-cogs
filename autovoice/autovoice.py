import discord
from redbot.core import commands, Config
from .control import (
    ChannelControlView,
    LockChannelButton,
    UnlockChannelButton
)

class AutoVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=3498571294, force_registration=True)
        default_guild = {
            "trigger_channel_id": None,
            "control_channel_id": None,
            "control_message_id": None
        }
        self.config.register_guild(**default_guild)
        self.bot.created_channels = set()

    async def save_control_message(self, guild, message_id):
        await self.config.guild(guild).control_message_id.set(message_id)

    async def load_control_message(self, guild):
        return await self.config.guild(guild).control_message_id()

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            control_channel_id = await self.config.guild(guild).control_channel_id()
            control_message_id = await self.load_control_message(guild)
            if control_channel_id:
                control_channel = self.bot.get_channel(control_channel_id)
                if control_channel:
                    if control_message_id:
                        try:
                            message = await control_channel.fetch_message(control_message_id)
                        except discord.NotFound:
                            message = None
                    else:
                        message = None

                    if not message:
                        await self.send_control_message(control_channel, guild)
                    else:
                        view = ChannelControlView(self.bot)
                        view.add_item(LockChannelButton())
                        view.add_item(UnlockChannelButton())
                        await message.edit(view=view)

    async def send_control_message(self, channel, guild):
        view = ChannelControlView(self.bot)
        view.add_item(LockChannelButton())
        view.add_item(UnlockChannelButton())
        embed = discord.Embed(title="Channel Management", description="Use the buttons below to control your channel.")
        message = await channel.send(embed=embed, view=view)
        await self.save_control_message(guild, message.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        trigger_channel_id = await self.config.guild(member.guild).trigger_channel_id()
        if after.channel and after.channel.id == trigger_channel_id:
            new_channel = await member.guild.create_voice_channel(name=f"{member.display_name}'s channel", category=after.channel.category)
            self.bot.created_channels.add(new_channel.id)
            await member.move_to(new_channel)
        elif before.channel and len(before.channel.members) == 0 and before.channel.id in self.bot.created_channels:
            await before.channel.delete()
            self.bot.created_channels.remove(before.channel.id)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(name="autovoiceset", aliases=["avs"], invoke_without_command=True)
    async def autovoiceset(self, ctx):
        """Commands for autoroom"""
        await ctx.send_help(ctx.command)

    @autovoiceset.command()
    async def trigger(self, ctx, channel: discord.VoiceChannel):
        """Set the voice channel that triggers a new voice channel to be created."""
        await self.config.guild(ctx.guild).trigger_channel_id.set(channel.id)
        await ctx.send(f"Trigger channel set to {channel.name}.")

    @autovoiceset.command()
    async def control(self, ctx, channel: discord.TextChannel):
        """Set the control channel where the control buttons will be displayed."""
        await self.config.guild(ctx.guild).control_channel_id.set(channel.id)
        await ctx.send(f"Control channel set to {channel.name}.")

        await self.send_control_message(channel, ctx.guild)

    @commands.group(name="autovoice", aliases=["av"], invoke_without_command=True)
    async def autovoice(self, ctx):
        """Control your own personal voice channel."""
        await ctx.send_help(ctx.command)

    @autovoice.command()
    async def lock(self, ctx):
        """Lock your personal voice channel."""
        user_channel = ctx.author.voice.channel if ctx.author.voice else None
        if user_channel and user_channel.id in self.bot.created_channels:
            await user_channel.set_permissions(ctx.guild.default_role, connect=False)
            await ctx.send(f"{user_channel.name} is now locked.")

    @autovoice.command()
    async def unlock(self, ctx):
        """Unlock your personal voice channel."""
        user_channel = ctx.author.voice.channel if ctx.author.voice else None
        if user_channel and user_channel.id in self.bot.created_channels:
            await user_channel.set_permissions(ctx.guild.default_role, connect=True)
            await ctx.send(f"{user_channel.name} is now unlocked.")

    @autovoice.command()
    async def kick(self, ctx, member: discord.Member):
        """Kick a user from your personal voice channel."""
        user_channel = ctx.author.voice.channel if ctx.author.voice else None
        if user_channel and member in user_channel.members:
            await member.move_to(None)
            await ctx.send(f"{member.display_name} has been kicked from {user_channel.name}.")
        else:
            await ctx.send(f"{member.display_name} is not in your channel.")

    @autovoice.command()
    async def limit(self, ctx, limit: int):
        """Set a user limit on your personal voice channel."""
        user_channel = ctx.author.voice.channel if ctx.author.voice else None
        if user_channel:
            await user_channel.edit(user_limit=limit)
            await ctx.send(f"{user_channel.name} now has a limit of {limit} users.")
