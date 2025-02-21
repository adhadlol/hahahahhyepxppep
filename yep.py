import discord_ios
from bot.bot import yep
import discord
from discord.ext import commands
import aiosqlite
import os
import json

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"

with open("config.json") as f:
    config = json.load(f)

bot = yep(config)

@bot.check
async def cooldown_check(ctx: commands.Context):
    bucket = bot.global_cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.member)
    return True

async def check_ratelimit(ctx):
    cd = bot.m_cd2.get_bucket(ctx.message)
    return cd.update_rate_limit()

async def get_db():
    if not hasattr(bot, "db") or bot.db is None:
        bot.db = await aiosqlite.connect("database.db")
    return bot.db

@bot.check 
async def blacklist(ctx: commands.Context): 
    rl = await check_ratelimit(ctx)
    if rl:
        return
    if ctx.guild is None:
        return False

    db = await get_db()
    
    async with db.execute("SELECT * FROM nodata WHERE user_id = ?", (ctx.author.id,)) as cursor:
        check = await cursor.fetchone()

    if check is not None:
        return check[1] != "false"

    embed = discord.Embed(
        color=bot.color, 
        description="Do you **agree** to our [privacy policy](https://evict.cc/privacy)?\n"
                    "**DISAGREEING** will result in a blacklist from using bot's commands"
    )
    yes = discord.ui.Button(emoji=bot.yes, style=discord.ButtonStyle.gray)
    no = discord.ui.Button(emoji=bot.no, style=discord.ButtonStyle.gray)

    async def yes_callback(interaction: discord.Interaction):
        channel = bot.get_channel(1341992247104634921)

        if interaction.user != ctx.author:
            return await interaction.response.send_message(
                embed=discord.Embed(color=bot.color, description=f"{bot.warning} {interaction.user.mention}: This is not your message"), 
                ephemeral=True
            )

        db = await get_db()
        await db.execute("INSERT INTO nodata VALUES (?, ?)", (ctx.author.id, "true"))
        await db.commit()

        await interaction.message.delete()
        await bot.process_commands(ctx.message)

        embed = discord.Embed(title="yep Logs", description="User agreed to yep's privacy policy & terms of service.", color=bot.color)
        embed.add_field(name="User", value=f"{interaction.user}", inline=False)
        embed.add_field(name="User ID", value=f"{interaction.user.id}", inline=False)
        embed.add_field(name="Guild", value=f"{ctx.guild.name}", inline=False)
        embed.add_field(name="Guild ID", value=f"{ctx.guild.id}", inline=False)
        embed.set_thumbnail(url=bot.user.avatar.url)
        await channel.send(embed=embed)

    yes.callback = yes_callback

    async def no_callback(interaction: discord.Interaction):
        channel = bot.get_channel(1341992247104634921)

        if interaction.user != ctx.author:
            return await interaction.response.send_message(
                embed=discord.Embed(color=bot.color, description=f"{bot.warning} {interaction.user.mention}: This is not your message"), 
                ephemeral=True
            )

        db = await get_db()
        await db.execute("INSERT INTO nodata VALUES (?, ?)", (ctx.author.id, "false"))
        await db.commit()

        await interaction.response.edit_message(
            embed=discord.Embed(
                color=bot.color, 
                description="You got blacklisted from using bot's commands. "
                            "If this is a mistake, please check our [**support server**](https://discord.gg/evict)"
            ), 
            view=None
        )

        embed = discord.Embed(title="yep Logs", description="User got blacklisted for saying no on callback.", color=bot.color)
        embed.add_field(name="User", value=f"{interaction.user}", inline=False)
        embed.add_field(name="User ID", value=f"{interaction.user.id}", inline=False)
        embed.add_field(name="Guild", value=f"{ctx.guild.name}", inline=False)
        embed.add_field(name="Guild ID", value=f"{ctx.guild.id}", inline=False)
        embed.set_thumbnail(url=bot.user.avatar.url)
        await channel.send("<@1341992375207071846>")
        await channel.send(embed=embed)

    no.callback = no_callback

    view = discord.ui.View()
    view.add_item(yes)
    view.add_item(no)
    await ctx.reply(embed=embed, view=view, mention_author=False)

@bot.check
async def is_chunked(ctx: commands.Context):
    if ctx.guild:
        if not ctx.guild.chunked:
            await ctx.guild.chunk(cache=True)
        return True

@bot.check
async def disabled_command(ctx: commands.Context):
    cmd = bot.get_command(ctx.invoked_with)
    if not cmd:
        return True
    db = await get_db()

    async with db.execute('SELECT * FROM disablecommand WHERE command = ? AND guild_id = ?', (cmd.name, ctx.guild.id)) as cursor:
        check = await cursor.fetchone()

    if check:
        await ctx.warning(f"The command **{cmd.name}** is **disabled**")
    return check is None

@bot.check
async def restricted_command(ctx: commands.Context):
    if ctx.author.id == ctx.guild.owner.id or ctx.author.id in bot.owner_ids:
        return True

    db = await get_db()

    async with db.execute("SELECT * FROM restrictcommand WHERE guild_id = ? AND command = ?", 
                          (ctx.guild.id, ctx.command.qualified_name)) as cursor:
        check = await cursor.fetchall()

    if check:
        for row in check:
            role = ctx.guild.get_role(row[1])
            if not role:
                await db.execute("DELETE FROM restrictcommand WHERE role_id = ?", (row[1],))
                await db.commit()
            if role not in ctx.author.roles:
                await ctx.warning(f"You cannot use `{ctx.command.qualified_name}`")
                return False
        return True
    return True

if __name__ == '__main__':
    bot.run(str(config["token"]))