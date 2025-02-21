import discord, os
import aiosqlite
from discord.ext.commands import Context 
from discord import Embed, utils, ButtonStyle, Message
from typing import Any, Union, Dict, Optional, List, Sequence
from discord.ui import View
from discord.ext import commands
from bot.ext import PaginatorView

class YepContext(Context): 
    flags: Dict[str, Any] = {}

    async def getprefix(bot, message):
        if not message.guild:
            return ";"
        
        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT * FROM selfprefix WHERE user_id = ?", (message.author.id,)) as cursor:
                check = await cursor.fetchone()
                selfprefix = check["prefix"] if check else ";"

            async with db.execute("SELECT * FROM prefixes WHERE guild_id = ?", (message.guild.id,)) as cursor:
                res = await cursor.fetchone()
                guildprefix = res["prefix"] if res else ";"

            if not check and res:
                selfprefix = res["prefix"]
            elif not check and not res:
                selfprefix = ";"

        return guildprefix, selfprefix

    def find_role(self, name: str): 
        for role in self.guild.roles:
            if role.name == "@everyone":
                continue  
            if name.lower() in role.name.lower():
                return role 
        return None 

    async def success(self, message: str) -> discord.Message:  
        return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {self.author.mention}: {message}"))

    async def neutral(self, message: str) -> discord.Message:  
        return await self.reply(embed=discord.Embed(color=self.bot.color, description=message))

    async def error(self, message: str) -> discord.Message: 
        return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.no} {self.author.mention}: {message}"))

    async def warning(self, message: str) -> discord.Message: 
        return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.warning} {self.author.mention}: {message}"))

    async def check(self):
        return await self.message.add_reaction("✅")

    async def reply(self, content: Optional[str] = None, *, embed: Optional[discord.Embed] = None, view: Optional[discord.ui.View] = None, mention_author: bool = False, file: Optional[discord.File] = None) -> discord.Message:
        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT * FROM reskin WHERE user_id = ? AND toggled = ?", (self.author.id, True)) as cursor:
                reskin = await cursor.fetchone()

        if reskin:
            hook = await self.webhook(self.message.channel)
            return await hook.send(content=content, embed=embed, username=reskin['name'], avatar_url=reskin['avatar'], file=file)

        return await self.send(content=content, embed=embed, reference=self.message, view=view, mention_author=mention_author, file=file)

    async def send(self, content: Optional[str] = None, *, embed: Optional[discord.Embed] = None, view: Optional[discord.ui.View] = None, mention_author: bool = False, reference: Optional[discord.Message] = None, file: Optional[discord.File] = None) -> discord.Message:
        return await self.channel.send(content=content, embed=embed, view=view, reference=reference, mention_author=mention_author, file=file)

    async def webhook(self, channel) -> discord.Webhook:
        for webhook in await channel.webhooks():
            if webhook.user == self.me:
                return webhook
        return await channel.create_webhook(name='yep')

    async def cmdhelp(self): 
        command = self.command
        commandname = f"{str(command.parent)} {command.name}" if command.parent else command.name

        embed = discord.Embed(color=self.bot.color, title=commandname, description=command.description)
        embed.set_author(name=self.author.name, icon_url=self.author.display_avatar.url or '')
        embed.add_field(name="aliases", value=', '.join(command.aliases) or "none")
        embed.add_field(name="permissions", value=command.brief or "any")
        embed.add_field(name="usage", value=f"""```{commandname} {command.usage or ''}```""", inline=False)
        embed.set_footer(text=f'module: {command.cog_name}', icon_url=self.author.display_avatar.url or '')

        await self.reply(embed=embed)
    
class HelpCommand(commands.HelpCommand):
  def __init__(self, **kwargs):
   self.ec_color = 0xCCCCFF
   super().__init__(**kwargs)

  async def send_bot_help(self, ctx: commands.Context) -> None:
    return await self.context.reply(f'{self.context.author.mention}: check <https://evict.cc/commands> for list of commands')
  
  async def send_command_help(self, command: commands.Command):
    
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    
    embed = discord.Embed(color=self.ec_color, title=commandname, description=command.description)
    embed.set_author(name=self.context.author.name, icon_url=self.context.author.display_avatar.url if not None else '')
    embed.add_field(name="aliases", value=', '.join(map(str, command.aliases)) or "none")
    embed.add_field(name="permissions", value=command.brief or "any")
    embed.add_field(name="usage", value=f"{commandname} {command.usage if command.usage else ''}", inline=False)
    embed.set_footer(text=f'module: {command.cog_name}', icon_url=self.context.author.display_avatar.url if not None else '')
    
    await self.context.reply(embed=embed)

  async def send_group_help(self, group: commands.Group): 
   
   ctx = self.context
   embeds = []
   i=0
   
   for command in group.commands: 
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    i+=1 
    
    embeds.append(discord.Embed(color=self.ec_color, title=f"{commandname}", description=command.description)
                  .set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url if not None else '')
                  .add_field(name="aliases", value=', '.join(map(str, command.aliases)) or "none")
                  .add_field(name="permissions", value=command.brief or "any")
                  .add_field(name="usage", value=f"{commandname} {command.usage if command.usage else ''}", inline=False)
                  .set_footer(text=f"module: {command.cog_name} ・ page {i}/{len(group.commands)}", icon_url=ctx.author.display_avatar.url if not None else ''))
     
   return await self.context.paginator(embeds)
 
 
class StartUp:

 async def startup(bot):
    await bot.wait_until_ready()

 async def loadcogs(self): 
  
  for file in os.listdir("./events"): 
   if file.endswith(".py"):
    try:
     await self.load_extension(f"events.{file[:-3]}")
     print(f"Loaded plugin {file[:-3]}".lower())
    except Exception as e: print("failed to load %s %s".lower(), file[:-3], e)
  
  for fil in os.listdir("./cogs"):
   if fil.endswith(".py"):
    try:
     await self.load_extension(f"cogs.{fil[:-3]}")
     print(f"Loaded plugin {fil[:-3]}".lower())
    except Exception as e: print("failed to load %s %s".lower(), fil[:-3], e)