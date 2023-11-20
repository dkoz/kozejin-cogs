from .speaker import Speaker

async def setup(bot):
    await bot.add_cog(Speaker(bot))