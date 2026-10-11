"""Whisper transcription for uploaded audio.

Groq's free Whisper tier is used when GROQ_API_KEY is set.
OpenAI is the fallback when only OPENAI_API_KEY is set.
The chat microphone uses the browser and does not call this.
"""

import os

import requests


def transcribe_audio(filename: str, data: bytes) -> str:
    if not data:
        raise RuntimeError("The audio file is empty.")
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        return _transcribe(
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key=groq_key,
            filename=filename,
            data=data,
            model=os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo"),
        )
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return _transcribe(
            url="https://api.openai.com/v1/audio/transcriptions",
            api_key=openai_key,
            filename=filename,
            data=data,
            model="whisper-1",
        )
    raise RuntimeError(
        "GROQ_API_KEY is not set. Use the browser microphone, or add a Groq key."
    )


def _transcribe(url: str, api_key: str, filename: str, data: bytes, model: str) -> str:
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": (filename or "audio.webm", data)},
        data={"model": model},
        timeout=90,
    )
    if response.status_code >= 400:
        detail = response.text[:300]
        raise RuntimeError(f"Transcription failed ({response.status_code}): {detail}")
    return response.json().get("text") or ""
