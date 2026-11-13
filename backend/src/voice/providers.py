from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.google.llm import GoogleLLMService


def create_stt(api_key: str) -> ElevenLabsRealtimeSTTService:
    return ElevenLabsRealtimeSTTService(
        api_key=api_key,
        settings=ElevenLabsRealtimeSTTService.Settings(
            model="scribe_v2_realtime",
            language="en",
        ),
    )


def create_llm(api_key: str, system_prompt: str) -> GoogleLLMService:
    return GoogleLLMService(
        api_key=api_key,
        settings=GoogleLLMService.Settings(
            model="gemini-3.6-flash",
            system_instruction=system_prompt,
        ),
    )


def create_tts(api_key: str) -> ElevenLabsTTSService:
    return ElevenLabsTTSService(
        api_key=api_key,
        settings=ElevenLabsTTSService.Settings(
            model="eleven_turbo_v2_5",
            voice="cgSgspJ2msm6clMCkdW9",  # "Jessica"
        ),
    )
