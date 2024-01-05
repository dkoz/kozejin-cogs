from .egnotifier import EpicGamesNotifier

async def setup(bot):
    await bot.add_cog(EpicGamesNotifier(bot))