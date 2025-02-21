import aiosqlite
from discord.ext import commands

        
async def create_db(bot: commands.Bot):
    db = bot.db  # use the existing connection from your bot
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS prefixes (guild_id BIGINT, prefix TEXT);
        CREATE TABLE IF NOT EXISTS selfprefix (user_id BIGINT, prefix TEXT);
        CREATE TABLE IF NOT EXISTS nodata (user_id BIGINT, state TEXT);
        CREATE TABLE IF NOT EXISTS snipe (guild_id BIGINT, channel_id BIGINT, author TEXT, content TEXT, attachment TEXT, avatar TEXT, time TEXT);
        CREATE TABLE IF NOT EXISTS afk (guild_id BIGINT, user_id BIGINT, reason TEXT, time INTEGER);
        CREATE TABLE IF NOT EXISTS voicemaster (guild_id BIGINT, channel_id BIGINT, interface BIGINT);
        CREATE TABLE IF NOT EXISTS vcs (user_id BIGINT, voice BIGINT);
        CREATE TABLE IF NOT EXISTS fake_permissions (guild_id BIGINT, role_id BIGINT, permissions TEXT);
        CREATE TABLE IF NOT EXISTS confess (guild_id BIGINT, channel_id BIGINT, confession INTEGER);
        CREATE TABLE IF NOT EXISTS marry (author BIGINT, soulmate BIGINT, time INTEGER);
        CREATE TABLE IF NOT EXISTS mediaonly (guild_id BIGINT, channel_id BIGINT);
        CREATE TABLE IF NOT EXISTS tickets (guild_id BIGINT, message TEXT, channel_id BIGINT, category BIGINT, color INTEGER, logs BIGINT);
        CREATE TABLE IF NOT EXISTS opened_tickets (guild_id BIGINT, channel_id BIGINT, user_id BIGINT);
        CREATE TABLE IF NOT EXISTS ticket_topics (guild_id BIGINT, name TEXT, description TEXT);
        CREATE TABLE IF NOT EXISTS ticket_support (guild_id BIGINT, role_id BIGINT);
        CREATE TABLE IF NOT EXISTS pingonjoin (channel_id BIGINT, guild_id BIGINT);
        CREATE TABLE IF NOT EXISTS autorole (role_id BIGINT, guild_id BIGINT);
        CREATE TABLE IF NOT EXISTS levels (guild_id BIGINT, author_id BIGINT, exp INTEGER, level INTEGER, total_xp INTEGER);
        CREATE TABLE IF NOT EXISTS levelsetup (guild_id BIGINT, channel_id BIGINT, destination TEXT);
        CREATE TABLE IF NOT EXISTS levelroles (guild_id BIGINT, level INTEGER, role_id BIGINT);
        CREATE TABLE IF NOT EXISTS oldusernames (username TEXT, discriminator TEXT, time INTEGER, user_id BIGINT);
        CREATE TABLE IF NOT EXISTS donor (user_id BIGINT, time INTEGER);
        CREATE TABLE IF NOT EXISTS restore (guild_id BIGINT, user_id BIGINT, roles TEXT);
        CREATE TABLE IF NOT EXISTS lastfm (user_id BIGINT, username TEXT);
        CREATE TABLE IF NOT EXISTS lastfmcc (user_id BIGINT, command TEXT);
        CREATE TABLE IF NOT EXISTS lfmode (user_id BIGINT, mode TEXT);
        CREATE TABLE IF NOT EXISTS lfcrowns (user_id BIGINT, artist TEXT);
        CREATE TABLE IF NOT EXISTS lfreactions (user_id BIGINT, reactions TEXT);
        CREATE TABLE IF NOT EXISTS starboardmes (guild_id BIGINT, channel_starboard_id BIGINT, channel_message_id BIGINT, message_starboard_id BIGINT, message_id BIGINT);
        CREATE TABLE IF NOT EXISTS starboard (guild_id BIGINT, channel_id BIGINT, count INTEGER, emoji_id BIGINT, emoji_text TEXT);
        CREATE TABLE IF NOT EXISTS seen (guild_id BIGINT, user_id BIGINT, time INTEGER);
        CREATE TABLE IF NOT EXISTS booster_module (guild_id BIGINT, base BIGINT);
        CREATE TABLE IF NOT EXISTS booster_roles (guild_id BIGINT, user_id BIGINT, role_id BIGINT);
        CREATE TABLE IF NOT EXISTS hardban (guild_id BIGINT, banned BIGINT, author BIGINT);
        CREATE TABLE IF NOT EXISTS forcenick (guild_id BIGINT, user_id BIGINT, nickname TEXT);
        CREATE TABLE IF NOT EXISTS uwulock (guild_id BIGINT, user_id BIGINT);
        CREATE TABLE IF NOT EXISTS shutup (guild_id BIGINT, user_id BIGINT);
        CREATE TABLE IF NOT EXISTS antiinvite (guild_id BIGINT);
        CREATE TABLE IF NOT EXISTS whitelist (guild_id BIGINT, module TEXT, object_id BIGINT, mode TEXT);
        CREATE TABLE IF NOT EXISTS invoke (guild_id BIGINT, command TEXT, embed TEXT);
        CREATE TABLE IF NOT EXISTS chatfilter (guild_id BIGINT, word TEXT);
        CREATE TABLE IF NOT EXISTS autoreact (guild_id BIGINT, trigger TEXT, emojis TEXT);
        CREATE TABLE IF NOT EXISTS welcome (guild_id BIGINT, channel_id BIGINT, mes TEXT);
        CREATE TABLE IF NOT EXISTS leave (guild_id BIGINT, channel_id BIGINT, mes TEXT);
        CREATE TABLE IF NOT EXISTS boost (guild_id BIGINT, channel_id BIGINT, mes TEXT);
        CREATE TABLE IF NOT EXISTS antiraid (guild_id BIGINT, command TEXT, punishment TEXT, seconds INTEGER);
        CREATE TABLE IF NOT EXISTS disablecommand (guild_id BIGINT, command TEXT);
        CREATE TABLE IF NOT EXISTS reactionrole (guild_id BIGINT, message_id BIGINT, channel_id BIGINT, role_id BIGINT, emoji_id BIGINT, emoji_text TEXT);
        CREATE TABLE IF NOT EXISTS editsnipe (guild_id BIGINT, channel_id BIGINT, author_name TEXT, author_avatar TEXT, before_content TEXT, after_content TEXT);
        CREATE TABLE IF NOT EXISTS reactionsnipe (guild_id BIGINT, channel_id BIGINT, author_name TEXT, author_avatar TEXT, emoji_name TEXT, emoji_url TEXT, message_id BIGINT);
        CREATE TABLE IF NOT EXISTS mod (guild_id BIGINT, channel_id BIGINT, jail_id BIGINT, role_id BIGINT);
        CREATE TABLE IF NOT EXISTS cases (guild_id BIGINT, count INTEGER);
        CREATE TABLE IF NOT EXISTS warns (guild_id BIGINT, user_id BIGINT, author_id BIGINT, time TEXT, reason TEXT);
        CREATE TABLE IF NOT EXISTS jail (guild_id BIGINT, user_id BIGINT, roles TEXT);
        CREATE TABLE IF NOT EXISTS authorize (guild_id BIGINT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS gblacklist (guild_id BIGINT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS giveaway (guild_id BIGINT, channel_id BIGINT, message_id BIGINT, title TEXT, host BIGINT, finish INTEGER, winners INTEGER, members TEXT);
        CREATE TABLE IF NOT EXISTS reskin (user_id BIGINT, guild_id BIGINT, name TEXT, avatar TEXT, toggled INTEGER);
        CREATE TABLE IF NOT EXISTS gw_ended (channel_id BIGINT, message_id BIGINT, members TEXT); 
    """)
    await db.commit()