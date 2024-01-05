from .battlemetricsapi import BattleMetricsCog

async def setup(bot):
    await bot.add_cog(BattleMetricsCog(bot))