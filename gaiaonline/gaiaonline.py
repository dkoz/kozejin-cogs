import discord
from redbot.core import commands, Config
import aiohttp
import urllib.parse
import binascii

class GaiaAvatar:
    SALT = 'lksdfou'
    AVA_CDN = 'https://a1cdn.gaiaonline.com/dress-up/avatar/ava/'

    @staticmethod
    def abs_crc32_64bit(value):
        crc = abs(binascii.crc32(value.encode()))
        if crc & 0x80000000:
            crc ^= 0xffffffff
            crc += 1
        return crc

    @classmethod
    def to_url(cls, userid, variant=""):
        crc = cls.abs_crc32_64bit(str(userid) + cls.SALT)
        base = '%x%x' % (crc, userid)
        return f'{cls.AVA_CDN}{base[-2:]}/{base[-4:-2]}/{base}{variant}.png'


class AvatarDropdown(discord.ui.Select):
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        options = [
            discord.SelectOption(label="Default", value="default"),
            discord.SelectOption(label="Flipped", value="flip"),
            discord.SelectOption(label="Full Layout", value="strip"),
        ]
        super().__init__(placeholder="Choose Avatar View", options=options)

    async def callback(self, interaction: discord.Interaction):
        variant = "" if self.values[0] == "default" else f"_{self.values[0]}"
        avatar_url = GaiaAvatar.to_url(self.user_id, variant)
        
        embed = discord.Embed(title=f'{self.username}', color=discord.Color.blue())
        embed.set_image(url=avatar_url)
        await interaction.response.edit_message(embed=embed, view=self.view)

class AvatarView(discord.ui.View):
    def __init__(self, user_id, username):
        super().__init__(timeout=None)
        self.add_item(AvatarDropdown(user_id, username))


class GaiaIntegration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8475638592, force_registration=True)
        self.config.register_user(gaia_userid=None)

    @commands.guild_only()
    @commands.group(name="gaia", aliases=["go"], invoke_without_command=True)
    async def gaia_group(self, ctx):
        """Commands related to Gaia Online."""
        await ctx.send_help(ctx.command)

    @gaia_group.command(name="ava")
    async def gaia_avatar(self, ctx, *, username: str):
        """Display an avatar on Gaia Online."""
        user_id = await self.retrieve_gaiaid(username)
        if not user_id:
            await ctx.send(f'No user ID found for "{username}".')
            return

        avatar_url = GaiaAvatar.to_url(user_id)
        embed = discord.Embed(title=f'{username}', color=discord.Color.blue())
        embed.set_image(url=avatar_url)
        await ctx.send(embed=embed, view=AvatarView(user_id, username))

    @gaia_group.command(name="save")
    async def gaia_save(self, ctx, *, username: str):
        """Save your Gaia Online username and user ID."""
        user_id = await self.retrieve_gaiaid(username)
        if not user_id:
            await ctx.send(f'Error: Could not find a user ID for "{username}".')
            return

        await self.config.user(ctx.author).gaia_userid.set(user_id)
        await ctx.send(f"Gaia Online user ID saved for: {username} (ID: {user_id})")

    @gaia_group.command(name="me")
    async def gaia_me(self, ctx):
        """Display your saved Gaia Online avatar."""
        user_id = await self.config.user(ctx.author).gaia_userid()
        if not user_id:
            await ctx.send("You haven't set a username yet. Use `.go save [username]` to save it.")
            return

        avatar_url = GaiaAvatar.to_url(user_id)
        embed = discord.Embed(title="Your Gaia Avatar", color=discord.Color.blue())
        embed.set_image(url=avatar_url)
        await ctx.send(embed=embed, view=AvatarView(user_id, ctx.author.display_name))

    @gaia_group.command(name="wipe")
    async def gaia_wipe(self, ctx):
        """Delete your saved Gaia Online user ID."""
        await self.config.user(ctx.author).clear()
        await ctx.send("Your Gaia Online user ID has been deleted from the database.")

    async def retrieve_gaiaid(self, username):
        encoded_username = urllib.parse.quote(username)
        profile_url = f"https://www.gaiaonline.com/profiles/{encoded_username}"

        async with aiohttp.ClientSession() as session:
            async with session.get(profile_url, allow_redirects=True) as response:
                if response.status != 200:
                    return None

                final_url = str(response.url)
                try:
                    user_id = final_url.rstrip('/').split('/')[-1]
                    if user_id.isdigit():
                        return int(user_id)
                except Exception:
                    return None