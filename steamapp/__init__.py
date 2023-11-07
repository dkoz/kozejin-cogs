from .steamapp import SteamAPI

async def setup(bot):
    await bot.add_cog(SteamAPI(bot))