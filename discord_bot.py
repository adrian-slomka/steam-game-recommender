
import os
import discord
import asyncio

from database import Database
from discord import app_commands
from profiler import Profiler
from dotenv import load_dotenv
load_dotenv()


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced.")

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        self.loop.create_task(self.background_updater())

    async def background_updater(self):
        db = Database()
        await db.update()  # Run once at startup
        while not self.is_closed():
            await asyncio.sleep(24 * 60 * 60)  # Wait 24 hours
            await db.update()


def discord_run():
    client = MyClient(intents=discord.Intents.default())


    # Main command group: /sara
    sara_group = app_commands.Group(name="sara", description="Sara bot commands")

    # Subcommand: /sara trending
    @sara_group.command(name="trending", description="Get trending games for your Steam ID")
    @app_commands.describe(steam_id="Your SteamID64")
    async def trending(interaction: discord.Interaction, steam_id: str):
        msg = Profiler().recommend(steam_id)
        await interaction.response.send_message(msg, ephemeral=True)

    # Subcommand: /sara compare
    @sara_group.command(name="compare", description="Compare two Steam accounts for co-op recommendations")
    @app_commands.describe(steam1="First SteamID64", steam2="Second SteamID64")
    async def compare(interaction: discord.Interaction, steam1: str, steam2: str):
        msg = Profiler().compare(steam1, steam2)
        await interaction.response.send_message(msg, ephemeral=True)

    # Subcommand: /sara update
    @sara_group.command(name="update", description="Manually update the database")
    async def manual_update(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await Database().update()
        await interaction.followup.send("✅ Database updated manually!", ephemeral=True)


    # Add the group to the bot
    client.tree.add_command(sara_group)
    client.run(os.getenv("DISCORD_AUTH"))

if __name__ == "__main__":
    pass