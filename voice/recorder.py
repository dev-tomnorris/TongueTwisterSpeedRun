"""Audio recording from Discord voice channels.

Note: Since discord.py doesn't provide direct audio receiving in this version,
we use PyAudio to record from the system's default microphone as a workaround.
This records whatever audio is coming through the user's microphone.
"""

import discord
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime
import wave
import struct
import config


class AudioRecorder:
    """Records audio from Discord voice channels using system microphone."""
    
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client = voice_client
        self.recording = False
        self.target_user_id = None
        self.recorded_file = None
    
    async def record_user_audio(
        self,
        user_id: int,
        timeout: float = None
    ) -> Optional[str]:
        """
        Record audio from a user for a specified duration.
        
        Uses system microphone as a workaround since discord.py doesn't
        provide direct audio receiving in this version.
        
        Args:
            user_id: Discord user ID to record (for logging)
            timeout: Maximum recording time in seconds
            
        Returns:
            Path to audio file or None
        """
        if timeout is None:
            timeout = config.VOICE_RECORDING_TIMEOUT
        
        if self.recording:
            return None
        
        print(f"[INFO] Starting audio recording for user {user_id} (timeout: {timeout}s)")
        print("[INFO] Recording from system microphone (discord.py audio receiving not available)")
        
        self.target_user_id = user_id
        self.recording = True
        
        # Prepare output file
        data_dir = Path("data/audio")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{user_id}_{timestamp}.wav"
        filepath = data_dir / filename
        
        try:
            # Record from system microphone using PyAudio
            await self._record_from_microphone(filepath, timeout)
            
            absolute_path = filepath.resolve()
            self.recorded_file = str(absolute_path)
            self.recording = False
            
            if absolute_path.exists():
                file_size = absolute_path.stat().st_size
                print(f"[INFO] Recording saved to {absolute_path} ({file_size} bytes)")
                return self.recorded_file
            else:
                print(f"[ERROR] File was not created: {absolute_path}")
                return None
                
        except ImportError:
            print("[ERROR] PyAudio not installed. Install with: pip install pyaudio")
            print("[INFO] Falling back to placeholder audio")
            self._create_placeholder_wav(filepath, timeout)
            absolute_path = filepath.resolve()
            self.recorded_file = str(absolute_path)
            self.recording = False
            return self.recorded_file
        except Exception as e:
            print(f"[ERROR] Error recording audio: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to placeholder
            self._create_placeholder_wav(filepath, timeout)
            absolute_path = filepath.resolve()
            self.recorded_file = str(absolute_path)
            self.recording = False
            return self.recorded_file
    
    async def _record_from_microphone(self, filepath: Path, duration: float):
        """Record audio from system microphone using PyAudio."""
        import pyaudio
        import numpy as np
        
        # Audio parameters
        chunk = 1024
        sample_format = pyaudio.paInt16
        sample_rate = 48000
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        try:
            # List all available input devices for debugging
            print(f"[DEBUG] Available input devices:")
            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        is_default = (i == p.get_default_input_device_info()['index'])
                        default_marker = " (DEFAULT)" if is_default else ""
                        print(f"[DEBUG]   Device {i}: {info['name']} - {info['maxInputChannels']} channels{default_marker}")
                except:
                    pass
            
            # Get default input device info to determine supported channels
            try:
                default_device = p.get_default_input_device_info()
                max_channels = int(default_device['maxInputChannels'])
                device_name = default_device['name']
                device_index = default_device['index']
                print(f"[INFO] Using microphone: {device_name} (Device {device_index}, {max_channels} channels)")
                
                # Use mono (1 channel) if available, fallback to what's supported
                channels = 1 if max_channels >= 1 else max_channels
            except Exception as e:
                print(f"[WARNING] Could not get device info: {e}, using mono")
                channels = 1
                device_index = None
            
            # Try to open audio stream with detected channels
            try:
                stream_kwargs = {
                    'format': sample_format,
                    'channels': channels,
                    'rate': sample_rate,
                    'frames_per_buffer': chunk,
                    'input': True
                }
                if device_index is not None:
                    stream_kwargs['input_device_index'] = device_index
                
                stream = p.open(**stream_kwargs)
            except OSError as e:
                # If stereo fails, try mono
                if channels == 2:
                    print(f"[WARNING] Stereo not supported, trying mono...")
                    channels = 1
                    stream_kwargs['channels'] = channels
                    stream = p.open(**stream_kwargs)
                else:
                    raise
            
            print(f"[INFO] Recording from microphone for up to {duration} seconds...")
            print(f"[INFO] Please speak now! Recording will stop automatically when you finish.")
            
            # Record audio with real-time level monitoring and silence detection
            frames = []
            num_chunks = int(sample_rate / chunk * duration)
            max_level_seen = 0.0
            chunks_with_audio = 0
            
            # Silence detection
            silence_chunks = 0
            chunks_per_second = sample_rate // chunk
            silence_threshold_chunks = int(config.VOICE_SILENCE_THRESHOLD * chunks_per_second)
            min_recording_chunks = int(config.VOICE_MIN_RECORDING_TIME * chunks_per_second)
            has_detected_speech = False
            
            for i in range(num_chunks):
                if not self.recording:
                    break
                    
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
                
                # Check audio level in real-time
                audio_data = np.frombuffer(data, dtype=np.int16)
                max_level = np.abs(audio_data).max() / 32768.0
                max_level_seen = max(max_level_seen, max_level)
                
                # Determine if this chunk has audio
                is_silent = max_level < config.VOICE_SILENCE_LEVEL
                
                if not is_silent:
                    chunks_with_audio += 1
                    has_detected_speech = True
                    silence_chunks = 0  # Reset silence counter
                else:
                    silence_chunks += 1
                
                # Check if we should stop early due to silence
                # Only stop if:
                # 1. We've recorded at least the minimum time (to avoid stopping before user speaks)
                # 2. We've detected speech at some point (user has spoken)
                # 3. We've had silence for the threshold duration
                if (i >= min_recording_chunks and 
                    has_detected_speech and 
                    silence_chunks >= silence_threshold_chunks):
                    seconds_recorded = (i + 1) * chunk / sample_rate
                    print(f"[INFO] Silence detected for {config.VOICE_SILENCE_THRESHOLD}s, stopping recording early at {seconds_recorded:.1f}s")
                    break
                
                # Print progress every second
                if (i + 1) % chunks_per_second == 0:
                    seconds_recorded = (i + 1) * chunk / sample_rate
                    print(f"[INFO] Recording... {seconds_recorded:.1f}s (max level: {max_level_seen:.4f})")
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            
            # Analyze final audio levels
            if frames:
                all_audio = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
                final_max = np.abs(all_audio).max()
                final_rms = np.sqrt(np.mean(all_audio**2))
                audio_percentage = (chunks_with_audio / len(frames)) * 100
                
                print(f"[INFO] Recording complete - Max level: {final_max:.4f}, RMS: {final_rms:.4f}")
                print(f"[INFO] Audio detected in {audio_percentage:.1f}% of chunks")
                
                if final_max < 0.01:
                    print(f"[WARNING] ⚠️  Very quiet recording detected! Max amplitude: {final_max:.6f}")
                    print(f"[WARNING] This might mean:")
                    print(f"[WARNING]   1. Your microphone is muted or not working")
                    print(f"[WARNING]   2. You're using a different microphone than Discord")
                    print(f"[WARNING]   3. Your microphone volume is too low")
                    print(f"[WARNING]   4. Discord is using a different audio input device")
            
            # Save to WAV file
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
            
            print(f"[INFO] Recorded {len(frames)} chunks ({len(frames) * chunk / sample_rate:.2f}s)")
            
        finally:
            p.terminate()
    
    def _create_placeholder_wav(self, filepath: Path, duration: float):
        """Create a placeholder WAV file."""
        sample_rate = 48000
        channels = 2
        sample_width = 2  # 16-bit
        
        # Generate silence
        num_samples = int(sample_rate * duration * channels)
        silence = struct.pack(f'<{num_samples}h', *([0] * num_samples))
        
        with wave.open(str(filepath), 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence)
