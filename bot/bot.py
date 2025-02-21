import discord, aiosqlite, json, aiohttp, random, asyncio, datetime, os
from discord.ext import commands, tasks
from discord import Embed
from pymongo import MongoClient
import typing
from typing import List

from bot.database import create_db
from bot.helpers import StartUp
from bot.helpers import YepContext, HelpCommand

from cogs.giveaway import GiveawayView


config = json.load(open("config.json", encoding="UTF-8"))

class yep(commands.AutoShardedBot):
    def __init__(self, config):
        self.config = config
        self.cluster = MongoClient(config["mongo"])
        self.color = 0xffd4d4
        self.error_color = 0xFFFFED
        self.yes = "<:check:1099886706703999096>"
        self.no = "<:deny:1099886708457222215> "
        self.warning = "<:warning:1099217491709935687>"
        self.left = "<a:leftarrow:1099036501922287646>"
        self.right = "<a:rightarrow:1099216036844281958>"
        self.goto = "<:hammer:1099879884936986714> "
        self.m_cd = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.member)
        self.c_cd = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.channel)
        self.m_cd2 = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.member)
        self.global_cd = commands.CooldownMapping.from_cooldown(2, 3, commands.BucketType.member)
        intents = discord.Intents.all()
        # Record when the bot starts
        self.start_time = datetime.datetime.utcnow()  
        super().__init__(  # call to super must come after setting any attributes you want to use later
            help_command=HelpCommand(),
            intents=intents,
            command_prefix=YepContext.getprefix,         
            owner_ids=[1050907666068807721, 837939884429279252, 837939884429279252],
            case_insensitive=True,
            activity=discord.CustomActivity(name="🔗 yep.rip"),
        )

    async def on_ready(self) -> None:
        print("I'm online!")
        await self.cogs["Music"].start_nodes()

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.NotOwner):
            pass
        if isinstance(error, commands.CheckFailure):
            if isinstance(error, commands.MissingPermissions):
                return await ctx.warning(f"This command requires **{error.missing_permissions[0]}** permission")
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.command.name != "hit":
                return await ctx.reply(
                    embed=discord.Embed(color=0xE1C16E, description=f"⌛ {ctx.author.mention}: You are on cooldown. Try again in {format_timespan(error.retry_after)}"),
                    mention_author=False,
                )
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.cmdhelp()
        if isinstance(error, commands.EmojiNotFound):
            return await ctx.warning(f"Unable to convert {error.argument} into an **emoji**")
        if isinstance(error, commands.MemberNotFound):
            return await ctx.warning(f"Unable to find member **{error.argument}**")
        if isinstance(error, commands.UserNotFound):
            return await ctx.warning(f"Unable to find user **{error.argument}**")
        if isinstance(error, commands.RoleNotFound):
            return await ctx.warning(f"Couldn't find role **{error.argument}**")
        if isinstance(error, commands.ChannelNotFound):
            return await ctx.warning(f"Couldn't find channel **{error.argument}**")
        if isinstance(error, commands.ThreadNotFound):
            return await ctx.warning(f"I was unable to find the thread **{error.argument}**")
        if isinstance(error, commands.UserConverter):
            return await ctx.warning(f"Couldn't convert that into an **user** ")
        if isinstance(error, commands.MemberConverter):
            return await ctx.warning("Couldn't convert that into a **member**")
        if isinstance(error, commands.BadArgument):
            return await ctx.warning(error.args[0])
        if isinstance(error, commands.BotMissingPermissions):
            return await ctx.warning(f"I do not have enough **permissions** to execute this command")
        if isinstance(error, commands.CommandInvokeError):
            return await ctx.warning(error.original)
        if isinstance(error, discord.HTTPException):
            return await ctx.warning("Unable to execute this command")
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.warning(f"This command cannot be used in private messages.")
        if isinstance(error, commands.UserInputError):
            return await ctx.send_help(ctx.command.qualified_name)
        if isinstance(error, discord.NotFound):
            return await ctx.warning(f"**Not found** - the **ID** is invalid")
        if isinstance(error, commands.GuildNotFound):
            return await ctx.warning(f"I was unable to find that **server** or the **ID** is invalid")
        if isinstance(error, commands.BadInviteArgument):
            return await ctx.warning(f"Invalid **invite code** given")

    async def channel_ratelimit(self, message: discord.Message) -> typing.Optional[int]:
        cd = self.c_cd
        bucket = cd.get_bucket(message)
        return bucket.update_rate_limit()

    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.process_commands(after)

    async def prefixes(self, message: discord.Message) -> list[str]:
        prefixes = []
        for l in set(p for p in await self.command_prefix(self, message)):
            prefixes.append(l)
        return prefixes

    async def member_ratelimit(self, message: discord.Message) -> typing.Optional[int]:
        cd = self.m_cd
        bucket = cd.get_bucket(message)
        return bucket.update_rate_limit()

    async def on_message(self, message: discord.Message):
        channel_rl = await self.channel_ratelimit(message)
        member_rl = await self.member_ratelimit(message)

        if channel_rl:
            return

        if member_rl:
            return

        if message.content == f"<@{self.user.id}>":
            return await message.reply(content="prefixes: " + " ".join(f"`{g}`" for g in await self.prefixes(message)))

        await self.process_commands(message)


    async def create_db_pool(self):
        self.db = await aiosqlite.connect("database.db")
        print("Database connected!")


    async def setup_hook(self):

        self.add_view(GiveawayView())

        await self.load_extension('jishaku')
        await self.create_db_pool()
        await StartUp.loadcogs(self)
        await create_db(self)

        # Run table setup from external file
        await create_db(self)

    async def on_ready(self):
        print(f"Logged in as {self.user} ({self.user.id})")

    async def get_context(self, message: discord.Message, cls=YepContext) -> YepContext:
        return await super().get_context(message, cls=cls)
