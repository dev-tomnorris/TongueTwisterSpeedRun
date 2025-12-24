"""Discord bot client setup."""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_bot() -> commands.Bot:
    """Create and configure Discord bot."""
    # Set up intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    intents.guilds = True
    intents.members = True
    
    # Create bot (command_prefix is required even if we only use slash commands)
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    return bot

