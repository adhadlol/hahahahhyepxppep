from discord.ext import tasks, commands
from discord.ext.commands import check
import discord, datetime
import arrow, random, json

class task(commands.Cog): 
    def __init__(self, bot: commands.Bot): 
        self.bot = bot 

@tasks.loop(minutes=10)
async def counter_update(bot: commands.Bot): 
    async with bot.db.execute("SELECT * FROM counters") as cursor:
        columns = [column[0] for column in cursor.description]  # Extract column names
        async for row in cursor:
            result = dict(zip(columns, row))  # Convert tuple to dict

            channel = bot.get_channel(int(result["channel_id"]))
            if channel: 
                guild = channel.guild 
                module = result["module"]
                if module == "members": 
                    target = str(guild.member_count)
                elif module == "humans": 
                    target = str(len([m for m in guild.members if not m.bot]))
                elif module == "bots": 
                    target = str(len([m for m in guild.members if m.bot])) 
                elif module == "boosters": 
                    target = str(len(guild.premium_subscribers))
                elif module == "voice": 
                    target = str(sum(len(c.members) for c in guild.voice_channels))     
                name = result["channel_name"].replace("{target}", target)
                await channel.edit(name=name, reason="updating counter")         

@tasks.loop(hours=6)
async def snipe_delete(bot: commands.Bot):
    await bot.db.execute("DELETE FROM snipe")
    await bot.db.commit()

@tasks.loop(hours=6)
async def edit_snipe_delete(bot: commands.Bot):
    await bot.db.execute("DELETE FROM editsnipe")
    await bot.db.commit()

@tasks.loop(hours=6)
async def reaction_snipe_delete(bot: commands.Bot):
    await bot.db.execute("DELETE FROM reactionsnipe")   
    await bot.db.commit()

@tasks.loop(seconds=5)
async def gw_loop(bot: commands.Bot):
    async with bot.db.execute("SELECT * FROM giveaway") as cursor:
        columns = [column[0] for column in cursor.description]
        async for row in cursor:
            result = dict(zip(columns, row))  # Convert tuple to dict
            date = datetime.datetime.now()

            if date.timestamp() > result["finish"]:
                await gwend_task(bot, result, date)

async def gwend_task(bot: commands.Bot, result, date: datetime.datetime): 
    members = json.loads(result["members"])
    winners = result["winners"]
    channel_id = result["channel_id"]
    message_id = result["message_id"]
    channel = bot.get_channel(channel_id)
    
    if channel:   
        message = await channel.fetch_message(message_id)
        if message:    
            wins = []
            if len(members) <= winners:       
                embed = discord.Embed(color=bot.color, title=message.embeds[0].title, description=f"Hosted by: <@!{result['host_id']}>\n\nNot enough entries to determine the winners!")
                await message.edit(embed=embed, view=None)
            else:  
                for _ in range(winners): 
                    wins.append(random.choice(members))
                embed = discord.Embed(
                    color=bot.color, 
                    title=message.embeds[0].title, 
                    description=f"Ended <t:{int(date.timestamp())}:R>\nHosted by: <@!{result['host_id']}>"
                ).add_field(name="Winners", value='\n'.join([f"**{bot.get_user(w)}** ({w})" for w in wins]))
                await message.edit(embed=embed, view=None)
                await message.reply(f"**{result['title']}** winners:\n" + '\n'.join([f"<@{w}> ({w})" for w in wins])) 
    
    await bot.db.execute("INSERT INTO gw_ended (channel_id, message_id, members) VALUES (?, ?, ?)", (channel_id, message_id, json.dumps(members)))
    await bot.db.execute("DELETE FROM giveaway WHERE channel_id = ? AND message_id = ?", (channel_id, message_id))
    await bot.db.commit()

def is_there_a_reminder(): 
    async def predicate(ctx: commands.Context):
        async with ctx.bot.db.execute("SELECT * FROM reminder WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id)) as cursor:
            check = await cursor.fetchone()
        
        if not check: 
            await ctx.warning("You don't have a reminder set in this server")
        return check is not None

    return check(predicate) 

@tasks.loop(seconds=5)
async def reminder_task(bot: commands.Bot): 
    async with bot.db.execute("SELECT * FROM reminder") as cursor:
        columns = [column[0] for column in cursor.description]
        async for row in cursor:
            result = dict(zip(columns, row))  # Convert tuple to dict

            if datetime.datetime.now().timestamp() > result["date"]: 
                channel = bot.get_channel(int(result["channel_id"]))
                if channel:
                    await channel.send(f"🕰️ <@{result['user_id']}> {result['task']}")
                    await bot.db.execute("DELETE FROM reminder WHERE guild_id = ? AND user_id = ? AND channel_id = ?", (channel.guild.id, result["user_id"], channel.id))   
                    await bot.db.commit()

@tasks.loop(seconds=10)
async def bday_task(bot: commands.Bot): 
    async with bot.db.execute("SELECT * FROM birthday") as cursor:
        columns = [column[0] for column in cursor.description]
        async for row in cursor:
            result = dict(zip(columns, row))  # Convert tuple to dict

            bday = arrow.get(result["bday"])
            today = arrow.utcnow()
            
            if bday.day == today.day and bday.month == today.month:
                if result["said"] == "false":  
                    member = await bot.fetch_user(result["user_id"])
                    if member: 
                        try: 
                            await member.send("🎂 Happy birthday!!")
                            await bot.db.execute("UPDATE birthday SET said = ? WHERE user_id = ?", ("true", result["user_id"]))
                            await bot.db.commit()
                        except: 
                            continue   
            else: 
                if result["said"] == "true": 
                    await bot.db.execute("UPDATE birthday SET said = ? WHERE user_id = ?", ("false", result["user_id"]))
                    await bot.db.commit()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(task(bot))