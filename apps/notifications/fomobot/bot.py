# bot.py
import os

import discord
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_NAME = os.getenv("DISCORD_GUILD")

default_intents = discord.Intents.default()
default_intents.members = True

client = discord.Client(intents=default_intents)


def get_userid_from_username(members, username):
    for member in members:
        if "#".join([member.name, member.discriminator]) == username:
            return member.id


def send_discord_bot_notification(username, title, description, color=0xFF2600):
    @client.event
    async def on_ready():
        logger.info(f"{client.user} has connected to Discord!")

        guild = discord.utils.find(lambda g: g.name == GUILD_NAME, client.guilds)
        members = [member for member in guild.members]
        user_id = get_userid_from_username(members, username)

        member = client.get_user(user_id) or await client.fetch_user(user_id)
        embed = discord.Embed(title=title, description=description, color=color)
        await member.send(embed=embed)
        await client.close()

    client.run(TOKEN)


if __name__ == "__main__":
    send_discord_bot_notification(
        "annthomy#8614", title="test", description="test description"
    )
