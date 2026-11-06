import os
import shutil
import subprocess
import asyncio
from pathlib import Path
from typing import List, Optional
from backend.config import settings

class Compositor:
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or settings.ffmpeg_path

    def build_assembly_command(
        self,
        video_clips: List[str],
        narration_path: str,
        bgm_path: Optional[str],
        subtitles_path: Optional[str],
        output_path: str
    ) -> List[str]:
        """
        Builds the FFmpeg command line to concatenate clips, mix narration & BGM,
        and burn synchronized vertical ASS subtitles.
        """
        cmd = [self.ffmpeg_path, "-y"]
        
        # Inputs: video clips
        for clip in video_clips:
            cmd.extend(["-i", str(clip)])
            
        # Input: voice narration
        narration_idx = len(video_clips)
        cmd.extend(["-i", str(narration_path)])
        
        # Input: BGM if provided
        bgm_idx = None
        if bgm_path:
            bgm_idx = len(video_clips) + 1
            cmd.extend(["-i", str(bgm_path)])
            
        # Filter complex construction
        filter_parts = []
        
        # Concat video streams
        num_vids = len(video_clips)
        concat_inputs = "".join([f"[{i}:v]" for i in range(num_vids)])
        filter_parts.append(f"{concat_inputs}concat=n={num_vids}:v=1:a=0[v_concat]")
        
        # Subtitle burning on vertical video
        current_v = "[v_concat]"
        if subtitles_path:
            # Use relative posix path to avoid Windows drive colon (C:) tripping FFmpeg's filter parser
            try:
                rel_sub = Path(subtitles_path).resolve().relative_to(Path.cwd()).as_posix()
            except Exception:
                rel_sub = Path(subtitles_path).as_posix().replace(":", "\\:")
            filter_parts.append(f"{current_v}subtitles={rel_sub}[v_sub]")
            current_v = "[v_sub]"
            
        # Audio mixing: Voice + soft BGM
        if bgm_idx is not None:
            filter_parts.append(f"[{narration_idx}:a]volume=1.0[a_voice]")
            filter_parts.append(f"[{bgm_idx}:a]volume=0.15[a_bgm]")
            filter_parts.append(f"[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=2[a_out]")
            audio_tag = "[a_out]"
        else:
            filter_parts.append(f"[{narration_idx}:a]anull[a_out]")
            audio_tag = "[a_out]"
            
        filter_str = ";".join(filter_parts)
        cmd.extend(["-filter_complex", filter_str])
        
        # Map final streams
        cmd.extend([
            "-map", current_v,
            "-map", audio_tag,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path)
        ])
        
        return cmd

    async def assemble_video_async(
        self,
        video_clips: Optional[List[str]] = None,
        narration_path: Optional[str] = None,
        bgm_path: Optional[str] = None,
        subtitles_path: Optional[str] = None,
        output_path: Optional[str] = None,
        scene_clip_paths: Optional[List[str]] = None,
        audio_path: Optional[str] = None,
        thumbnail_output_path: Optional[str] = None,
        target_duration: Optional[float] = None,
        timeout_seconds: float = 180.0
    ) -> str:
        """Runs the FFmpeg assembly asynchronously."""
        clips = video_clips or scene_clip_paths or []
        audio = narration_path or audio_path or ""
        out_target = output_path or "output/final.mp4"
        out_file = Path(out_target)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        # If multiple clips or need subtitles, run the assembly command
        cmd = self.build_assembly_command(
            video_clips=clips,
            narration_path=audio,
            bgm_path=bgm_path,
            subtitles_path=subtitles_path,
            output_path=str(out_file)
        )
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        except Exception:
            pass
        
        if not out_file.exists() or out_file.stat().st_size < 1000:
            # Fallback simple mux if complex filter encountered an error
            fallback_cmd = [
                self.ffmpeg_path, "-y",
                "-i", str(clips[0]) if clips else "",
                "-i", str(audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(out_file)
            ]
            try:
                fb_proc = await asyncio.create_subprocess_exec(*fallback_cmd)
                await asyncio.wait_for(fb_proc.communicate(), timeout=timeout_seconds)
            except Exception:
                pass

        if thumbnail_output_path and out_file.exists():
            self.extract_thumbnail(str(out_file), thumbnail_output_path)
            
        return str(out_file)

    def extract_thumbnail(self, video_path: str, output_thumbnail_path: str) -> str:
        """Extracts a crisp frame at 1.5s as high-res thumbnail."""
        out_file = Path(output_thumbnail_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            self.ffmpeg_path, "-y",
            "-ss", "00:00:01.5",
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(out_file)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            pass
        return str(out_file)
