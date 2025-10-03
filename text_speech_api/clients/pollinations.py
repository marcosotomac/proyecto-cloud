"""HTTP client for gTTS (Google Text-to-Speech) - Free Alternative"""
import httpx
import logging
from typing import Optional
from gtts import gTTS
import io

logger = logging.getLogger(__name__)


class PollinationsTTSClient:
    """Client for Text-to-Speech using gTTS (Google TTS - Free)"""

    def __init__(self, base_url: str = "https://text.pollinations.ai"):
        # Keep for compatibility but we'll use gTTS instead
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    async def generate_speech(
        self,
        prompt: str,
        model: str = "gtts",
        voice: str = "en"
    ) -> bytes:
        """
        Generate speech from text using gTTS (Google Text-to-Speech)

        Free alternative to paid TTS services.

        Args:
            prompt: Text to synthesize
            model: TTS model (gtts, gtts-slow)
            voice: Language code (en, es, fr, de, etc.)

        Returns:
            Audio bytes (MP3 format)

        Raises:
            Exception: If TTS generation fails
        """
        try:
            logger.info(
                f"Generating TTS with gTTS: prompt_length={len(prompt)}, lang={voice}")

            # Determine if slow speech is requested
            slow = model == "gtts-slow"

            # Generate speech using gTTS
            tts = gTTS(text=prompt, lang=voice, slow=slow)

            # Save to BytesIO buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            audio_bytes = audio_buffer.read()
            logger.info(
                f"TTS generated successfully: size={len(audio_bytes)} bytes")

            return audio_bytes

        except Exception as e:
            logger.error(f"gTTS generation failed: {e}")
            raise


async def test_pollinations_tts():
    """Test function for gTTS client"""
    client = PollinationsTTSClient()

    try:
        audio = await client.generate_speech(
            prompt="Hello, this is a test",
            voice="en"
        )
        print(f"✓ TTS test successful: {len(audio)} bytes")
        return True
    except Exception as e:
        print(f"✗ TTS test failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pollinations_tts())
