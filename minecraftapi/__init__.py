from .minecraftapi import MinecraftAPI

__red_end_user_data_statement__ = (
    "This cog does not persistently store user data."
)

async def setup(bot):
    await bot.add_cog(MinecraftAPI(bot))