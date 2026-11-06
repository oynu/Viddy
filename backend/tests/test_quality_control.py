import pytest
from backend.agents.quality_control import QualityControlAgent, QCReport
from backend.media.compositor import Compositor

def test_qc_validation_rules(tmp_path):
    qc = QualityControlAgent()
    
    # Non-existent file must fail QC
    report = qc.validate_video(str(tmp_path / "non_existent.mp4"))
    assert not report.passed
    assert "not found" in report.issues[0].lower() or "missing" in report.issues[0].lower()

    # Test parameter validation rules
    valid_probe = {
        "format": {"duration": "35.2", "size": "15000000"},
        "streams": [
            {"codec_type": "video", "width": 1080, "height": 1920, "r_frame_rate": "30/1"},
            {"codec_type": "audio", "codec_name": "aac", "channels": 2}
        ]
    }
    report_valid = qc.evaluate_probe_data(valid_probe)
    assert report_valid.passed
    assert len(report_valid.issues) == 0

    # Wrong resolution must fail
    invalid_probe = {
        "format": {"duration": "35.2", "size": "15000000"},
        "streams": [
            {"codec_type": "video", "width": 720, "height": 1280, "r_frame_rate": "30/1"},
            {"codec_type": "audio", "codec_name": "aac", "channels": 2}
        ]
    }
    report_invalid = qc.evaluate_probe_data(invalid_probe)
    assert not report_invalid.passed
    assert any("resolution" in i.lower() for i in report_invalid.issues)

    # Missing audio stream must fail
    no_audio_probe = {
        "format": {"duration": "35.2", "size": "15000000"},
        "streams": [
            {"codec_type": "video", "width": 1080, "height": 1920, "r_frame_rate": "30/1"}
        ]
    }
    report_no_audio = qc.evaluate_probe_data(no_audio_probe)
    assert not report_no_audio.passed
    assert any("audio" in i.lower() for i in report_no_audio.issues)

def test_compositor_command():
    compositor = Compositor()
    cmd = compositor.build_assembly_command(
        video_clips=["clip1.mp4", "clip2.mp4"],
        narration_path="voice.wav",
        bgm_path="ambient.wav",
        subtitles_path="subs.ass",
        output_path="final.mp4"
    )
    cmd_str = " ".join(cmd)
    assert "ffmpeg" in cmd_str
    assert "final.mp4" in cmd_str
    assert "voice.wav" in cmd_str
    assert "subtitles" in cmd_str.lower() or "ass" in cmd_str.lower()
