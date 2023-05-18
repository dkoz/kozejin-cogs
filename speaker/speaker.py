import discord
from redbot.core import commands

class Speaker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(name="speak", aliases=["sk"], invoke_without_command=True)
    async def speak_group(self, ctx):
        """Commands for bot speak actions."""
        await ctx.send_help(ctx.command)

    @speak_group.command(name="say")
    async def speak_say(self, ctx, destination: discord.TextChannel, *, content):
        """Speak as the bot."""
        await ctx.message.delete()
        await destination.send(content=content)

    @speak_group.command(name="embed")
    async def speak_embed(self, ctx, destination: discord.TextChannel):
        """Create an embedded message as the bot."""
        await ctx.message.delete()
        await ctx.send("Please enter the title for the embedded message:")
        try:
            title = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
            await ctx.send("Please enter the description for the embedded message:")
            description = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        except TimeoutError:
            await ctx.send("Embed creation timed out.")
            return

        embed = discord.Embed(title=title.content, description=description.content)
        await destination.send(embed=embed)

    @speak_group.command(name="edit")
    async def speak_edit(self, ctx, channel: discord.TextChannel, message_id: int, *, new_content):
        """Edit a message sent by the bot."""
        try:
            message = await channel.fetch_message(message_id)
        except Exception:
            await ctx.send("Could not find the specified message.")
            return

        if message.author == self.bot.user:
            await self.edit_embed_message(ctx, message, new_content)
        else:
            await ctx.send("You can only edit messages sent by the bot.")

    @speak_group.command(name="editembed")
    async def speak_edit_embed(self, ctx, channel: discord.TextChannel, message_id: int):
        """Edit the embedded message sent by the bot."""
        try:
            message = await channel.fetch_message(message_id)
        except Exception:
            await ctx.send("Could not find the specified message.")
            return

        if message.author == self.bot.user:
            await self.edit_entire_embed_message(ctx, message)
        else:
            await ctx.send("You can only edit messages sent by the bot.")

    async def edit_embed_message(self, ctx, message: discord.Message, new_content: str):
        if message.embeds:
            embed = message.embeds[0]
            if embed.title:
                embed.title = new_content
                await message.edit(embed=embed)
                await ctx.send("Embedded message title edited.")
            else:
                embed.description = new_content
                await message.edit(embed=embed)
                await ctx.send("Embedded message description edited.")
        else:
            await message.edit(content=new_content)
            await ctx.send("Message edited.")

    async def edit_entire_embed_message(self, ctx, message):
        if message.embeds:
            old_embed = message.embeds[0]
            await ctx.send("Please enter the new title for the embedded message:")
            new_title = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
            await ctx.send("Please enter the new description for the embedded message:")
            new_description = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)

            embed = discord.Embed(title=new_title.content, description=new_description.content)
            if old_embed.color is not None:
                embed.color = old_embed.color
            if old_embed.timestamp is not None:
                embed.timestamp = old_embed.timestamp

            await message.edit(embed=embed)
            await ctx.send("Embedded message edited.")
        else:
            await ctx.send("The specified message does not have an embed.")