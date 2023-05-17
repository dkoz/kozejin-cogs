from .pokedex import Pokedex

async def setup(bot):
    await bot.add_cog(Pokedex(bot))