import discord
from redbot.core import commands, Config
from discord.ui import Button, View
from io import StringIO

class SimpleTickets(commands.Cog):
    """Ticket System Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        ) 
        default_guild = {
            "ticket_channel_id": None,
            "log_channel_id": None,
            "message_id": None,
            "categories": [],
            "ticket_counter": 1,
            "dm_on_close": False,
            "transcript_enabled": False,
            "ticket_roles": [],
        }
        self.config.register_guild(**default_guild)
        self.bot.loop.create_task(self.setup_buttons())

    async def setup_buttons(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            ticket_channel_id = await self.config.guild(guild).ticket_channel_id()
            message_id = await self.config.guild(guild).message_id()
            if ticket_channel_id:
                channel = guild.get_channel(ticket_channel_id)
                if channel:
                    categories = await self.config.guild(guild).categories()
                    view = View(timeout=None)
                    for category in categories:
                        button = Button(
                            label=category,
                            style=discord.ButtonStyle.green,
                            custom_id=f"create_ticket_{category}",
                        )
                        button.callback = self.button_callback
                        view.add_item(button)

                    embed = discord.Embed(
                        title="Support Tickets",
                        description="Click a button below to create a new ticket in a specific category.",
                    )

                    if message_id:
                        try:
                            message = await channel.fetch_message(message_id)
                            await message.edit(embed=embed, view=view)
                        except (discord.NotFound, discord.HTTPException):
                            message = await channel.send(embed=embed, view=view)
                            await self.config.guild(guild).message_id.set(message.id)
                    else:
                        message = await channel.send(embed=embed, view=view)
                        await self.config.guild(guild).message_id.set(message.id)

    @commands.guild_only()
    @commands.group(
        name="stickets",
        invoke_without_command=True
    )
    @commands.has_permissions(manage_channels=True)
    async def tickets(self, ctx):
        """Simple Tickets Commands"""
        await ctx.send_help(ctx.command)

    @tickets.command(name="setup")
    @commands.has_permissions(manage_channels=True)
    async def setup(self, ctx):
        """Setup guide for the ticket system."""
        prefix = ctx.clean_prefix
        embed = discord.Embed(
            title="Ticket System Setup Guide",
            description="Follow the steps below to set up the ticket system.",
            color=discord.Color.orange(),
        )
        embed.add_field(
            name="Step 1: Create a Ticket Channel",
            value=(
                f"Create a new text channel where users can create tickets. Use the `{prefix}stickets channel` command to set this channel."
            ),
            inline=False,
        )
        embed.add_field(
            name="Step 2: Set Log Channel (Optional)",
            value=(
                f"Set a log channel to log ticket creations. Use the `{prefix}stickets logchannel` command to set this channel."
            ),
            inline=False,
        )
        embed.add_field(
            name="Step 3: Add Ticket Categories",
            value=(
                f"Add ticket categories using the `{prefix}stickets addcategory` command. Users can create tickets in these categories."
            ),
            inline=False,
        )
        embed.add_field(
            name="Step 4: Add Ticket Roles",
            value=(
                f"Add roles that can access the ticket system using the `{prefix}stickets role` command."
            ),
            inline=False,
        )
        embed.add_field(
            name="Step 5: Toggle DM on Close and Transcript Generation",
            value=(
                f"Toggle DM on close and transcript generation using the `{prefix}stickets transcript <true/false> <true/false>` command."
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @tickets.command(name="transcript")
    @commands.has_permissions(manage_channels=True)
    async def toggle_transcript(
        self, ctx, dm_on_close: bool, transcript_enabled: bool
    ):
        """Toggle DM on close and transcript generation. (true/false)"""
        await self.config.guild(ctx.guild).dm_on_close.set(dm_on_close)
        await self.config.guild(ctx.guild).transcript_enabled.set(transcript_enabled)
        await ctx.send(
            f"DM on close set to {dm_on_close}. Transcript generation set to {transcript_enabled}."
        )

    @tickets.command(name="addcategory")
    @commands.has_permissions(manage_channels=True)
    async def add_category(self, ctx, *, category_name: str):
        """Add a category to the ticket system."""
        async with self.config.guild(ctx.guild).categories() as categories:
            if category_name in categories:
                await ctx.send(f"Category '{category_name}' already exists.")
                return
            categories.append(category_name)
        await self.update_ticket_message(ctx.guild)
        await ctx.send(f"Category '{category_name}' added to the ticket system.")

    @tickets.command(name="removecategory")
    @commands.has_permissions(manage_channels=True)
    async def remove_category(self, ctx, *, category_name: str):
        """Remove a category from the ticket system."""
        async with self.config.guild(ctx.guild).categories() as categories:
            if category_name in categories:
                categories.remove(category_name)
                await self.update_ticket_message(ctx.guild)
                await ctx.send(f"Category '{category_name}' removed from the ticket system.")
            else:
                await ctx.send(f"Category '{category_name}' does not exist.")

    async def update_ticket_message(self, guild):
        ticket_channel_id = await self.config.guild(guild).ticket_channel_id()
        message_id = await self.config.guild(guild).message_id()
        if ticket_channel_id:
            ticket_channel = guild.get_channel(ticket_channel_id)
            if ticket_channel:
                categories = await self.config.guild(guild).categories()
                view = View(timeout=None)
                for category in categories:
                    button = Button(
                        label=category,
                        style=discord.ButtonStyle.green,
                        custom_id=f"create_ticket_{category}",
                    )
                    button.callback = self.button_callback
                    view.add_item(button)

                embed = discord.Embed(
                    title="Support Tickets",
                    description="Click a button below to create a new ticket in a specific category.",
                )

                if message_id:
                    try:
                        message = await ticket_channel.fetch_message(message_id)
                        await message.edit(embed=embed, view=view)
                    except (discord.NotFound, discord.HTTPException):
                        message = await ticket_channel.send(embed=embed, view=view)
                        await self.config.guild(guild).message_id.set(message.id)
                else:
                    message = await ticket_channel.send(embed=embed, view=view)
                    await self.config.guild(guild).message_id.set(message.id)

    @tickets.command(name="role")
    @commands.has_permissions(manage_channels=True)
    async def add_ticket_roles(self, ctx, *roles: discord.Role):
        """Add roles to the ticket system."""
        async with self.config.guild(ctx.guild).ticket_roles() as ticket_roles:
            for role in roles:
                if role.id not in ticket_roles:
                    ticket_roles.append(role.id)
        role_mentions = " ".join([role.mention for role in roles])
        await ctx.send(f"Roles {role_mentions} added to ticket access.")

    @tickets.command(name="channel")
    @commands.has_permissions(manage_channels=True)
    async def setup_ticket(self, ctx, channel: discord.TextChannel):
        """Set up the ticket system in a channel."""
        guild = ctx.guild
        await self.config.guild(guild).ticket_channel_id.set(channel.id)

        ticket_roles = await self.config.guild(guild).ticket_roles()
        if ticket_roles:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False)
            }
            for role_id in ticket_roles:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=True, manage_threads=True
                    )
            await channel.edit(overwrites=overwrites)
            await ctx.send(
                f"Ticket system set up in {channel.mention} with role-based access and Manage Threads permission."
            )
        else:
            await ctx.send(f"Ticket system set up in {channel.mention}.")

        await self.update_ticket_message(ctx.guild)

    @tickets.command(name="logchannel")
    @commands.has_permissions(manage_channels=True)
    async def setup_log(self, ctx, channel: discord.TextChannel):
        """Set up the ticket log channel."""
        await self.config.guild(ctx.guild).log_channel_id.set(channel.id)
        await ctx.send(f"Ticket log channel set to {channel.mention}")

    async def button_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")
        if custom_id.startswith("create_ticket_"):
            category = custom_id.split("_", 2)[2]
            await self.create_ticket(interaction, category)
        elif custom_id.startswith("close_ticket_"):
            thread_id = int(custom_id.split("_")[-1])
            thread = await self.bot.fetch_channel(thread_id)
            await self.close_ticket(interaction, thread)

    async def create_ticket(self, interaction: discord.Interaction, category: str):
        member = interaction.user
        guild = interaction.guild
        ticket_channel_id = await self.config.guild(guild).ticket_channel_id()
        if ticket_channel_id:
            ticket_channel = guild.get_channel(ticket_channel_id)
            counter = await self.config.guild(guild).ticket_counter()
            thread_name = f"ticket-{counter}-{member.display_name}"
            thread = await ticket_channel.create_thread(
                name=thread_name, auto_archive_duration=4320
            )
            await self.config.guild(guild).ticket_counter.set(counter + 1)

            ticket_roles = await self.config.guild(guild).ticket_roles()
            role_mentions = " ".join(
                [
                    guild.get_role(role_id).mention
                    for role_id in ticket_roles
                    if guild.get_role(role_id) is not None
                ]
            )

            embed = discord.Embed(
                title=f"{category} Ticket",
                description="Support will be with you shortly. Click the button to close this ticket.",
            )
            embed.add_field(
                name="Explain your issue",
                value="Provide details about your issue to help us assist you.",
                inline=False,
            )

            close_button = Button(
                label="Close Ticket",
                style=discord.ButtonStyle.red,
                custom_id=f"close_ticket_{thread.id}",
            )
            close_button.callback = self.button_callback
            view = View(timeout=None)
            view.add_item(close_button)

            await thread.send(
                f"{member.mention} {role_mentions}", embed=embed, view=view
            )
            await interaction.response.send_message("Ticket created!", ephemeral=True)

            log_channel_id = await self.config.guild(guild).log_channel_id()
            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title="Ticket Opened", color=discord.Color.green())
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(
                        name="Created By", value=f"{member.display_name}", inline=False
                    )
                    embed.add_field(name="User ID", value=member.id, inline=False)
                    embed.add_field(
                        name="Opened",
                        value=interaction.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        inline=False,
                    )
                    embed.add_field(name="Category", value=category, inline=False)
                    embed.add_field(name="Ticket Name", value=thread.name, inline=False)
                    view = View(timeout=None)
                    view.add_item(
                        Button(
                            label="Go to Ticket",
                            style=discord.ButtonStyle.link,
                            url=thread.jump_url,
                        )
                    )
                    await log_channel.send(embed=embed, view=view)

    async def close_ticket(self, interaction: discord.Interaction, thread: discord.Thread):
        guild = interaction.guild
        dm_on_close = await self.config.guild(guild).dm_on_close()
        transcript_enabled = await self.config.guild(guild).transcript_enabled()

        if not thread.archived:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Closed",
                    description="Your ticket has been closed.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        await thread.edit(archived=True, locked=True)

        if transcript_enabled:
            messages = [msg async for msg in thread.history(limit=None)]
            transcript = StringIO()
            for msg in reversed(messages):
                transcript.write(
                    f"{msg.author.display_name} [{msg.created_at}]: {msg.content}\n"
                )
            transcript.seek(0)

            if dm_on_close:
                try:
                    await interaction.user.send(
                        file=discord.File(transcript, filename=f"{thread.name}_transcript.txt")
                    )
                except discord.Forbidden:
                    pass

            log_channel_id = await self.config.guild(guild).log_channel_id()
            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    await log_channel.send(
                        file=discord.File(transcript, filename=f"{thread.name}_transcript.txt")
                    )

        log_channel_id = await self.config.guild(guild).log_channel_id()
        if log_channel_id:
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Ticket Closed",
                    description=f"The ticket '{thread.name}' has been closed.",
                    color=discord.Color.red(),
                )
                embed.add_field(name="Closed By", value=interaction.user.mention, inline=False)
                embed.add_field(name="Thread", value=f"[Jump to Ticket]({thread.jump_url})", inline=False)
                await log_channel.send(embed=embed)