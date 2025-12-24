"""Audio recording from Discord voice channels."""

import discord
import discord.sinks
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime
import config


class AudioRecorder:
    """Records audio from Discord voice channels."""
    
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client = voice_client
        self.sink = None
        self.recording = False
        self.target_user_id = None
        self.recorded_file = None
        self.finished_event = None
    
    async def record_user_audio(
        self,
        user_id: int,
        timeout: float = None
    ) -> Optional[str]:
        """
        Record audio from a user for a specified duration.
        
        Args:
            user_id: Discord user ID to record
            timeout: Maximum recording time in seconds
            
        Returns:
            Path to audio file or None
        """
        if timeout is None:
            timeout = config.VOICE_RECORDING_TIMEOUT
        
        if self.recording:
            return None
        
        self.target_user_id = user_id
        self.recording = True
        self.recorded_file = None
        self.finished_event = asyncio.Event()
        
        # Create a sink to receive audio
        self.sink = discord.sinks.WaveSink()
        
        # Start recording
        self.voice_client.start_recording(
            self.sink,
            self._finished_callback,
            sync_start=False
        )
        
        # Wait for timeout or finish
        try:
            await asyncio.wait_for(self.finished_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Timeout reached, stop recording
            if self.recording:
                self.voice_client.stop_recording()
                await asyncio.sleep(0.5)  # Wait for callback
        
        return self.recorded_file
    
    def _finished_callback(self, sink: discord.sinks.WaveSink, *args):
        """Callback when recording is finished."""
        self.recording = False
        
        # Get audio for the target user
        if self.target_user_id and hasattr(sink, 'audio_data') and self.target_user_id in sink.audio_data:
            audio_data = sink.audio_data[self.target_user_id]
            
            # Save to file
            data_dir = Path("data/audio")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{self.target_user_id}_{timestamp}.wav"
            filepath = data_dir / filename
            
            # Write audio data
            if hasattr(audio_data, 'file'):
                with open(filepath, "wb") as f:
                    f.write(audio_data.file.getvalue())
            elif isinstance(audio_data, bytes):
                with open(filepath, "wb") as f:
                    f.write(audio_data)
            else:
                # Try to get bytes from sink
                try:
                    with open(filepath, "wb") as f:
                        f.write(sink.audio_data[self.target_user_id])
                except:
                    self.recorded_file = None
                    if self.finished_event:
                        self.finished_event.set()
                    return
            
            self.recorded_file = str(filepath)
        else:
            self.recorded_file = None
        
        if self.finished_event:
            self.finished_event.set()

