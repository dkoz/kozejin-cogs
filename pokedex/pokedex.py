import aiohttp
import discord
from redbot.core import commands

class Pokedex(commands.Cog):
    """Whos that pokemon?"""

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

    async def get_pokemon_data(self, pokemon_url):
        return await self.fetch_data(pokemon_url)

    async def get_item_info(self, item_id_or_name):
        base_url = "https://pokeapi.co/api/v2/item/"
        url = base_url + item_id_or_name.lower()
        return await self.fetch_data(url)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pokedex(self, ctx, name_or_id):
        """Show Pokemon info"""
        async with ctx.typing():
            pokemon_info = await self.get_pokemon_info(name_or_id)
            if pokemon_info is None:
                await ctx.send("No Pokemon found.")
                return

            pokemon_data = await self.get_pokemon_data(pokemon_info["varieties"][0]["pokemon"]["url"])
            if pokemon_data is None:
                await ctx.send("No Pokemon found.")
                return

            description = ""
            for entry in pokemon_info["flavor_text_entries"]:
                if entry["language"]["name"] == "en":
                    description = entry["flavor_text"]
                    break

            height = str(pokemon_data.get("height", 0) / 10.0) + "m"
            weight = str(pokemon_data.get("weight", 0) / 10.0) + "kg"

            evolution_chain = []
            chain = pokemon_info.get("evolution_chain")
            while chain:
                species_name = chain.get("species", {}).get("name")
                if species_name:
                    evolution_chain.append(species_name.capitalize())
                chain = chain.get("evolves_to", [])[0] if chain.get("evolves_to") else None

            evolution_string = " -> ".join(evolution_chain) if evolution_chain else "No evolutions"

            embed = discord.Embed()
            embed.title = pokemon_data["name"].capitalize()
            embed.description = description
            embed.set_thumbnail(url=pokemon_data["sprites"]["front_default"])
            embed.add_field(name="Evolution Chain", value=evolution_string, inline=False)
            embed.add_field(name="Height", value=height)
            embed.add_field(name="Weight", value=weight)
            embed.set_footer(text="Powered by PokeAPI")

            await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def iteminfo(self, ctx, *, item_name):
        """Show Pokemon item info"""
        item_name = item_name.lower().replace(" ", "-")
        item_info = await self.get_item_info(item_name)
        
        if item_info is not None:
            item_name = item_info["name"]
            item_cost = item_info["cost"]
            item_category = item_info["category"]["name"]
            item_effect = item_info["effect_entries"][0]["effect"]
            
            flavor_text_entries = item_info["flavor_text_entries"]
            flavor_text = next((entry["text"] for entry in flavor_text_entries if entry["language"]["name"] == "en"), "")
            
            item_sprites = item_info["sprites"]
            item_thumbnail = item_sprites.get("default")  # Get the default sprite
            
            embed = discord.Embed(title="Item Information", color=discord.Color.blue())
            embed.set_thumbnail(url=item_thumbnail)
            embed.add_field(name="Name", value=item_name.capitalize(), inline=False)
            embed.add_field(name="Category", value=item_category.capitalize(), inline=False)
            embed.add_field(name="Cost", value=str(item_cost), inline=False)
            embed.add_field(name="Effect", value=item_effect, inline=False)
            embed.add_field(name="Flavor Text", value=flavor_text, inline=False)
            embed.set_footer(text="Powered by PokeAPI")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("No item found.")