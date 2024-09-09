import aiohttp
import discord
from redbot.core import commands
from aiocache import cached, SimpleMemoryCache

class Pokedex(commands.Cog):
    """Look up information on Pokemon and game items"""

    __version__ = "1.1.5"

    def __init__(self, bot):
        self.bot = bot

    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

    def format_name(self, name):
        return name.lower().replace(" ", "-").replace(".", "")

    def clean_name(self, name):
        return ' '.join(word.capitalize() for word in name.replace("-", " ").replace(".", "").split())

    async def get_pokemon_info(self, poke_name):
        base_url = "https://pokeapi.co/api/v2/pokemon-species/"
        url = base_url + self.format_name(poke_name)
        return await self.cached_fetch_data(url)

    async def get_pokemon_data(self, pokemon_url):
        return await self.cached_fetch_data(pokemon_url)

    async def get_item_info(self, item_id_or_name):
        base_url = "https://pokeapi.co/api/v2/item/"
        url = base_url + self.format_name(item_id_or_name)
        return await self.cached_fetch_data(url)

    async def get_move_info(self, move_name):
        base_url = "https://pokeapi.co/api/v2/move/"
        url = base_url + self.format_name(move_name)
        return await self.cached_fetch_data(url)

    async def get_evolution_chain(self, evolution_url):
        return await self.cached_fetch_data(evolution_url)

    @cached(ttl=3600, cache=SimpleMemoryCache)
    async def cached_fetch_data(self, url):
        return await self.fetch_data(url)

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def pokedex(self, ctx, *, poke_name):
        """Show Pokemon info"""
        async with ctx.typing():
            pokemon_info = await self.get_pokemon_info(poke_name)
            if not pokemon_info:
                await ctx.send("No Pokemon found.")
                return

            pokemon_data = await self.get_pokemon_data(pokemon_info["varieties"][0]["pokemon"]["url"])
            if not pokemon_data:
                await ctx.send("No Pokemon found.")
                return

            description = next((entry["flavor_text"] for entry in pokemon_info["flavor_text_entries"] if entry["language"]["name"] == "en"), None)
            height = f"{pokemon_data.get('height', 0) / 10.0}m"
            weight = f"{pokemon_data.get('weight', 0) / 10.0}kg"

            evolution_chain_url = pokemon_info["evolution_chain"]["url"]
            evolution_chain = await self.get_evolution_chain(evolution_chain_url)

            evolutions = [self.clean_name(evolution_chain["chain"]["species"]["name"])]
            evolution = evolution_chain["chain"].get("evolves_to")
            while evolution:
                evolutions.append(self.clean_name(evolution[0]["species"]["name"]))
                evolution = evolution[0].get("evolves_to")

            evolution_string = " -> ".join(evolutions) if len(evolutions) > 1 else "No evolutions"

            embed = discord.Embed()
            embed.title = self.clean_name(pokemon_data["name"])
            embed.description = description
            embed.set_thumbnail(url=pokemon_data["sprites"]["front_default"])
            embed.add_field(name="Evolution Chain", value=evolution_string, inline=False)
            embed.add_field(name="Height", value=height)
            embed.add_field(name="Weight", value=weight)
            embed.set_footer(text="Powered by PokeAPI")

            await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def iteminfo(self, ctx, *, item_name):
        """Show Pokemon item info"""
        async with ctx.typing():
            item_info = await self.get_item_info(item_name)
            if not item_info:
                await ctx.send("No item found.")
                return

            item_name = self.clean_name(item_info["name"])
            item_cost = item_info["cost"]
            item_category = self.clean_name(item_info["category"]["name"])
            item_effect = next((entry["effect"] for entry in item_info["effect_entries"] if entry["language"]["name"] == "en"), "No effect information.")

            flavor_text_entries = item_info.get("flavor_text_entries", [])
            flavor_text = next((entry["text"] for entry in flavor_text_entries if entry["language"]["name"] == "en"), "No flavor text available.")

            item_thumbnail = item_info["sprites"]["default"]

            embed = discord.Embed(title="Item Information", color=discord.Color.blue())
            embed.set_thumbnail(url=item_thumbnail)
            embed.add_field(name="Name", value=item_name, inline=False)
            embed.add_field(name="Category", value=item_category, inline=False)
            embed.add_field(name="Cost", value=str(item_cost), inline=False)
            embed.add_field(name="Effect", value=item_effect, inline=False)
            embed.add_field(name="Flavor Text", value=flavor_text, inline=False)
            embed.set_footer(text="Powered by PokeAPI")

            await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def moveset(self, ctx, *, move_name):
        """Show Pokemon moveset info"""
        async with ctx.typing():
            move_info = await self.get_move_info(move_name)
            if not move_info:
                await ctx.send("No move found.")
                return

            move_name_formatted = self.clean_name(move_info["name"])
            move_type = self.clean_name(move_info["type"]["name"])
            move_power = move_info.get("power", "-")
            move_pp = move_info.get("pp", "-")
            move_accuracy = move_info.get("accuracy", "-")
            move_description = next((entry["flavor_text"] for entry in move_info["flavor_text_entries"] if entry["language"]["name"] == "en"), "No description available.")

            embed = discord.Embed(title=f"Move Information: {move_name_formatted}", color=discord.Color.blue())
            embed.set_thumbnail(url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/tm-normal.png")
            embed.add_field(name="Type", value=move_type, inline=True)
            embed.add_field(name="Power", value=str(move_power), inline=True)
            embed.add_field(name="PP", value=str(move_pp), inline=True)
            embed.add_field(name="Accuracy", value=str(move_accuracy), inline=True)
            embed.add_field(name="Description", value=move_description, inline=False)
            embed.set_footer(text="Powered by PokeAPI")

            await ctx.send(embed=embed)
