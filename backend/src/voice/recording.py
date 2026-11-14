import wave
from io import BytesIO

import logfire as logger
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor

from src.core import storage


class CallRecorder:
    """Records the whole call (caller and agent mixed, mono) in memory, and
    uploads it as a WAV to the bucket when the call ends."""

    def __init__(self, recording_url: str) -> None:
        self._recording_url = recording_url

        # buffer_size=0: on_audio_data fires once, with the whole call, when the
        # pipeline ends (EndFrame or CancelFrame).
        self.processor = AudioBufferProcessor(num_channels=1, auto_start_recording=True)
        self.processor.event_handler("on_audio_data")(self._on_audio_data)

    async def _on_audio_data(
        self,
        _processor: AudioBufferProcessor,
        audio: bytes,
        sample_rate: int,
        num_channels: int,
    ) -> None:
        if not audio:
            return

        with BytesIO() as buffer:
            with wave.open(buffer, "wb") as wf:
                wf.setnchannels(num_channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio)
            data = buffer.getvalue()

        try:
            await storage.upload_bytes(self._recording_url, data, "audio/wav")
        except Exception:
            logger.exception("Failed to upload the call recording.")
