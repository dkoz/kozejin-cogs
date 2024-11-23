from .simpletickets import SimpleTickets

async def setup(bot):
    await bot.add_cog(SimpleTickets(bot))