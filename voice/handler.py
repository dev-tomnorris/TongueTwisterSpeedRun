"""Voice channel management."""

import discord
from discord.ext import commands
from typing import Optional

# Try to import voice receiving extension
try:
    from discord.ext import voice_recv
    VOICE_RECV_AVAILABLE = True
except ImportError:
    VOICE_RECV_AVAILABLE = False


class VoiceHandler:
    """Manages Discord voice channel connections."""
    
    def __init__(self, bot: commands.Bot):
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
            existing_client = self.voice_clients[channel.id]
            # If VoiceRecv is available but we have a regular VoiceClient, reconnect
            if VOICE_RECV_AVAILABLE and not isinstance(existing_client, voice_recv.VoiceRecvClient):
                print("[INFO] Reconnecting with VoiceRecvClient to enable audio receiving...")
                try:
                    await existing_client.disconnect()
                    del self.voice_clients[channel.id]
                except:
                    pass
            else:
                return existing_client
        
        # Connect to voice channel
        try:
            # Use voice_recv if available, otherwise use standard connection
            if VOICE_RECV_AVAILABLE:
                print(f"[INFO] Connecting with VoiceRecvClient for audio receiving...")
                voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)
                print(f"[INFO] Connected! Voice client type: {type(voice_client).__name__}")
            else:
                print(f"[WARNING] VoiceRecv not available, using standard VoiceClient")
                voice_client = await channel.connect()
            self.voice_clients[channel.id] = voice_client
            return voice_client
        except Exception as e:
            print(f"Error joining voice channel: {e}")
            import traceback
            traceback.print_exc()
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

