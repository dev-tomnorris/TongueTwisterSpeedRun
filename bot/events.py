"""Discord bot event handlers."""

import discord
from voice.speech_to_text import initialize_whisper, get_whisper
import os
from dotenv import load_dotenv

load_dotenv()


async def setup_events(bot: discord.Bot):
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
    
    @bot.event
    async def on_application_command_error(ctx: discord.ApplicationContext, error: Exception):
        """Handle application command errors."""
        if isinstance(error, discord.CheckFailure):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        elif isinstance(error, discord.CommandOnCooldown):
            await ctx.respond(f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.", ephemeral=True)
        else:
            await ctx.respond("An error occurred while executing this command.", ephemeral=True)
            import traceback
            traceback.print_exc()

