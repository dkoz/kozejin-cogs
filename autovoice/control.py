import discord

class ChannelControlView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def on_timeout(self):
        pass

class LockChannelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Lock Channel")

    async def callback(self, interaction: discord.Interaction):
        user_channel = interaction.user.voice.channel if interaction.user.voice else None
        if user_channel and user_channel.id in self.view.bot.created_channels:
            await user_channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message(f"{user_channel.name} is now locked.", ephemeral=True)
        else:
            await interaction.response.send_message("You are not in a created voice channel or it doesn't exist.", ephemeral=True)

class UnlockChannelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Unlock Channel")

    async def callback(self, interaction: discord.Interaction):
        user_channel = interaction.user.voice.channel if interaction.user.voice else None
        if user_channel and user_channel.id in self.view.bot.created_channels:
            await user_channel.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.response.send_message(f"{user_channel.name} is now unlocked.", ephemeral=True)
        else:
            await interaction.response.send_message("You are not in a created voice channel or it doesn't exist.", ephemeral=True)
