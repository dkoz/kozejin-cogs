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
            "control_message_id": None,
            "channel_owners": {}
        }
        self.config.register_guild(**default_guild)
        self.bot.created_channels = set()

    async def set_channel_owner(self, guild, channel_id, member_id):
        async with self.config.guild(guild).channel_owners() as channel_owners:
            channel_owners[str(channel_id)] = member_id

    async def get_channel_owner(self, guild, channel_id):
        channel_owners = await self.config.guild(guild).channel_owners()
        return channel_owners.get(str(channel_id), None)

    async def send_control_message(self, channel, guild):
        view = ChannelControlView(self.bot, channel.id)
        view.add_item(LockChannelButton(self.bot))
        view.add_item(UnlockChannelButton(self.bot))
        embed = discord.Embed(title="Channel Management", description="Use the buttons below to control your channel.")
        message = await channel.send(embed=embed, view=view)
        await self.config.guild(guild).control_message_id.set(message.id)

    async def update_control_message(self, guild, channel):
        control_message_id = await self.config.guild(guild).control_message_id()
        control_channel_id = await self.config.guild(guild).control_channel_id()
        if control_channel_id:
            control_channel = self.bot.get_channel(control_channel_id)
            if control_channel:
                try:
                    message = await control_channel.fetch_message(control_message_id)
                    view = ChannelControlView(self.bot, control_channel.id)
                    view.add_item(LockChannelButton(self.bot))
                    view.add_item(UnlockChannelButton(self.bot))
                    await message.edit(view=view)
                except discord.NotFound:
                    await self.send_control_message(control_channel, guild)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            control_channel_id = await self.config.guild(guild).control_channel_id()
            if control_channel_id:
                control_channel = self.bot.get_channel(control_channel_id)
                await self.update_control_message(guild, control_channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        trigger_channel_id = await self.config.guild(member.guild).trigger_channel_id()

        if before.channel and before.channel.id in self.bot.created_channels:
            old_channel = before.channel
        else:
            old_channel = None

        if after.channel and after.channel.id == trigger_channel_id:
            new_channel = await member.guild.create_voice_channel(name=f"{member.display_name}'s channel", category=after.channel.category)
            self.bot.created_channels.add(new_channel.id)
            await self.set_channel_owner(member.guild, new_channel.id, member.id)
            await member.move_to(new_channel)

            if old_channel and len(old_channel.members) == 0:
                await old_channel.delete()
                self.bot.created_channels.remove(old_channel.id)

        elif before.channel and len(before.channel.members) == 0 and before.channel.id in self.bot.created_channels:
            await before.channel.delete()
            self.bot.created_channels.remove(before.channel.id)

    async def is_channel_owner(self, ctx):
        user_channel = ctx.author.voice.channel if ctx.author.voice else None
        if user_channel and user_channel.id in self.bot.created_channels:
            owner_id = await self.get_channel_owner(ctx.guild, user_channel.id)
            return owner_id == ctx.author.id
        return False

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
        control_message_id = await self.config.guild(ctx.guild).control_message_id()
        if control_message_id:
            await self.update_control_message(ctx.guild, channel)
        else:
            await self.send_control_message(channel, ctx.guild)
            
    @autovoiceset.command()
    async def wipe(self, ctx):
        """Wipe all settings for this guild."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send(f"All AutoVoice settings for this guild have been wiped.")

    @commands.group(name="autovoice", aliases=["av"], invoke_without_command=True)
    async def autovoice(self, ctx):
        """Control your own personal voice channel."""
        await ctx.send_help(ctx.command)

    @autovoice.command()
    async def lock(self, ctx):
        """Lock your personal voice channel."""
        if await self.is_channel_owner(ctx):
            user_channel = ctx.author.voice.channel
            await user_channel.set_permissions(ctx.guild.default_role, connect=False)
            await ctx.send(f"{user_channel.name} is now locked.")
        else:
            await ctx.send("You are not the owner of this channel.")

    @autovoice.command()
    async def unlock(self, ctx):
        """Unlock your personal voice channel."""
        if await self.is_channel_owner(ctx):
            user_channel = ctx.author.voice.channel
            await user_channel.set_permissions(ctx.guild.default_role, connect=True)
            await ctx.send(f"{user_channel.name} is now unlocked.")
        else:
            await ctx.send("You are not the owner of this channel.")

    @autovoice.command()
    async def kick(self, ctx, member: discord.Member):
        """Kick a user from your personal voice channel."""
        if await self.is_channel_owner(ctx):
            user_channel = ctx.author.voice.channel
            if member in user_channel.members:
                await member.move_to(None)
                await ctx.send(f"{member.display_name} has been kicked from {user_channel.name}.")
            else:
                await ctx.send(f"{member.display_name} is not in your channel.")
        else:
            await ctx.send("You are not the owner of this channel.")

    @autovoice.command()
    async def limit(self, ctx, limit: int):
        """Set a user limit on your personal voice channel."""
        if await self.is_channel_owner(ctx):
            user_channel = ctx.author.voice.channel
            await user_channel.edit(user_limit=limit)
            await ctx.send(f"{user_channel.name} now has a limit of {limit} users.")
        else:
            await ctx.send("You are not the owner of this channel.")
