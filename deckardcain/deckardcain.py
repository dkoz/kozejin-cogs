import discord
from redbot.core import commands, Config
import openai
import asyncio

class DeckardCain(commands.Cog):
    """Deckard Cain as ChatGPT"""

    __version__ = "1.0.3"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(api_key=None, allowed_channel=None)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def setcainapikey(self, ctx, api_key):
        """Sets the API Key for OpenAI ChatGPT"""
        await self.config.guild(ctx.guild).api_key.set(api_key)
        await ctx.send("API key has been set successfully.")

    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    async def setcainchannel(self, ctx, channel: discord.TextChannel):
        """Restricts `askcain` to a specified channel"""
        await self.config.guild(ctx.guild).allowed_channel.set(channel.id)
        await ctx.send(f"The channel '{channel.name}' has been set as the allowed channel for the 'askcain' command.")

    @commands.command()
    async def askcain(self, ctx, *, question):
        """Chat with Deckard Cain(ChatGPT)"""
        allowed_channel_id = await self.config.guild(ctx.guild).allowed_channel()

        if allowed_channel_id is None or ctx.channel.id == allowed_channel_id:
            api_key = await self.config.guild(ctx.guild).api_key()

            if api_key:
                response = await self.generate_response(question, api_key)
                await ctx.message.delete()  # Delete the user's command message
                await ctx.send(response)
            else:
                await ctx.send("API key is not set. Please ask the guild owner to use the setapikey command to set the API key for this guild.")
        else:
            allowed_channel = self.bot.get_channel(allowed_channel_id)
            await ctx.send(f"The 'askcain' command can only be used in {allowed_channel.mention}.")

    async def generate_response(self, question, api_key):
        openai.api_key = api_key

        prompt = "You are Deckard Cain, an old wise scholar.\nUser: " + question
        try:
            response = await asyncio.to_thread(openai.Completion.create, model="text-davinci-003", prompt=prompt)
            response_content = response["choices"][0]["text"].strip()
        except Exception as e:
            response_content = f"An error occurred: {str(e)}"

        return response_content