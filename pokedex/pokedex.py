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

    async def get_pokemon_info(self, poke_name):
        base_url = "https://pokeapi.co/api/v2/pokemon-species/"
        url = base_url + poke_name.lower()
        return await self.fetch_data(url)

    async def get_pokemon_data(self, pokemon_url):
        return await self.fetch_data(pokemon_url)

    async def get_item_info(self, item_id_or_name):
        base_url = "https://pokeapi.co/api/v2/item/"
        url = base_url + item_id_or_name.lower()
        return await self.fetch_data(url)

    async def get_move_info(self, move_name):
        base_url = "https://pokeapi.co/api/v2/move/"
        url = base_url + move_name.lower()
        return await self.fetch_data(url)

    async def get_evolution_chain(self, evolution_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(evolution_url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

    @cached(ttl=3600, cache=SimpleMemoryCache)
    async def cached_fetch_data(self, url):
        return await self.fetch_data(url)

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def pokedex(self, ctx, poke_name):
        """Show Pokemon info"""
        async with ctx.typing():
            pokemon_info = await self.get_pokemon_info(poke_name)
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

            evolution_chain_url = pokemon_info["evolution_chain"]["url"]
            evolution_chain = await self.get_evolution_chain(evolution_chain_url)

            evolutions = [evolution_chain["chain"]["species"]["name"].capitalize()]
            evolution = evolution_chain["chain"].get("evolves_to")
            while evolution:
                evolutions.append(evolution[0]["species"]["name"].capitalize())
                evolution = evolution[0].get("evolves_to")

            evolution_string = " -> ".join(evolutions) if len(evolutions) > 1 else "No evolutions"

            embed = discord.Embed()
            embed.title = pokemon_data["name"].capitalize()
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
        item_name = item_name.lower().replace(" ", "-")
        item_info = await self.get_item_info(item_name)

        if item_info is not None:
            item_name = item_info["name"]
            item_cost = item_info["cost"]
            item_category = item_info["category"]["name"]
            item_effect = item_info["effect_entries"][0]["effect"]

            flavor_text_entries = item_info["flavor_text_entries"]
            flavor_text = next(
                (entry["text"] for entry in flavor_text_entries if entry["language"]["name"] == "en"), ""
            )

            item_sprites = item_info["sprites"]
            item_thumbnail = item_sprites.get("default")

            embed = discord.Embed(title="Item Information", color=discord.Color.blue())
            embed.set_thumbnail(url=item_thumbnail)
            embed.add_field(name="Name", value=item_name.replace("-", " ").capitalize(), inline=False)
            embed.add_field(name="Category", value=item_category.capitalize(), inline=False)
            embed.add_field(name="Cost", value=str(item_cost), inline=False)
            embed.add_field(name="Effect", value=item_effect, inline=False)
            embed.add_field(name="Flavor Text", value=flavor_text, inline=False)
            embed.set_footer(text="Powered by PokeAPI")

            await ctx.send(embed=embed)
        else:
            await ctx.send("No item found.")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def moveset(self, ctx, *, move_name):
        """Show Pokemon moveset info"""
        move_name = move_name.lower().replace(" ", "-")
        async with ctx.typing():
            move_info = await self.get_move_info(move_name)
            if move_info is None:
                await ctx.send("No move found.")
                return

            move_name = move_info["name"].replace("-", " ").capitalize()
            move_type = move_info["type"]["name"].capitalize()
            move_power = move_info.get("power", "-")
            move_pp = move_info.get("pp", "-")
            move_accuracy = move_info.get("accuracy", "-")
            move_description = move_info["flavor_text_entries"][0]["flavor_text"]

            embed = discord.Embed(title=f"Move Information: {move_name}", color=discord.Color.blue())
            embed.set_thumbnail(url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/tm-normal.png")
            embed.add_field(name="Type", value=move_type, inline=True)
            embed.add_field(name="Power", value=move_power, inline=True)
            embed.add_field(name="PP", value=move_pp, inline=True)
            embed.add_field(name="Accuracy", value=move_accuracy, inline=True)
            embed.add_field(name="Description", value=move_description, inline=False)
            embed.set_footer(text="Powered by PokeAPI")

            await ctx.send(embed=embed)
