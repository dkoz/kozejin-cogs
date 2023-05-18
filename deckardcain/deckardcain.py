import discord
from redbot.core import commands, Config
import openai
import asyncio

class DeckardCain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(api_key=None)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def setapikey(self, ctx, api_key):
        await self.config.guild(ctx.guild).api_key.set(api_key)
        await ctx.send("API key has been set successfully.")

    @commands.command()
    async def askcain(self, ctx, *, question):
        api_key = await self.config.guild(ctx.guild).api_key()

        if api_key:
            response = await self.generate_response(question, api_key)
            await ctx.send(response)
        else:
            await ctx.send("API key is not set. Please ask the guild owner to use the setapikey command to set the API key for this guild.")

    async def generate_response(self, question, api_key):
        openai.api_key = api_key

        prompt = "You are Deckard Cain, an old wise scholar.\nUser: " + question
        try:
            response = await asyncio.to_thread(openai.Completion.create, model="text-davinci-003", prompt=prompt)
            response_content = response["choices"][0]["text"].strip()
        except Exception as e:
            response_content = f"An error occurred: {str(e)}"
        
        return response_content