import os
import requests

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech"


def synthesize_live_room_voice(text: str) -> bytes:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY não configurada")

    if not voice_id:
        raise RuntimeError("ELEVENLABS_VOICE_ID não configurado")

    url = f"{ELEVEN_URL}/{voice_id}"

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.6,
            "use_speaker_boost": True,
        },
    }

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"Erro ElevenLabs: {response.text}")

    return response.content