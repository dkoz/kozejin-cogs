import aiohttp
import discord
from redbot.core import commands
from aiocache import cached, SimpleMemoryCache

class Pokedex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

    async def get_pokemon_info(self, name_or_id):
        base_url = "https://pokeapi.co/api/v2/pokemon-species/"
        url = base_url + name_or_id.lower()
        return await self.fetch_data(url)

    async def get_item_info(self, item_id_or_name):
        base_url = "https://pokeapi.co/api/v2/item/"
        url = base_url + item_id_or_name.lower()
        return await self.fetch_data(url)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pokemon(self, ctx, name_or_id):
        """Show Pokemon info"""
        async with ctx.typing():
            pokemon_info = await self.get_pokemon_info(name_or_id)
            if pokemon_info is None:
                await ctx.send("No Pokemon found.")
                return

            evolution_url = pokemon_info["evolution_chain"]["url"]
            evolution_data = await self.fetch_data(evolution_url)

            if evolution_data is None:
                await ctx.send("No Pokemon found.")
                return

            description = ""
            for entry in pokemon_info["flavor_text_entries"]:
                if entry["language"]["name"] == "en":
                    description = entry["flavor_text"]
                    break

            height = str(pokemon_info.get("height", 0) / 10.0) + "m"
            weight = str(pokemon_info.get("weight", 0) / 10.0) + "kg"

            evolution_chain = []
            chain = evolution_data["chain"]
            while chain:
                evolution_chain.append(chain["species"]["name"].capitalize())
                chain = chain.get("evolves_to", [])
                if chain:
                    chain = chain[0]
                else:
                    break

            evolution_string = " -> ".join(evolution_chain) if evolution_chain else "No evolutions"

            embed = discord.Embed()
            embed.title = pokemon_info["name"].capitalize()
            embed.description = description
            embed.set_thumbnail(url=f"https://pokeapi.co/media/sprites/pokemon/{pokemon_info['id']}.png")
            embed.add_field(name="Evolutions", value=evolution_string, inline=False)
            embed.add_field(name="Height", value=height)
            embed.add_field(name="Weight", value=weight)
            embed.set_footer(text="Powered by PokeAPI")

            await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def items(self, ctx, item_id_or_name):
        """Show item info"""
        async with ctx.typing():
            item_info = await self.get_item_info(item_id_or_name)
            if item_info is None:
                await ctx.send("No item found.")
                return

            embed = discord.Embed()
            embed.title = item_info["name"].capitalize()

            embed.add_field(name="Category", value=item_info.get("category", {}).get("name", "N/A"))
            embed.add_field(name="Cost", value=item_info.get("cost", "N/A"))

            flavor_text_entries = item_info.get("flavor_text_entries", [])
            flavor_text = next((entry["text"] for entry in flavor_text_entries if entry["language"]["name"] == "en"), "")
            embed.add_field(name="Flavor Text", value=flavor_text or "N/A")

            create_info = item_info.get("held_by_pokemon", [])
            create_pokemon = [pokemon["pokemon"]["name"].capitalize() for pokemon in create_info]
            create_string = ", ".join(create_pokemon) if create_pokemon else "N/A"
            embed.add_field(name="Create Item Info", value=create_string)

            thumbnail_url = item_info.get("sprites", {}).get("default")
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)

            await ctx.send(embed=embed)