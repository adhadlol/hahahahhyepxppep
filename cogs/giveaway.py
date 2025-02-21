import discord, json, humanfriendly, asyncio, datetime, random
from discord.ext import commands
from patches.permissions import Permissions
from events.tasks import gwend_task, gw_loop

class GiveawayView(discord.ui.View): 
    def __init__(self): 
        super().__init__(timeout=None) 

    @discord.ui.button(emoji="🎉", style=discord.ButtonStyle.green, custom_id="persistent:join_gw")
    async def join_gw(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with interaction.client.db.execute(
            "SELECT * FROM giveaway WHERE guild_id = ? AND message_id = ?", 
            (interaction.guild.id, interaction.message.id)
        ) as cursor:
            check = await cursor.fetchone()

            if check is None:
                return await interaction.response.send_message("This giveaway does not exist.", ephemeral=True)

            columns = [column[0] for column in cursor.description]  # Extract column names
            check_dict = dict(zip(columns, check))  # Convert tuple to dict
            lis = json.loads(check_dict["members"])  # ✅ Now it works!

        if interaction.user.id in lis: 
            button1 = discord.ui.Button(label="Leave the Giveaway", style=discord.ButtonStyle.danger)

            async def button1_callback(inter: discord.Interaction): 
                lis.remove(interaction.user.id)
                await interaction.client.db.execute(
                    "UPDATE giveaway SET members = ? WHERE guild_id = ? AND message_id = ?", 
                    (json.dumps(lis), inter.guild.id, interaction.message.id)
                ) 
                await interaction.client.db.commit()

                interaction.message.embeds[0].set_field_at(0, name="Entries", value=f"{len(lis)}")
                await interaction.message.edit(embed=interaction.message.embeds[0])
                return await inter.response.edit_message(content="You left the giveaway", view=None)

            button1.callback = button1_callback
            vi = discord.ui.View()
            vi.add_item(button1)
            return await interaction.response.send_message(content="You are already in this giveaway", view=vi, ephemeral=True)
        else: 
            lis.append(interaction.user.id)
            await interaction.client.db.execute(
                "UPDATE giveaway SET members = ? WHERE guild_id = ? AND message_id = ?", 
                (json.dumps(lis), interaction.guild.id, interaction.message.id)
            ) 
            await interaction.client.db.commit()

            interaction.message.embeds[0].set_field_at(0, name="Entries", value=f"{len(lis)}")
            return await interaction.response.edit_message(embed=interaction.message.embeds[0])
      
class giveaway(commands.Cog): 
    def __init__(self, bot: commands.Bot): 
        self.bot = bot 

    @commands.Cog.listener()
    async def on_connect(self): 
        gw_loop.start(self.bot)

    @commands.command(name="gcreate", brief="manage server", description="Create a giveaway", usage="<channel>")
    @Permissions.has_permission(manage_guild=True) 
    async def gcreate(self, ctx: commands.Context, *, channel: discord.TextChannel = None):  
        return await ctx.invoke(self.bot.get_command('giveaway create'), channel=channel or ctx.channel) 
  
    @commands.group(invoke_without_command=True, aliases=['gw'])
    async def giveaway(self, ctx): 
        return await ctx.create_pages()
  
    @giveaway.command(name="end", brief="manage_server", description="End a giveaway", usage="[message id] <channel>")
    @Permissions.has_permission(manage_guild=True) 
    async def gw_end(self, ctx: commands.Context, message_id: int, *, channel: discord.TextChannel = None): 
        if not channel: 
            channel = ctx.channel
        async with self.bot.db.execute(
            "SELECT * FROM giveaway WHERE guild_id = ? AND channel_id = ? AND message_id = ?", 
            (ctx.guild.id, channel.id, message_id)
        ) as cursor:
            check = await cursor.fetchone()

        if not check: 
            return await ctx.warning("This message is not a giveaway or it ended.")

        await gwend_task(self.bot, check, datetime.datetime.now())
        return await ctx.success(f"Ended giveaway in {channel.mention}")

    @giveaway.command(name="reroll", description="Reroll a giveaway", brief="Manage server", usage="[message id] <channel>")
    @Permissions.has_permission(manage_guild=True) 
    async def gw_reroll(self, ctx: commands.Context, message_id: int, *, channel: discord.TextChannel = None): 
        if not channel: 
            channel = ctx.channel
        async with self.bot.db.execute(
            "SELECT * FROM gw_ended WHERE channel_id = ? AND message_id = ?", 
            (channel.id, message_id)
        ) as cursor:
            check = await cursor.fetchone()

        if not check: 
            return await ctx.warning(f"This message is not a giveaway or it hasn't ended yet. Use `{ctx.clean_prefix}gend` to end it.")

        members = json.loads(check[4])  # Fetching 'members' column by index
        await ctx.reply(f"**New winner:** <@!{random.choice(members)}>")

    @giveaway.command(name="list", description="List active giveaways", help="config")
    @Permissions.has_permission(manage_guild=True) 
    async def gw_list(self, ctx: commands.Context): 
        async with self.bot.db.execute("SELECT * FROM giveaway WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
            results = await cursor.fetchall()

        if len(results) == 0: 
            return await ctx.error("There are no giveaways")

        embeds = []
        for i, result in enumerate(results):
            embed = discord.Embed(
                color=self.bot.color, 
                title=f"Giveaways ({len(results)})",
                description=f"`{i+1}` [**{result[3]}**](https://discord.com/channels/{ctx.guild.id}/{result[1]}/{result[2]}) ends <t:{int(result[5])}:R>"
            )
            embeds.append(embed)

        await ctx.paginate(embeds)  

    @giveaway.command(name="create", brief="Manage server", description="Create a giveaway", usage="<channel>")
    @Permissions.has_permission(manage_guild=True) 
    async def gw_create(self, ctx: commands.Context, *, channel: discord.TextChannel = None):
        if not channel: 
            channel = ctx.channel 
        await ctx.reply(f"Starting giveaway in {channel.mention}...")
    
        questions = [
            "What is the prize for this giveaway?", 
            "How long should the giveaway last?", 
            "How many winners should this giveaway have?"
        ]

        responses = [] 
        for question in questions:
            await ctx.send(question)
            try:
                message = await self.bot.wait_for('message', timeout=10.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                responses.append(message.content)
            except asyncio.TimeoutError:
                return await ctx.send(content="You didn't reply in time.")

        try:
            description = responses[0]
            seconds = humanfriendly.parse_timespan(responses[1])
            winners = int(responses[2])
        except (ValueError, humanfriendly.InvalidTimespan):
            return await ctx.send(content="Invalid input.")

        end_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        embed = discord.Embed(
            color=self.bot.color, 
            title=description,
            description=f"Ends: <t:{int(end_time.timestamp())}:R>\nHosted by: {ctx.author.mention}\nWinners: **{winners}**"
        )
        embed.add_field(name="Entries", value="0")
        view = GiveawayView()

        mes = await channel.send(embed=embed, view=view)
        await self.bot.db.execute(
            "INSERT INTO giveaway (guild_id, channel_id, message_id, winners, members, finish, host, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ctx.guild.id, channel.id, mes.id, winners, json.dumps([]), int(end_time.timestamp()), ctx.author.id, description)
        )
        await self.bot.db.commit()
        await ctx.send(f"Giveaway setup completed in {channel.mention}.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(giveaway(bot))