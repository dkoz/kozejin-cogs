import discord
from redbot.core import commands, Config
from openai import AsyncOpenAI
import asyncio

class DeckardCain(commands.Cog):
    """Deckard Cain as AI
    Make sure to create an API Key on [OpenAI Platform](https://platform.openai.com/)
    You will need to configure a billing method and usage limits."""

    __version__ = "1.0.6"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1928374650)
        self.config.register_guild(api_key=None, allowed_channel=None)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(name="cainset", invoke_without_command=True)
    async def cainset(self, ctx):
        """Commands for AI Deckard Cain"""
        await ctx.send_help(ctx.command)

    @cainset.command()
    async def apikey(self, ctx, api_key: str):
        """Sets the API Key for OpenAI"""
        try:
            if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await ctx.send("I do not have permissions to delete messages in this channel.")
                return

            await self.config.guild(ctx.guild).api_key.set(api_key)
            confirmation_message = await ctx.send("API key has been set successfully. This message will be deleted shortly.")
            await ctx.message.delete()
            await asyncio.sleep(3)
            await confirmation_message.delete()

        except Exception as e:
            await ctx.send(f"Error while setting the API key: {str(e)}")

    @cainset.command()
    async def wipeapikey(self, ctx):
        """Wipes the stored API Key for OpenAI"""
        try:
            current_key = await self.config.guild(ctx.guild).api_key()
            
            if current_key is None:
                await ctx.send("No API key is currently set.")
                return

            await self.config.guild(ctx.guild).api_key.clear()
            await ctx.send("The API key has been wiped successfully.")
        except Exception as e:
            await ctx.send(f"Error wiping the API key: {str(e)}")

    @cainset.command()
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Restricts direct messages to Deckard Cain to a specified channel
        Run the command without a channel to clear the database."""
        if channel is None:
            await self.config.guild(ctx.guild).allowed_channel.clear()
            await ctx.send("The channel restriction for `Deckard Cain` has been removed.")
        else:
            await self.config.guild(ctx.guild).allowed_channel.set(channel.id)
            await ctx.send(f"The channel '{channel.name}' has been set as the allowed channel for directly talking to `Deckard Cain`.")

    @commands.command()
    @commands.guild_only()
    async def askcain(self, ctx, *, question):
        """Chat with AI Deckard Cain"""
        allowed_channel_id = await self.config.guild(ctx.guild).allowed_channel()

        if allowed_channel_id is None or ctx.channel.id == allowed_channel_id:
            api_key = await self.config.guild(ctx.guild).api_key()

            if api_key:
                response = await self.generate_response(question, api_key)
                await ctx.send(response)
            else:
                await ctx.send("API key not set! Use the command `[p]cainset apikey`.")
        else:
            allowed_channel = self.bot.get_channel(allowed_channel_id)
            await ctx.send(f"The `[p]askcain` command can only be used in {allowed_channel.mention}.")

    async def generate_response(self, question, api_key):
        client = AsyncOpenAI(api_key=api_key)

        prompt = (
            "You are Deckard Cain, the last of the Horadrim from the Diablo universe. "
            "Respond to the following question with wisdom and knowledge from your extensive lore experience.\n"
            f"Question: {question}\n"
            "Answer:"
        )

        try:
            response = await client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=600,
                temperature=0.5
            )

            response_content = response.choices[0].text.strip()
            return response_content
        except Exception as e:
            return f"An error occurred: {str(e)}"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        allowed_channel_id = await self.config.guild(message.guild).allowed_channel()

        if allowed_channel_id and message.channel.id == allowed_channel_id:
            api_key = await self.config.guild(message.guild).api_key()

            if api_key:
                response = await self.generate_response(message.content, api_key)
                await message.channel.send(response)
            else:
                await message.channel.send("API key not set! Use the command `[p]cainset apikey`.")
