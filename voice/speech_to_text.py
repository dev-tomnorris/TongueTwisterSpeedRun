"""Speech-to-text using OpenAI Whisper."""

import whisper
import asyncio
import os
from pathlib import Path
from typing import Optional


class WhisperSTT:
    """Whisper speech-to-text handler."""
    
    def __init__(self, model_name: str = "base"):
        """Initialize Whisper model."""
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model (synchronous, called at startup)."""
        print(f"Loading Whisper model: {self.model_name}...")
        self.model = whisper.load_model(self.model_name)
        print(f"Whisper model loaded successfully!")
    
    async def transcribe(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file to text asynchronously.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None if transcription fails
        """
        if not self.model:
            raise RuntimeError("Whisper model not loaded")
        
        if not os.path.exists(audio_file_path):
            return None
        
        # Run transcription in executor to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                self.model.transcribe,
                audio_file_path
            )
            text = result.get("text", "").strip()
            return text if text else None
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None


# Global instance (will be initialized in main.py)
whisper_stt: Optional[WhisperSTT] = None


def initialize_whisper(model_name: str = "base") -> WhisperSTT:
    """Initialize global Whisper instance."""
    global whisper_stt
    whisper_stt = WhisperSTT(model_name)
    return whisper_stt


def get_whisper() -> Optional[WhisperSTT]:
    """Get global Whisper instance."""
    return whisper_stt

