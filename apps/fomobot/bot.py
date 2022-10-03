# bot.py
import os

import discord
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    GUILD = os.getenv("DISCORD_GUILD")
    default_intents = discord.Intents.default()
    default_intents.members = True

    client = discord.Client(intents=default_intents)
    USER_IDS = [304666698114400257]

    @client.event
    async def on_ready():
        guild = discord.utils.find(lambda g: g.name == GUILD, client.guilds)

        print(
            f"{client.user} is connected to the following guild:\n"
            f"{guild.name}(id: {guild.id})"
        )

        members = [member.id for member in guild.members]
        print(f"Guild Members:\n - {members}")

        user = client.get_user(USER_IDS[0]) or await client.fetch_user(USER_IDS[0])
        await user.send("Test pour te faire iech!")

        # guild = client.get_guild(guild.id)  # specify guild_id here
        # for member in filter(lambda member_: member_.id in USER_IDS, guild.members):
        #     await member.send("test message")

    client.run(TOKEN)
