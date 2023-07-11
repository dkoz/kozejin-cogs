from datetime import datetime, timedelta, timezone
import discord
from dateutil.parser import parse
from redbot.core import commands, app_commands

class TimestampPy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(date="The date for the timestamp", format="The format of the timestamp")
    @app_commands.choices(format=[
        app_commands.Choice(name="Short Time", value="t"),
        app_commands.Choice(name="Long Time", value="T"),
        app_commands.Choice(name="Short Date", value="d"),
        app_commands.Choice(name="Long Date", value="D"),
        app_commands.Choice(name="Short Date/Time", value="f"),
        app_commands.Choice(name="Long Date/Time", value="F"),
        app_commands.Choice(name="Relative Time", value="R")
    ])
    async def timestamp(self, interaction: discord.Interaction, date: str, format: app_commands.Choice[str]):
        try:
            date, tz = date.rsplit(' ', 1)
            date = parse(date)
        except ValueError:
            await interaction.response.send_message("Invalid date format.", ephemeral=True)
            return

        tz = tz.lower()
        if tz in ['est', 'cst', 'pst']:
            offsets = {'est': -5, 'cst': -6, 'pst': -8}
            offset = offsets[tz]

            if datetime(date.year, 3, 14, 2) <= date < datetime(date.year, 11, 7, 2):
                offset += 1
            date -= timedelta(hours=offset)

        timestamp = int(date.timestamp())
        timestamp_code = f"<t:{timestamp}:{format.value}>"

        embed = discord.Embed(
            title="Timestamp",
            description=f"Your date: {timestamp_code}\nYour format: {format.name}\nYour timestamp: `{timestamp_code}`",
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
