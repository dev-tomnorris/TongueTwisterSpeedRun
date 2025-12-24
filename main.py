"""Main entry point for Tongue Twister Bot."""

import discord
import asyncio
import os
from dotenv import load_dotenv
from bot.client import create_bot
from bot.events import setup_events
from database.migrations import initialize_database
from cogs import game_commands

# Load environment variables
load_dotenv()


async def main():
    """Main function to start the bot."""
    # Initialize database
    print("Initializing database...")
    await initialize_database()
    print("Database initialized!")
    
    # Create bot
    bot = create_bot()
    
    # Setup events
    setup_events(bot)
    
    # Load cogs
    bot.load_extension('cogs.game_commands')
    
    # Get token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your Discord bot token.")
        return
    
    # Start bot
    print("Starting bot...")
    await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc()

