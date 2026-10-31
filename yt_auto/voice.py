"""Text-to-speech using Microsoft Edge's free neural voices (edge-tts)."""
import asyncio

import edge_tts


async def _save(text: str, voice: str, path: str) -> None:
    await edge_tts.Communicate(text, voice).save(path)


def synthesize(text: str, path: str, voice: str = "en-US-AndrewNeural") -> None:
    asyncio.run(_save(text, voice, path))
