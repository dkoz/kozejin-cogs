from .timestamps import TimestampPy

async def setup(bot):
    await bot.add_cog(TimestampPy(bot))