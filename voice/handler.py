"""Voice channel management."""

import discord
from typing import Optional


class VoiceHandler:
    """Manages Discord voice channel connections."""
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.voice_clients: dict[int, discord.VoiceClient] = {}
    
    async def join_voice_channel(
        self,
        member: discord.Member
    ) -> Optional[discord.VoiceClient]:
        """
        Join the voice channel that a member is in.
        
        Args:
            member: Discord member to join their voice channel
            
        Returns:
            VoiceClient or None if member not in voice channel
        """
        if not member.voice or not member.voice.channel:
            return None
        
        channel = member.voice.channel
        
        # Check if already connected to this channel
        if channel.id in self.voice_clients:
            return self.voice_clients[channel.id]
        
        # Connect to voice channel
        try:
            voice_client = await channel.connect()
            self.voice_clients[channel.id] = voice_client
            return voice_client
        except Exception as e:
            print(f"Error joining voice channel: {e}")
            return None
    
    async def leave_voice_channel(self, channel_id: int) -> bool:
        """
        Leave a voice channel.
        
        Args:
            channel_id: ID of voice channel to leave
            
        Returns:
            True if successfully left, False otherwise
        """
        if channel_id not in self.voice_clients:
            return False
        
        voice_client = self.voice_clients[channel_id]
        
        try:
            await voice_client.disconnect()
            del self.voice_clients[channel_id]
            return True
        except Exception as e:
            print(f"Error leaving voice channel: {e}")
            return False
    
    def get_voice_client(self, channel_id: int) -> Optional[discord.VoiceClient]:
        """Get voice client for a channel."""
        return self.voice_clients.get(channel_id)

