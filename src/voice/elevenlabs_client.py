"""
ElevenLabs API client for text-to-speech conversion using the official SDK.
Uses the latest eleven_ttv_v3 model.
"""
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save

load_dotenv()
logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """Client for ElevenLabs text-to-speech API using official SDK."""

    # Popular voice IDs
    VOICES = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",
        "george": "JBFqnCBsd6RMkjVDRZzb",  # Deep, narrative
        "adam": "pNInz6obpgDQGcFmaJgB",
        "josh": "TxGEqnHWrfWFTfGW9XjX",
        "bella": "EXAVITQu4vr4xnSDxMaL",
        "arnold": "VR6AewLTigWG4xSOukaG",
    }

    def __init__(self, api_key: str, voice_id: Optional[str] = None):
        """
        Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use (defaults to 'george')
        """
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id or self.VOICES["george"]

    def text_to_speech(
        self,
        text: str,
        output_path: str,
        model_id: str = "eleven_v3",
        output_format: str = "mp3_44100_128",
    ) -> str:
        """
        Convert text to speech and save as MP3.

        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file
            model_id: Model to use (eleven_multilingual_v2, eleven_turbo_v2_5, eleven_turbo_v2)
            output_format: Audio format (mp3_44100_128, mp3_22050_32, etc.)

        Returns:
            Path to the saved audio file
        """
        try:
            logger.info(
                f"Generating audio for {len(text)} characters using {model_id}...")

            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=model_id,
                output_format=output_format,
            )

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Save audio file
            save(audio, str(output_file))

            logger.info(f"Audio saved to {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            raise

    def get_available_voices(self) -> list:
        """Fetch available voices from ElevenLabs."""
        try:
            response = self.client.voices.get_all()
            return response.voices
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return []

    def set_voice(self, voice_name: str) -> bool:
        """
        Set voice by name or ID.

        Args:
            voice_name: Voice name (from VOICES dict) or voice ID

        Returns:
            True if voice was set successfully
        """
        if voice_name.lower() in self.VOICES:
            self.voice_id = self.VOICES[voice_name.lower()]
            return True
        elif len(voice_name) > 10:  # Likely a voice ID
            self.voice_id = voice_name
            return True
        return False
