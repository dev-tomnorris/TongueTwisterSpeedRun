"""Discord bot event handlers."""

import discord
from discord import app_commands
from discord.ext import commands
from voice.speech_to_text import initialize_whisper, get_whisper
import os
from dotenv import load_dotenv

load_dotenv()


async def setup_events(bot: commands.Bot):
    """Set up event handlers for the bot."""
    
    @bot.event
    async def on_ready():
        """Called when bot is ready."""
        print(f"{bot.user} has connected to Discord!")
        print(f"Bot is in {len(bot.guilds)} guilds")
        
        # Initialize Whisper
        model_name = os.getenv("WHISPER_MODEL", "base")
        print(f"Initializing Whisper with model: {model_name}")
        initialize_whisper(model_name)
        print("Bot is ready!")
    
    @bot.event
    async def on_error(event, *args, **kwargs):
        """Handle errors."""
        import traceback
        print(f"Error in {event}:")
        traceback.print_exc()
    
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle application command errors."""
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        elif isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.", ephemeral=True)
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while executing this command.", ephemeral=True)
            import traceback
            traceback.print_exc()

