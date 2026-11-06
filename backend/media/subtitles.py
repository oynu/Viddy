from pathlib import Path
from typing import List, Optional

class SubtitleGenerator:
    def __init__(self):
        pass

    def generate_ass_subtitles(
        self,
        script_blocks: Optional[List[str]] = None,
        text: Optional[str] = None,
        total_duration: float = 30.0,
        output_ass_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        full_text = text or " ".join(script_blocks or [])
        out = output_ass_path or output_path or "subtitles.ass"
        return self.generate_styled_ass(full_text, total_duration, out)

    def generate_styled_ass(
        self,
        text: str,
        total_duration: float,
        output_path: str
    ) -> str:
        """
        Generates vertical 9:16 optimized Advanced SubStation Alpha (.ass) subtitles
        with high contrast, heavy black outline, and kinetic rhythm.
        """
        words = text.split()
        if not words:
            words = ["..."]
            
        # Group into punchy 3 to 5 word chunks
        chunk_size = 4
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        chunk_duration = total_duration / len(chunks)
        
        ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,320,1
Style: Highlight,Arial,68,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,4,2,60,60,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for idx, chunk in enumerate(chunks):
            start_sec = idx * chunk_duration
            end_sec = min(total_duration, (idx + 1) * chunk_duration)
            
            start_str = self._format_ass_time(start_sec)
            end_str = self._format_ass_time(end_sec)
            
            # Use highlight style on alternating lines or key questions
            style = "Highlight" if "?" in chunk or idx == 0 else "Default"
            events.append(f"Dialogue: 0,{start_str},{end_str},{style},,0,0,0,,{chunk.upper()}")
            
        ass_content = ass_header + "\n".join(events) + "\n"
        
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(ass_content)
            
        return str(out_file)

    def _format_ass_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds - int(seconds)) * 100))
        if centis >= 100:
            centis = 99
        return f"{hours:01d}:{minutes:02d}:{secs:02d}.{centis:02d}"
