import discord

class ChannelControlView(discord.ui.View):
    def __init__(self, bot, channel_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.channel_id = channel_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        user_channel = interaction.user.voice.channel if interaction.user.voice else None
        if not user_channel:
            await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
            return False
        owner_id = await self.bot.get_cog('AutoVoice').get_channel_owner(interaction.guild, user_channel.id)
        if interaction.user.id != owner_id:
            await interaction.response.send_message("You are not the owner of this channel.", ephemeral=True)
            return False
        return True

class LockChannelButton(discord.ui.Button):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.danger, label="Lock Channel")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        user_channel = interaction.user.voice.channel if interaction.user.voice else None
        if user_channel:
            await user_channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message(f"{user_channel.name} is now locked.", ephemeral=True)
        else:
            await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)

class UnlockChannelButton(discord.ui.Button):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.success, label="Unlock Channel")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        user_channel = interaction.user.voice.channel if interaction.user.voice else None
        if user_channel:
            await user_channel.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.response.send_message(f"{user_channel.name} is now unlocked.", ephemeral=True)
        else:
            await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
