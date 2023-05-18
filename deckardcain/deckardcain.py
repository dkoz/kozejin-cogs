import discord
from redbot.core import commands
import openai
import json
import asyncio

class DeckardCainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_keys = self.load_api_keys()

    def load_api_keys(self):
        try:
            with open("api_keys.json", "r") as file:
                data = json.load(file)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_api_keys(self):
        with open("api_keys.json", "w") as file:
            json.dump(self.api_keys, file)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def setapikey(self, ctx, api_key):
        self.api_keys[ctx.guild.id] = api_key
        self.save_api_keys()
        await ctx.send("API key has been set successfully.")

    @commands.command()
    async def askcain(self, ctx, *, question):
        api_key = self.api_keys.get(ctx.guild.id)

        if api_key:
            response = await self.generate_response(question, api_key)
            await ctx.send(response)
        else:
            await ctx.send("API key is not set. Please ask the guild owner to use the setapikey command to set the API key for this guild.")

    async def generate_response(self, question, api_key):
        openai.api_key = api_key

        chat_input = {
            'messages': [
                {'role': 'system', 'content': 'You are Deckard Cain, an old wise scholar.'},
                {'role': 'user', 'content': question}
            ]
        }

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, openai.Completion.create, 'text-davinci-003', chat_input, 0.7, 50, 1, None, 0, 0)
        
        return response.choices[0].text.strip()