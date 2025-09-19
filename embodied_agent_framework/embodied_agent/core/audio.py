"""
Audio Processing Module - Handles audio input/output, speech recognition, and TTS
"""

import asyncio
import pyaudio
import wave
import numpy as np
import time
import threading
from typing import Dict, Any, Optional, Callable
from loguru import logger
from pydantic import BaseModel
import os

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    logger.warning("sounddevice not available, using fallback audio detection")
    SOUNDDEVICE_AVAILABLE = False


class AudioConfig(BaseModel):
    """Audio configuration parameters"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: int = pyaudio.paInt16
    input_device_index: Optional[int] = None
    output_device_index: Optional[int] = None


class AudioProcessor:
    """
    Audio processor for recording, playback, and real-time audio processing
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize audio processor

        Args:
            config: Audio processing configuration
        """
        self.config = config

        # Audio configuration
        self.audio_config = AudioConfig(**config.get('audio', {}))

        # Recording settings
        self.recording_duration = config.get('recording_duration', 5)  # seconds
        self.voice_activation_threshold = config.get('voice_activation_threshold', 0.01)
        self.silence_duration = config.get('silence_duration', 2.0)  # seconds

        # File settings
        self.save_directory = config.get('save_directory', 'temp')
        self.audio_format = config.get('audio_format', 'wav')

        # PyAudio instance
        self._audio: Optional[pyaudio.PyAudio] = None
        self._recording_stream: Optional[pyaudio.Stream] = None
        self._playback_stream: Optional[pyaudio.Stream] = None

        # Recording state
        self._is_recording = False
        self._is_voice_activated = False
        self._recorded_frames = []
        self._recording_thread: Optional[threading.Thread] = None

        # Voice activation detection
        self._voice_detected_time: Optional[float] = None
        self._silence_start_time: Optional[float] = None

    async def initialize(self) -> bool:
        """
        Initialize audio processor

        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize PyAudio
            self._audio = pyaudio.PyAudio()

            # List available audio devices
            self._list_audio_devices()

            # Test audio devices
            if not self._test_audio_devices():
                logger.warning("Audio device test failed, continuing with defaults")

            # Ensure save directory exists
            os.makedirs(self.save_directory, exist_ok=True)

            logger.info("Audio processor initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing audio processor: {e}")
            return False

    async def shutdown(self) -> bool:
        """
        Shutdown audio processor

        Returns:
            bool: True if shutdown successful
        """
        try:
            # Stop any ongoing recording
            await self.stop_recording()

            # Close streams
            if self._recording_stream:
                self._recording_stream.close()
                self._recording_stream = None

            if self._playback_stream:
                self._playback_stream.close()
                self._playback_stream = None

            # Terminate PyAudio
            if self._audio:
                self._audio.terminate()
                self._audio = None

            logger.info("Audio processor shutdown complete")
            return True

        except Exception as e:
            logger.error(f"Error during audio processor shutdown: {e}")
            return False

    def _list_audio_devices(self):
        """List available audio devices"""
        if not self._audio:
            return

        logger.info("Available audio devices:")
        for i in range(self._audio.get_device_count()):
            device_info = self._audio.get_device_info_by_index(i)
            logger.info(f"  Device {i}: {device_info['name']} "
                       f"(inputs: {device_info['maxInputChannels']}, "
                       f"outputs: {device_info['maxOutputChannels']})")

    def _test_audio_devices(self) -> bool:
        """
        Test audio input and output devices

        Returns:
            bool: True if devices are working
        """
        try:
            if not self._audio:
                return False

            # Test input device
            if self.audio_config.input_device_index is not None:
                device_info = self._audio.get_device_info_by_index(self.audio_config.input_device_index)
                if device_info['maxInputChannels'] == 0:
                    logger.error(f"Input device {self.audio_config.input_device_index} has no input channels")
                    return False

            # Test output device
            if self.audio_config.output_device_index is not None:
                device_info = self._audio.get_device_info_by_index(self.audio_config.output_device_index)
                if device_info['maxOutputChannels'] == 0:
                    logger.error(f"Output device {self.audio_config.output_device_index} has no output channels")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error testing audio devices: {e}")
            return False

    async def record_fixed_duration(self, duration: float, save_path: Optional[str] = None) -> Optional[str]:
        """
        Record audio for a fixed duration

        Args:
            duration: Recording duration in seconds
            save_path: Optional path to save the recording

        Returns:
            Optional[str]: Path to saved recording or None if failed
        """
        try:
            if self._is_recording:
                logger.warning("Recording already in progress")
                return None

            logger.info(f"Starting {duration}s recording")

            # Generate save path if not provided
            if save_path is None:
                timestamp = int(time.time())
                save_path = f"{self.save_directory}/record_{timestamp}.{self.audio_format}"

            # Open recording stream
            stream = self._audio.open(
                format=self.audio_config.format,
                channels=self.audio_config.channels,
                rate=self.audio_config.sample_rate,
                input=True,
                input_device_index=self.audio_config.input_device_index,
                frames_per_buffer=self.audio_config.chunk_size
            )

            frames = []
            num_chunks = int(self.audio_config.sample_rate * duration / self.audio_config.chunk_size)

            self._is_recording = True

            for _ in range(num_chunks):
                if not self._is_recording:
                    break

                data = stream.read(self.audio_config.chunk_size)
                frames.append(data)

                # Small delay to prevent blocking
                await asyncio.sleep(0.001)

            # Close stream
            stream.stop_stream()
            stream.close()

            self._is_recording = False

            # Save recording
            if self._save_audio_frames(frames, save_path):
                logger.info(f"Recording saved to {save_path}")
                return save_path
            else:
                logger.error("Failed to save recording")
                return None

        except Exception as e:
            logger.error(f"Error during fixed duration recording: {e}")
            self._is_recording = False
            return None

    async def record_voice_activated(self, max_duration: float = 30.0, save_path: Optional[str] = None) -> Optional[str]:
        """
        Record audio with voice activation (start on voice, stop on silence)

        Args:
            max_duration: Maximum recording duration in seconds
            save_path: Optional path to save the recording

        Returns:
            Optional[str]: Path to saved recording or None if failed
        """
        try:
            if self._is_recording:
                logger.warning("Recording already in progress")
                return None

            logger.info("Starting voice-activated recording (speak to begin)")

            # Generate save path if not provided
            if save_path is None:
                timestamp = int(time.time())
                save_path = f"{self.save_directory}/voice_record_{timestamp}.{self.audio_format}"

            # Reset voice activation state
            self._is_voice_activated = False
            self._voice_detected_time = None
            self._silence_start_time = None
            self._recorded_frames = []

            # Start recording in separate thread
            self._recording_thread = threading.Thread(
                target=self._voice_activated_recording_loop,
                args=(max_duration,)
            )
            self._is_recording = True
            self._recording_thread.start()

            # Wait for recording to complete
            while self._is_recording and self._recording_thread.is_alive():
                await asyncio.sleep(0.1)

            # Wait for thread to finish
            if self._recording_thread:
                self._recording_thread.join()

            # Save recording if we have frames
            if self._recorded_frames:
                if self._save_audio_frames(self._recorded_frames, save_path):
                    logger.info(f"Voice recording saved to {save_path}")
                    return save_path
                else:
                    logger.error("Failed to save voice recording")
                    return None
            else:
                logger.warning("No audio recorded")
                return None

        except Exception as e:
            logger.error(f"Error during voice-activated recording: {e}")
            self._is_recording = False
            return None

    def _voice_activated_recording_loop(self, max_duration: float):
        """
        Voice-activated recording loop (runs in separate thread)

        Args:
            max_duration: Maximum recording duration
        """
        try:
            # Open recording stream
            stream = self._audio.open(
                format=self.audio_config.format,
                channels=self.audio_config.channels,
                rate=self.audio_config.sample_rate,
                input=True,
                input_device_index=self.audio_config.input_device_index,
                frames_per_buffer=self.audio_config.chunk_size
            )

            start_time = time.time()

            while self._is_recording and (time.time() - start_time) < max_duration:
                data = stream.read(self.audio_config.chunk_size)

                # Calculate audio level
                audio_data = np.frombuffer(data, dtype=np.int16)
                audio_level = np.abs(audio_data).mean() / 32768.0  # Normalize to 0-1

                current_time = time.time()

                if audio_level > self.voice_activation_threshold:
                    # Voice detected
                    if not self._is_voice_activated:
                        self._is_voice_activated = True
                        self._voice_detected_time = current_time
                        logger.info("Voice detected, recording started")

                    self._silence_start_time = None
                    self._recorded_frames.append(data)

                else:
                    # Silence detected
                    if self._is_voice_activated:
                        if self._silence_start_time is None:
                            self._silence_start_time = current_time
                        elif (current_time - self._silence_start_time) > self.silence_duration:
                            # Silence duration exceeded, stop recording
                            logger.info("Silence detected, recording stopped")
                            break

                        # Continue recording during short silence
                        self._recorded_frames.append(data)

            # Close stream
            stream.stop_stream()
            stream.close()

        except Exception as e:
            logger.error(f"Error in voice-activated recording loop: {e}")
        finally:
            self._is_recording = False

    async def stop_recording(self) -> bool:
        """
        Stop ongoing recording

        Returns:
            bool: True if stopped successfully
        """
        try:
            if not self._is_recording:
                return True

            self._is_recording = False

            # Wait for recording thread to finish
            if self._recording_thread and self._recording_thread.is_alive():
                self._recording_thread.join(timeout=5.0)

            logger.info("Recording stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False

    async def play_audio_file(self, file_path: str) -> bool:
        """
        Play audio file

        Args:
            file_path: Path to audio file

        Returns:
            bool: True if playback successful
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {file_path}")
                return False

            # Read audio file
            with wave.open(file_path, 'rb') as wf:
                # Create playback stream
                stream = self._audio.open(
                    format=self._audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=self.audio_config.output_device_index
                )

                # Read and play data
                chunk_size = 1024
                data = wf.readframes(chunk_size)

                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)

                # Close stream
                stream.stop_stream()
                stream.close()

            logger.info(f"Audio playback completed: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error playing audio file: {e}")
            return False

    def _save_audio_frames(self, frames: list, file_path: str) -> bool:
        """
        Save audio frames to file

        Args:
            frames: List of audio frames
            file_path: Path to save file

        Returns:
            bool: True if save successful
        """
        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(self.audio_config.channels)
                wf.setsampwidth(self._audio.get_sample_size(self.audio_config.format))
                wf.setframerate(self.audio_config.sample_rate)
                wf.writeframes(b''.join(frames))

            return True

        except Exception as e:
            logger.error(f"Error saving audio frames: {e}")
            return False

    def get_audio_devices(self) -> Dict[str, list]:
        """
        Get available audio devices

        Returns:
            Dict[str, list]: Dictionary with 'input' and 'output' device lists
        """
        devices = {'input': [], 'output': []}

        if not self._audio:
            return devices

        try:
            for i in range(self._audio.get_device_count()):
                device_info = self._audio.get_device_info_by_index(i)
                device_data = {
                    'index': i,
                    'name': device_info['name'],
                    'max_input_channels': device_info['maxInputChannels'],
                    'max_output_channels': device_info['maxOutputChannels'],
                    'default_sample_rate': device_info['defaultSampleRate']
                }

                if device_info['maxInputChannels'] > 0:
                    devices['input'].append(device_data)

                if device_info['maxOutputChannels'] > 0:
                    devices['output'].append(device_data)

            return devices

        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
            return devices

    def set_input_device(self, device_index: int) -> bool:
        """
        Set audio input device

        Args:
            device_index: Device index

        Returns:
            bool: True if set successfully
        """
        try:
            if self._audio:
                device_info = self._audio.get_device_info_by_index(device_index)
                if device_info['maxInputChannels'] > 0:
                    self.audio_config.input_device_index = device_index
                    logger.info(f"Input device set to: {device_info['name']}")
                    return True
                else:
                    logger.error(f"Device {device_index} has no input channels")
                    return False
            return False

        except Exception as e:
            logger.error(f"Error setting input device: {e}")
            return False

    def set_output_device(self, device_index: int) -> bool:
        """
        Set audio output device

        Args:
            device_index: Device index

        Returns:
            bool: True if set successfully
        """
        try:
            if self._audio:
                device_info = self._audio.get_device_info_by_index(device_index)
                if device_info['maxOutputChannels'] > 0:
                    self.audio_config.output_device_index = device_index
                    logger.info(f"Output device set to: {device_info['name']}")
                    return True
                else:
                    logger.error(f"Device {device_index} has no output channels")
                    return False
            return False

        except Exception as e:
            logger.error(f"Error setting output device: {e}")
            return False