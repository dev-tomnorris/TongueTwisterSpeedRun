"""Audio recording from Discord voice channels.

Uses discord-ext-voice-recv to receive audio directly from Discord voice channels.
This allows recording any user's voice in the channel, not just the local microphone.
"""

import discord
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime
import wave
import numpy as np
import time
import config

# Try to import voice receiving extension
try:
    from discord.ext import voice_recv
    VOICE_RECV_AVAILABLE = True
except ImportError:
    VOICE_RECV_AVAILABLE = False
    print("[WARNING] discord-ext-voice-recv not installed. Install with: pip install discord-ext-voice-recv")
    print("[WARNING] Falling back to system microphone recording.")


class AudioRecorder:
    """Records audio from Discord voice channels."""
    
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client = voice_client
        self.recording = False
        self.target_user_id = None
        self.recorded_file = None
        self.audio_buffer = []
        self.sink = None
    
    async def record_user_audio(
        self,
        user_id: int,
        timeout: float = None
    ) -> Optional[str]:
        """
        Record audio from a user in Discord voice channel.
        
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
        
        print(f"[INFO] Starting audio recording for user {user_id} (timeout: {timeout}s)")
        
        # Check if voice_recv is available and voice client supports it
        if VOICE_RECV_AVAILABLE:
            # Check if this is a VoiceRecvClient
            is_voice_recv_client = isinstance(self.voice_client, voice_recv.VoiceRecvClient)
            has_listen = hasattr(self.voice_client, 'listen')
            
            print(f"[DEBUG] VoiceRecv available: True")
            print(f"[DEBUG] Voice client type: {type(self.voice_client).__name__}")
            print(f"[DEBUG] Is VoiceRecvClient: {is_voice_recv_client}")
            print(f"[DEBUG] Has listen method: {has_listen}")
            
            if is_voice_recv_client and has_listen:
                try:
                    return await self._record_from_discord(user_id, timeout)
                except Exception as e:
                    print(f"[WARNING] Discord audio receiving failed: {e}")
                    import traceback
                    traceback.print_exc()
                    print("[INFO] Falling back to system microphone...")
            else:
                print(f"[WARNING] Voice client is not a VoiceRecvClient or lacks 'listen' method.")
                print(f"[WARNING] is_voice_recv_client={is_voice_recv_client}, has_listen={has_listen}")
                print("[WARNING] Reconnect to voice channel to enable Discord audio receiving.")
        else:
            print("[WARNING] discord-ext-voice-recv not available")
        
        # Fallback to system microphone
        return await self._record_from_microphone_fallback(user_id, timeout)
    
    async def _record_from_discord(self, user_id: int, timeout: float) -> Optional[str]:
        """Record audio directly from Discord voice channel."""
        print(f"[INFO] Recording from Discord voice channel for user {user_id}")
        
        self.target_user_id = user_id
        self.recording = True
        self.audio_buffer = []
        self.pre_buffer = []  # Buffer audio before speech is detected
        self.speech_detected = False  # Track if we've detected speech yet
        last_audio_time = [None]  # Use list to allow modification in nested function
        
        # Prepare output file
        data_dir = Path("data/audio")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{user_id}_{timestamp}.wav"
        filepath = data_dir / filename
        
        # Check if voice_client is a VoiceRecvClient
        if not isinstance(self.voice_client, voice_recv.VoiceRecvClient):
            raise TypeError(f"VoiceClient is not a VoiceRecvClient (got {type(self.voice_client).__name__})")
        
        # Create a custom sink that filters by user
        # Use AudioSink as the base class (not MultiAudioSink which requires destinations)
        class UserAudioSink(voice_recv.AudioSink):
            def __init__(self, target_user_id, audio_buffer, pre_buffer, speech_detected_ref, last_audio_time_ref):
                super().__init__()
                self.target_user_id = target_user_id
                self.audio_buffer = audio_buffer
                self.pre_buffer = pre_buffer
                self.speech_detected_ref = speech_detected_ref
                self.last_audio_time_ref = last_audio_time_ref
                self._write_call_count = 0  # Track all write() calls for debugging
                self._speech_chunks_count = 0  # Count consecutive chunks with speech
                print(f"[DEBUG] UserAudioSink initialized for user {target_user_id}")
            
            def wants_opus(self):
                return False  # We want PCM audio
            
            def write(self, user, data: voice_recv.VoiceData):
                """Called when audio is received from a user."""
                try:
                    # Log ALL audio received for debugging
                    if user:
                        user_id_received = user.id
                        user_name = getattr(user, 'display_name', getattr(user, 'name', 'Unknown'))
                    else:
                        user_id_received = None
                        user_name = "None"
                    
                    # ALWAYS log the first few calls to verify sink is receiving ANY audio
                    # This is critical for debugging - if we never see this, Discord isn't sending audio
                    total_calls = getattr(self, '_write_call_count', 0)
                    self._write_call_count = total_calls + 1
                    
                    if total_calls < 5:  # Log first 5 calls regardless of user
                        print(f"[DEBUG] write() called #{total_calls + 1}: user={user_name} (ID: {user_id_received}), target={self.target_user_id}, match={user and user.id == self.target_user_id if user else False}")
                    
                    if user and user.id == self.target_user_id:
                        # Get PCM data from VoiceData
                        if hasattr(data, 'pcm') and data.pcm:
                            pcm_data = data.pcm
                            # Convert PCM bytes to numpy array
                            audio_array = np.frombuffer(pcm_data, dtype=np.int16)
                            
                            # Voice Activity Detection (VAD) - check if this chunk has speech
                            audio_level = np.abs(audio_array).max() / 32768.0  # Normalize to 0-1
                            has_speech = audio_level >= config.VOICE_ACTIVITY_THRESHOLD
                            
                            # Require multiple consecutive chunks with speech before starting recording
                            # This prevents false positives from brief noise or background sounds
                            if has_speech:
                                self._speech_chunks_count += 1
                            else:
                                self._speech_chunks_count = 0  # Reset if we hit silence
                            
                            # Update speech detection status (only after confirmation)
                            if (self._speech_chunks_count >= config.VOICE_VAD_CONFIRMATION_CHUNKS and 
                                not self.speech_detected_ref[0]):
                                self.speech_detected_ref[0] = True
                                print(f"[INFO] Speech confirmed! Starting recording...")
                                # Move pre-buffer to main buffer (keep only last few chunks before confirmed speech)
                                keep_chunks = min(len(self.pre_buffer), config.VOICE_PREBUFFER_SIZE)
                                if keep_chunks > 0:
                                    self.audio_buffer.extend(self.pre_buffer[-keep_chunks:])
                                    print(f"[DEBUG] Added {keep_chunks} pre-buffered chunks to capture speech start")
                            
                            # Add to appropriate buffer
                            if self.speech_detected_ref[0]:
                                # Speech detected - add to main buffer
                                self.audio_buffer.append(audio_array)
                                self.last_audio_time_ref[0] = time.time()
                                # Print first few chunks and then every 50 to reduce noise
                                chunk_duration = len(audio_array) / 48000  # seconds
                                if len(self.audio_buffer) <= 5 or len(self.audio_buffer) % 50 == 0:
                                    print(f"[DEBUG] ✓ Received chunk #{len(self.audio_buffer)} from {user_name}: {chunk_duration:.3f}s, total: {len(self.audio_buffer)} chunks")
                            else:
                                # No speech yet - add to pre-buffer (limited size)
                                self.pre_buffer.append(audio_array)
                                if len(self.pre_buffer) > config.VOICE_PREBUFFER_SIZE * 2:
                                    # Keep only recent chunks
                                    self.pre_buffer = self.pre_buffer[-config.VOICE_PREBUFFER_SIZE:]
                        else:
                            print(f"[WARNING] VoiceData from {user_name} has no pcm attribute or pcm is None/empty")
                            if hasattr(data, 'pcm'):
                                print(f"[DEBUG] data.pcm exists but is: {data.pcm}")
                            else:
                                print(f"[DEBUG] data.pcm attribute does not exist. Data attributes: {[a for a in dir(data) if not a.startswith('_')]}")
                    elif user:
                        # Log audio from other users (only first time to reduce noise)
                        if len(self.audio_buffer) == 0:
                            print(f"[DEBUG] ✗ Received audio from {user_name} (ID: {user_id_received}), but target is {self.target_user_id} - IGNORING")
                    else:
                        # No user info - this shouldn't happen but log it
                        if len(self.audio_buffer) < 5:
                            print(f"[WARNING] write() called with user=None")
                except Exception as e:
                    print(f"[ERROR] Exception in sink.write(): {e}")
                    import traceback
                    traceback.print_exc()
            
            def cleanup(self):
                """Called when the sink is being cleaned up."""
                pass
        
        speech_detected = [False]  # Use list to allow modification in nested function
        sink = UserAudioSink(user_id, self.audio_buffer, self.pre_buffer, speech_detected, last_audio_time)
        
        # Use the listen() method - this is the correct way to start receiving audio
        # It doesn't require audio to be flowing first
        print(f"[INFO] Starting to listen for audio from user {user_id}...")
        print(f"[DEBUG] Voice client type: {type(self.voice_client).__name__}")
        print(f"[DEBUG] Voice client is_listening before: {self.voice_client.is_listening()}")
        
        # Stop any existing listener first (in case one is already active)
        try:
            if self.voice_client.is_listening():
                print(f"[DEBUG] Stopping existing listener...")
                self.voice_client.stop_listening()
                await asyncio.sleep(0.1)  # Small delay to ensure cleanup
        except Exception as e:
            print(f"[WARNING] Error stopping existing listener: {e}")
        
        try:
            self.voice_client.listen(sink)
            print(f"[DEBUG] Started listening with UserAudioSink")
            print(f"[DEBUG] Voice client is_listening after: {self.voice_client.is_listening()}")
            
            # Verify sink is actually registered
            if hasattr(self.voice_client, 'sink'):
                print(f"[DEBUG] Voice client sink: {type(self.voice_client.sink).__name__ if self.voice_client.sink else 'None'}")
        except Exception as e:
            print(f"[ERROR] Failed to start listening: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Small delay to allow Discord to start sending audio packets
        await asyncio.sleep(0.3)
        
        print(f"[INFO] Listening... I'll start recording when you speak!")
        print(f"[INFO] Make sure you're speaking in the voice channel and not muted!")
        print(f"[DEBUG] If you don't see 'write() called' messages, Discord isn't sending audio to the bot")
        
        # Wait for recording with silence detection
        # Use time.time() for consistency with the sink's time tracking
        start_time = time.time()
        silence_threshold = config.VOICE_SILENCE_THRESHOLD
        min_recording_time = config.VOICE_MIN_RECORDING_TIME
        
        while (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
            
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Check if we have recent audio (only after speech is detected)
            if speech_detected[0] and last_audio_time[0] is not None:
                time_since_audio = current_time - last_audio_time[0]
                has_detected_speech = len(self.audio_buffer) > 0
                
                # Check for silence-based early stop
                if (elapsed >= min_recording_time and 
                    has_detected_speech and 
                    time_since_audio >= silence_threshold):
                    print(f"[INFO] Silence detected, stopping recording early at {elapsed:.1f}s")
                    break
            elif not speech_detected[0]:
                # Still waiting for speech - show waiting message
                if int(elapsed) != int(elapsed - 0.1) and int(elapsed) > 0:  # Every second
                    print(f"[INFO] Waiting for speech... {elapsed:.1f}s")
            
            # Progress updates (only after speech is detected)
            if speech_detected[0] and int(elapsed) != int(elapsed - 0.1) and int(elapsed) > 0:  # Every second
                buffer_info = f", {len(self.audio_buffer)} chunks" if self.audio_buffer else ""
                print(f"[INFO] Recording... {elapsed:.1f}s{buffer_info}")
        
        # Stop recording - stop listening
        try:
            if self.voice_client.is_listening():
                self.voice_client.stop_listening()
                print(f"[DEBUG] Stopped listening")
            sink.cleanup()
        except Exception as e:
            print(f"[WARNING] Error stopping listening: {e}")
        
        # Process and save audio
        if len(self.audio_buffer) == 0:
            if not speech_detected[0]:
                print("[WARNING] No speech detected during recording period")
                print("[DEBUG] The bot was listening but didn't detect any speech above the threshold")
            else:
                print("[WARNING] No audio received from Discord voice channel")
                print("[DEBUG] Possible reasons:")
                print("[DEBUG]   1. User is not speaking (check if user is unmuted)")
                print("[DEBUG]   2. Discord is not sending audio (check Discord voice settings)")
                print("[DEBUG]   3. User is in a different voice channel")
                print("[DEBUG]   4. Bot doesn't have proper permissions")
            self.recording = False
            return None
        
        # Combine all audio chunks
        audio_data = np.concatenate(self.audio_buffer)
        
        # Normalize audio to prevent clipping and improve quality
        # Discord audio can sometimes be at max volume, causing clipping
        max_val = np.abs(audio_data).max()
        if max_val > 0:
            # Normalize to 90% of max to prevent clipping
            # This helps preserve audio quality for transcription
            audio_data = audio_data.astype(np.float32) / max_val * 0.9
            # Convert back to int16 for WAV file
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Save to WAV file
        sample_rate = 48000  # Discord's sample rate
        channels = 1  # Mono
        
        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        absolute_path = filepath.resolve()
        self.recorded_file = str(absolute_path)
        self.recording = False
        
        file_size = absolute_path.stat().st_size
        duration = len(audio_data) / sample_rate
        print(f"[INFO] Recording saved to {absolute_path} ({file_size} bytes, {duration:.2f}s)")
        
        return self.recorded_file
    
    async def _record_from_microphone_fallback(self, user_id: int, timeout: float) -> Optional[str]:
        """Fallback: Record from system microphone using PyAudio."""
        print("[WARNING] Using system microphone fallback")
        print("[WARNING] This will record from THIS computer's microphone, not Discord voice channel")
        
        self.target_user_id = user_id
        self.recording = True
        
        # Prepare output file
        data_dir = Path("data/audio")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{user_id}_{timestamp}.wav"
        filepath = data_dir / filename
        
        try:
            import pyaudio
            
            # Audio parameters
            chunk = 1024
            sample_format = pyaudio.paInt16
            sample_rate = 48000
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            try:
                # Get default input device
                try:
                    default_device = p.get_default_input_device_info()
                    max_channels = int(default_device['maxInputChannels'])
                    device_name = default_device['name']
                    device_index = default_device['index']
                    print(f"[INFO] Using microphone: {device_name} (Device {device_index}, {max_channels} channels)")
                    channels = 1 if max_channels >= 1 else max_channels
                except Exception as e:
                    print(f"[WARNING] Could not get device info: {e}, using mono")
                    channels = 1
                    device_index = None
                
                # Open audio stream
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
                
                print(f"[INFO] Recording from microphone for up to {timeout} seconds...")
                print(f"[INFO] Please speak now! Recording will stop automatically when you finish.")
                
                # Record audio with silence detection
                frames = []
                num_chunks = int(sample_rate / chunk * timeout)
                chunks_per_second = sample_rate // chunk
                silence_threshold_chunks = int(config.VOICE_SILENCE_THRESHOLD * chunks_per_second)
                min_recording_chunks = int(config.VOICE_MIN_RECORDING_TIME * chunks_per_second)
                silence_chunks = 0
                has_detected_speech = False
                max_level_seen = 0.0
                
                for i in range(num_chunks):
                    if not self.recording:
                        break
                    
                    data = stream.read(chunk, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Check audio level
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    max_level = np.abs(audio_data).max() / 32768.0
                    max_level_seen = max(max_level_seen, max_level)
                    
                    is_silent = max_level < config.VOICE_SILENCE_LEVEL
                    
                    if not is_silent:
                        has_detected_speech = True
                        silence_chunks = 0
                    else:
                        silence_chunks += 1
                    
                    # Early stop on silence
                    if (i >= min_recording_chunks and 
                        has_detected_speech and 
                        silence_chunks >= silence_threshold_chunks):
                        seconds_recorded = (i + 1) * chunk / sample_rate
                        print(f"[INFO] Silence detected, stopping recording early at {seconds_recorded:.1f}s")
                        break
                    
                    # Progress updates
                    if (i + 1) % chunks_per_second == 0:
                        seconds_recorded = (i + 1) * chunk / sample_rate
                        print(f"[INFO] Recording... {seconds_recorded:.1f}s (max level: {max_level_seen:.4f})")
                
                stream.stop_stream()
                stream.close()
                
                # Save to WAV file
                with wave.open(str(filepath), 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(p.get_sample_size(sample_format))
                    wf.setframerate(sample_rate)
                    wf.writeframes(b''.join(frames))
                
                print(f"[INFO] Recording complete - Max level: {max_level_seen:.4f}")
                
            finally:
                p.terminate()
            
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
            self.recording = False
            return None
        except Exception as e:
            print(f"[ERROR] Error recording audio: {e}")
            import traceback
            traceback.print_exc()
            self.recording = False
            return None
