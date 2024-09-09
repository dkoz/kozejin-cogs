import discord
from redbot.core import Config

class SteamAPIKeyModal(discord.ui.Modal, title="Enter Steam API Key"):
    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    steam_api_key = discord.ui.TextInput(
        label="Steam API Key",
        style=discord.TextStyle.short,
        placeholder="Enter your Steam API key...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.config.steam_api_key.set(self.steam_api_key.value)
        await interaction.response.send_message(f"Steam API key has been set!", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f"Something went wrong: {error}", ephemeral=True)
