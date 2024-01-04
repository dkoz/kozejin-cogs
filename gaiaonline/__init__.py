from .gaiaonline import GaiaIntegration

async def setup(bot):
    await bot.add_cog(GaiaIntegration(bot))