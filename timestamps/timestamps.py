from datetime import datetime
import discord
from dateutil.parser import parse
from pytz import timezone, all_timezones_set
from redbot.core import commands, app_commands
from .timezones import timezone_abbreviations

class TimestampPy(commands.Cog):
    """Create a timestamp from a date and timezone."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Create a timestamp from a date and timezone.")
    @app_commands.describe(date="Example: November 7th at 12 pm est", format="The format of the timestamp or all formats.")
    @app_commands.choices(format=[
        app_commands.Choice(name="All Formats", value="all"),
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
            date_str, tz_str = date.rsplit(' ', 1)
            parsed_date = parse(date_str)
            tz_str = tz_str.lower()

            if tz_str in timezone_abbreviations:
                tz = timezone(timezone_abbreviations[tz_str])
            elif tz_str in all_timezones_set:
                tz = timezone(tz_str)
            else:
                await interaction.response.send_message("Invalid or unsupported timezone.", ephemeral=True)
                return

            localized_date = tz.localize(parsed_date)
            utc_date = localized_date.astimezone(timezone('UTC'))

        except ValueError:
            await interaction.response.send_message("Invalid date format.", ephemeral=True)
            return

        timestamp = int(utc_date.timestamp())

        if format.value == "all":
            all_formats = {
                "Short Time": f"<t:{timestamp}:t>",
                "Long Time": f"<t:{timestamp}:T>",
                "Short Date": f"<t:{timestamp}:d>",
                "Long Date": f"<t:{timestamp}:D>",
                "Short Date/Time": f"<t:{timestamp}:f>",
                "Long Date/Time": f"<t:{timestamp}:F>",
                "Relative Time": f"<t:{timestamp}:R>"
            }
            
            embed = discord.Embed(
                title="Timestamps in All Formats",
                color=discord.Color.blue()
            )
            
            for name, code in all_formats.items():
                embed.add_field(name=name, value=f"{code}\n`{code}`", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            timestamp_code = f"<t:{timestamp}:{format.value}>"
            embed = discord.Embed(
                title="Timestamp",
                description=f"**{format.name}**\n{timestamp_code}\n`{timestamp_code}`",
                color=discord.Color.blue(),
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
