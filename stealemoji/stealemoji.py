import re
import discord
from redbot.core import commands
import aiohttp

class EmojiStealer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def stealemoji(self, ctx, *, message: str):
        """Upload an emoji from another server to your own.
        Usage: [p]stealemoji :emoji:"""
        emoji_pattern = r'<(a?):(\w+):(\d+)>'
        matches = re.findall(emoji_pattern, message)
        
        if len(matches) > 10:
            await ctx.send("You can only upload up to 10 emojis at a time.")
            return

        uploaded = []
        failed = []

        for match in matches:
            animated, emoji_name, emoji_id = match
            file_format = "gif" if animated else "png"
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{file_format}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(emoji_url) as resp:
                    if resp.status == 200:
                        emoji_bytes = await resp.read()
                        try:
                            await ctx.guild.create_custom_emoji(name=emoji_name, image=emoji_bytes)
                            uploaded.append(emoji_name)
                        except discord.HTTPException:
                            failed.append(emoji_name)
                    else:
                        failed.append(emoji_name)

        response = ""
        if uploaded:
            response += f"Uploaded: {', '.join(uploaded)}\n"
        if failed:
            response += f"Failed to upload: {', '.join(failed)}"
        
        await ctx.send(response)
