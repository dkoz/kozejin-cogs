from .deckardcain import DeckardCain

async def setup(bot):
    await bot.add_cog(DeckardCain(bot))