"""Speech-to-text using OpenAI Whisper."""

import whisper
import asyncio
import os
import shutil
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
        
        # Convert to absolute path and normalize
        audio_path = Path(audio_file_path)
        if not audio_path.is_absolute():
            audio_path = audio_path.resolve()
        
        # Normalize the path (handle Windows path issues)
        audio_file_path = str(audio_path.absolute())
        
        # Verify file exists and is readable
        if not audio_path.exists():
            print(f"[ERROR] Audio file not found: {audio_file_path}")
            print(f"[DEBUG] Current working directory: {os.getcwd()}")
            return None
        
        if not audio_path.is_file():
            print(f"[ERROR] Path is not a file: {audio_file_path}")
            return None
        
        # Check file size (should not be empty)
        file_size = audio_path.stat().st_size
        if file_size == 0:
            print(f"[ERROR] Audio file is empty: {audio_file_path}")
            return None
        
        print(f"[DEBUG] Transcribing file: {audio_file_path} (size: {file_size} bytes)")
        
        # Get absolute path
        abs_path = audio_path.resolve()
        
        # On Windows, use C:\temp\ which has NO SPACES and is guaranteed to work
        # This is the ONLY reliable way to avoid path issues with Whisper/ffmpeg
        if os.name == 'nt':
            # Use C:\temp\ which has no spaces
            temp_dir = Path("C:/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            # On Unix, use project temp directory
            temp_dir = Path("data/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_filename = f"whisper_{os.getpid()}_{abs_path.name}"
        temp_path = temp_dir / temp_filename
        
        try:
            # Copy file to temp directory (not symlink - more reliable)
            shutil.copy2(abs_path, temp_path)
            
            # Ensure file is fully written and flushed
            temp_path_abs = temp_path.resolve()
            file_path_for_whisper = str(temp_path_abs)
            
            # Verify the copy succeeded
            if not temp_path_abs.exists():
                raise FileNotFoundError(f"File copy failed - destination doesn't exist: {temp_path_abs}")
            
            # Get file size to verify it's complete
            copied_size = temp_path_abs.stat().st_size
            if copied_size != file_size:
                raise ValueError(f"File copy incomplete: source={file_size}, dest={copied_size}")
            
            print(f"[DEBUG] Copied file to temp location (no spaces): {file_path_for_whisper}")
            print(f"[DEBUG] Copied file size: {copied_size} bytes (matches source: {copied_size == file_size})")
        except Exception as e:
            print(f"[ERROR] Could not copy file to temp directory: {e}")
            # Fallback to original path
            file_path_for_whisper = str(abs_path)
            temp_path = None
        
        print(f"[DEBUG] Final file path for Whisper: {file_path_for_whisper}")
        
        # Verify we can actually open the file before passing to Whisper
        try:
            test_path = Path(file_path_for_whisper)
            with open(test_path, 'rb') as test_file:
                test_file.read(1)  # Read one byte to verify access
            print(f"[DEBUG] File is readable")
        except Exception as e:
            print(f"[ERROR] Cannot read file: {e}")
            return None
        
        # Run transcription in executor to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            def transcribe_file():
                # Use the file path from outer scope
                path_to_use = file_path_for_whisper
                
                # Double-check file exists in executor thread with detailed logging
                print(f"[DEBUG] Executor thread checking file: {path_to_use}")
                print(f"[DEBUG] Executor thread file exists check: {os.path.exists(path_to_use)}")
                print(f"[DEBUG] Executor thread current dir: {os.getcwd()}")
                
                if not os.path.exists(path_to_use):
                    # Try with absolute path
                    abs_check = Path(path_to_use).resolve()
                    print(f"[DEBUG] Executor thread trying absolute path: {abs_check}")
                    print(f"[DEBUG] Executor thread absolute exists: {abs_check.exists()}")
                    if not abs_check.exists():
                        raise FileNotFoundError(f"File not found in executor: {path_to_use} (absolute: {abs_check})")
                    path_to_use = str(abs_check)
                
                # Verify file is accessible (but don't keep it open)
                print(f"[DEBUG] Executor thread verifying file access...")
                try:
                    # Open and immediately close to verify access without locking
                    with open(path_to_use, 'rb') as f:
                        f.read(1)  # Read one byte to verify
                    print(f"[DEBUG] Executor thread file verified and closed")
                except Exception as e:
                    print(f"[ERROR] Executor thread cannot access file: {e}")
                    raise
                
                # Small delay to ensure file handle is fully released
                import time
                time.sleep(0.1)
                
                # Pass the path to Whisper - use absolute path with backslashes (Windows native)
                # Don't use forward slashes - Whisper on Windows expects native path format
                abs_path_final = Path(path_to_use).resolve()
                whisper_path = str(abs_path_final)
                print(f"[DEBUG] Executor thread calling Whisper with path: {whisper_path}")
                print(f"[DEBUG] Executor thread path type check: {type(whisper_path)}")
                
                # Double-check file still exists right before calling Whisper
                if not abs_path_final.exists():
                    raise FileNotFoundError(f"File disappeared before Whisper call: {abs_path_final}")
                
                # Verify file is still accessible
                try:
                    with open(abs_path_final, 'rb') as test:
                        test.read(1)
                    print(f"[DEBUG] File verified accessible right before Whisper call")
                except Exception as e:
                    raise FileNotFoundError(f"File not accessible right before Whisper: {e}")
                
                # Call Whisper - read WAV file directly using Python libraries to avoid ffmpeg path issues
                # whisper.load_audio() also uses ffmpeg, so we'll read the file ourselves
                print(f"[DEBUG] Reading WAV file directly to avoid ffmpeg path issues...")
                
                # Read WAV file using wave library (no ffmpeg needed)
                import wave
                import numpy as np
                from scipy import signal
                
                with wave.open(whisper_path, 'rb') as wav_file:
                    # Get audio parameters
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    
                    # Read all frames
                    audio_bytes = wav_file.readframes(frames)
                    
                    # Convert to numpy array
                    if sample_width == 1:
                        dtype = np.uint8
                        audio_array = np.frombuffer(audio_bytes, dtype=dtype).astype(np.float32) / 128.0 - 1.0
                    elif sample_width == 2:
                        dtype = np.int16
                        audio_array = np.frombuffer(audio_bytes, dtype=dtype).astype(np.float32) / 32768.0
                    elif sample_width == 4:
                        dtype = np.int32
                        audio_array = np.frombuffer(audio_bytes, dtype=dtype).astype(np.float32) / 2147483648.0
                    else:
                        raise ValueError(f"Unsupported sample width: {sample_width}")
                    
                    # Handle stereo to mono conversion if needed
                    if channels == 2:
                        audio_array = audio_array.reshape(-1, 2).mean(axis=1)
                    elif channels > 2:
                        audio_array = audio_array.reshape(-1, channels).mean(axis=1)
                
                print(f"[DEBUG] Audio loaded, shape: {audio_array.shape}, sample_rate: {sample_rate}")
                
                # Check audio level (to detect if it's silent)
                max_amplitude = np.abs(audio_array).max()
                rms = np.sqrt(np.mean(audio_array**2))
                print(f"[DEBUG] Audio stats - Max amplitude: {max_amplitude:.4f}, RMS: {rms:.4f}")
                
                if max_amplitude < 0.01:
                    print(f"[WARNING] Audio appears to be very quiet or silent (max amplitude: {max_amplitude})")
                
                # Whisper expects audio at 16kHz, so resample if necessary
                target_sample_rate = 16000
                if sample_rate != target_sample_rate:
                    num_samples = int(len(audio_array) * target_sample_rate / sample_rate)
                    audio_array = signal.resample(audio_array, num_samples)
                    print(f"[DEBUG] Resampled from {sample_rate}Hz to {target_sample_rate}Hz, new shape: {audio_array.shape}")
                else:
                    print(f"[DEBUG] Audio already at {target_sample_rate}Hz, no resampling needed")
                
                print(f"[DEBUG] Calling Whisper transcribe with audio array...")
                result = self.model.transcribe(audio_array)
                print(f"[DEBUG] Whisper transcription completed")
                print(f"[DEBUG] Whisper result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
                if isinstance(result, dict):
                    print(f"[DEBUG] Whisper result text: '{result.get('text', 'NO TEXT KEY')}'")
                    print(f"[DEBUG] Whisper result language: {result.get('language', 'NO LANGUAGE KEY')}")
                return result
            
            result = await loop.run_in_executor(None, transcribe_file)
            text = result.get("text", "").strip()
            print(f"[DEBUG] Transcription result: {text[:50]}..." if len(text) > 50 else f"[DEBUG] Transcription result: {text}")
            return text if text else None
        except FileNotFoundError as e:
            print(f"[ERROR] File not found during transcription: {file_path_for_whisper}")
            print(f"[ERROR] Error details: {e}")
            print(f"[ERROR] Current working directory in executor: {os.getcwd()}")
            return None
        except Exception as e:
            print(f"[ERROR] Error transcribing audio: {e}")
            print(f"[ERROR] File path was: {file_path_for_whisper}")
            print(f"[ERROR] File exists: {os.path.exists(file_path_for_whisper)}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Clean up copied file if we created one
            # IMPORTANT: Only clean up AFTER transcription completes successfully
            # Don't delete during transcription as Whisper/ffmpeg might still need it
            if temp_path:
                try:
                    # Small delay to ensure Whisper/ffmpeg has fully released the file
                    await asyncio.sleep(0.5)
                    temp_path_abs = temp_path.resolve()
                    if temp_path_abs.exists():
                        temp_path_abs.unlink()
                        print(f"[DEBUG] Cleaned up temp file: {temp_path_abs}")
                    else:
                        print(f"[DEBUG] Temp file already gone: {temp_path_abs}")
                except Exception as e:
                    print(f"[WARNING] Could not delete temp file {temp_path}: {e}")


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

