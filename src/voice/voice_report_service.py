"""
Voice Report Service - Orchestrates script generation, audio creation, and email delivery.
"""
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from .script_generator import VoiceScriptGenerator
from .elevenlabs_client import ElevenLabsClient

logger = logging.getLogger(__name__)


class VoiceReportService:
    """
    Orchestrates the complete voice report workflow:
    1. Generate narration script from executive summary
    2. Convert script to audio via ElevenLabs
    3. Prepare audio for email attachment
    """

    def __init__(
        self,
        llm_api_key: str,
        elevenlabs_api_key: str,
        llm_model: str = "gemini-2.0-flash",
        llm_provider: str = "gemini",
        voice_name: str = "rachel"
    ):
        """
        Initialize the voice report service.

        Args:
            llm_api_key: API key for LLM (Gemini/OpenAI)
            elevenlabs_api_key: API key for ElevenLabs
            llm_model: LLM model to use
            llm_provider: 'gemini' or 'openai'
            voice_name: ElevenLabs voice name
        """
        self.script_generator = VoiceScriptGenerator(
            api_key=llm_api_key,
            model=llm_model,
            provider=llm_provider
        )

        self.tts_client = ElevenLabsClient(
            api_key=elevenlabs_api_key,
            voice_id=ElevenLabsClient.VOICES.get(voice_name.lower())
        )

        self.output_dir = Path("reports/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_voice_report(
        self,
        insights: dict,
        report_data: dict,
        output_filename: Optional[str] = None
    ) -> dict:
        """
        Generate complete voice report (script + audio).

        Args:
            insights: LLM-generated insights dictionary
            report_data: Aggregated report data
            output_filename: Optional custom filename for audio

        Returns:
            Dictionary with:
                - script: Generated narration script
                - audio_path: Path to generated audio file
                - month: Report month
                - success: Boolean indicating success
        """
        month = report_data.get('report_month', 'Monthly Report')
        month_slug = month.lower().replace(' ', '_')

        result = {
            "month": month,
            "script": None,
            "audio_path": None,
            "success": False
        }

        try:
            # Step 1: Generate narration script
            logger.info(f"Generating voice script for {month}...")
            script = self.script_generator.generate_script(
                insights, report_data)
            result["script"] = script

            # Step 2: Convert to audio
            if output_filename:
                audio_filename = output_filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d")
                audio_filename = f"executive_summary_{month_slug}_{timestamp}.mp3"

            audio_path = self.output_dir / audio_filename

            logger.info(f"Converting script to audio...")
            self.tts_client.text_to_speech(script, str(audio_path))
            result["audio_path"] = str(audio_path)

            result["success"] = True
            logger.info(f"Voice report generated successfully: {audio_path}")

        except Exception as e:
            logger.error(f"Error generating voice report: {e}")
            result["error"] = str(e)

        return result

    def get_audio_for_email(
        self,
        insights: dict,
        report_data: dict
    ) -> Optional[str]:
        """
        Convenience method to generate audio and return path for email attachment.

        Args:
            insights: LLM-generated insights
            report_data: Report data

        Returns:
            Path to audio file or None if generation failed
        """
        result = self.generate_voice_report(insights, report_data)
        return result.get("audio_path") if result["success"] else None

    def get_memory_status(self) -> list:
        """Get status of stored monthly summaries in memory."""
        return self.script_generator.get_memory_summary()

    def clear_memory(self):
        """Clear the script generator's memory."""
        self.script_generator.clear_memory()


def create_voice_service_from_settings():
    """Factory function to create VoiceReportService from app settings."""
    from config.settings import settings

    # Detect provider
    if settings.LLM_API_KEY and settings.LLM_API_KEY.startswith('AIza'):
        provider = 'gemini'
    else:
        provider = 'openai'

    return VoiceReportService(
        llm_api_key=settings.LLM_API_KEY,
        elevenlabs_api_key=settings.ELEVENLABS_API_KEY,
        llm_model=settings.LLM_MODEL,
        llm_provider=provider,
        voice_name=getattr(settings, 'VOICE_NAME', 'rachel')
    )
