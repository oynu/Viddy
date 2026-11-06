import pytest
import os
from backend.media.audio_engine import AudioEngine
from backend.media.subtitles import SubtitleGenerator

@pytest.mark.asyncio
async def test_audio_synthesis_and_subtitles(tmp_path):
    output_audio = tmp_path / "test_narration.mp3"
    output_subtitles = tmp_path / "test_subs.ass"
    
    engine = AudioEngine()
    test_text = "What if gravity vanished for just five seconds? Everything not bolted down would launch into the sky."
    
    audio_path, duration = await engine.generate_voiceover(test_text, str(output_audio))
    assert os.path.exists(audio_path)
    assert duration > 0.5
    
    sub_gen = SubtitleGenerator()
    sub_path = sub_gen.generate_styled_ass(test_text, duration, str(output_subtitles))
    assert os.path.exists(sub_path)
    with open(sub_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "[Script Info]" in content
        assert "Style: Default" in content
        assert "gravity vanished" in content.lower()
