from .autovoice import AutoVoice

async def setup(bot):
    await bot.add_cog(AutoVoice(bot))