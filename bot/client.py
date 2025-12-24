"""Discord bot client setup."""

import discord
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_bot() -> discord.Bot:
    """Create and configure Discord bot."""
    # Set up intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    intents.guilds = True
    intents.members = True
    
    # Create bot
    bot = discord.Bot(intents=intents)
    
    return bot

