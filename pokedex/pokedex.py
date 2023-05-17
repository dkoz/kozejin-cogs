import aiohttp
import discord
from redbot.core import commands
from aiocache import cached, SimpleMemoryCache

class Pokedex(commands.Cog):
    """Show Pokemon info"""

    def __init__(self, bot):
        self.bot = bot
        self.cache = SimpleMemoryCache()

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pokemon(self, ctx, name_or_id):
        """Show Pokemon info"""
        async with ctx.typing():
            pokemon_info = await self.get_pokemon_info(name_or_id)
            if pokemon_info is None:
                await ctx.send("No pokemon found.")
                return

            embed = self.create_embed(pokemon_info)
            await ctx.send(embed=embed)

    @cached(ttl=3600, cache=SimpleMemoryCache)
    async def get_pokemon_info(self, name_or_id):
        try:
            headers = {"content-type": "application/json"}

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://pokeapi.co/api/v2/pokemon-species/{name_or_id.lower()}", headers=headers) as r1:
                    response1 = await r1.json()

                if "detail" in response1 and response1["detail"] == "Not found.":
                    return None

                evolution_url = response1["evolution_chain"]["url"]

                async with session.get(f"https://pokeapi.co/api/v2/pokemon/{name_or_id.lower()}", headers=headers) as r2:
                    response2 = await r2.json()

                async with session.get(evolution_url, headers=headers) as r3:
                    response3 = await r3.json()

            return response1, response2, response3

        except:
            return None

    def create_embed(self, pokemon_info):
        response1, response2, response3 = pokemon_info

        description = next(
            (entry["flavor_text"] for entry in response1["flavor_text_entries"] if entry["language"]["name"] == "en"),
            ""
        )

        height = f"{response2['height'] / 10.0}m"
        weight = f"{response2['weight'] / 10.0}kg"

        evolution_chain = response3["chain"]
        evolutions = [evolution_chain["species"]["name"].capitalize()]
        while evolution_chain["evolves_to"]:
            evolution_chain = evolution_chain["evolves_to"][0]
            evolutions.append(evolution_chain["species"]["name"].capitalize())
        evolution_string = " -> ".join(evolutions) if len(evolutions) > 1 else "No evolutions"

        embed = discord.Embed()
        embed.title = response1["name"].capitalize()
        embed.description = description
        embed.set_thumbnail(url=response2["sprites"]["front_default"])
        embed.add_field(name="Evolutions", value=evolution_string, inline=False)
        embed.add_field(name="Height", value=height)
        embed.add_field(name="Weight", value=weight)
        embed.set_footer(text="Powered by Pokeapi")

        return embed