from dataclasses import dataclass
import datetime
import aiosqlite

db = await aiosqlite.connect("database.db")
db.row_factory = aiosqlite.Row

@dataclass
class AntiNukeModule:
    module: str
    punishment: str  # Ban, Warn, or Kick
    threshold: int
    toggled: bool
    
    @classmethod
    async def from_database(cls, db: aiosqlite.Connection, guild_id: int, module: str):
        # Assuming the connection's row factory returns a dictionary-like object
        async with db.execute(
            "SELECT * FROM antinuke_modules WHERE guild_id = ? AND module = ?",
            (guild_id, module)
        ) as cursor:
            data = await cursor.fetchone()
        if not data:
            return None
        return cls(
            module=module,
            punishment=data['punishment'],
            threshold=data['threshold'],
            toggled=data['toggled']
        )
    
    async def update(self, db: aiosqlite.Connection, guild_id: int):
        await db.execute(
            "UPDATE antinuke_modules SET punishment = ?, threshold = ?, toggled = ? WHERE guild_id = ? AND module = ?",
            (self.punishment, self.threshold, self.toggled, guild_id, self.module)
        )
        await db.commit()

@dataclass
class AntiNukeUser:
    module: str
    user_id: int
    last_action: datetime.datetime
    amount: int
