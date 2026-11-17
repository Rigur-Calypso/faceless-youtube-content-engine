#!/usr/bin/env python3
"""
assemble.py
-----------
Combines visual clips, voiceover audio, and synchronized subtitles into a finished
YouTube Shorts MP4 video (9:16 vertical 1080x1920) or landscape (16:9 1920x1080).
Places subtitles right at the bottom edge (MarginV=70).
"""

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_CLIPS_DIR = Path("clips")
DEFAULT_AUDIO = Path("audio/voiceover.mp3")
DEFAULT_SUBTITLES = Path("audio/voiceover.srt")
DEFAULT_OUTPUT = Path("output/final_video.mp4")


def get_duration(file_path: Path) -> float:
    """Get media duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        str(file_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        return 0.0
    try:
        return float(res.stdout.strip())
    except ValueError:
        return 0.0


def escape_ffmpeg_path(path: Path) -> str:
    """Escapes special characters in file paths for FFmpeg filters."""
    p_str = str(path.resolve()).replace("\\", "/")
    p_str = p_str.replace(":", "\\:").replace("'", "\\'")
    return p_str


def assemble_video(
    clips_dir: Path = DEFAULT_CLIPS_DIR,
    audio_path: Path = DEFAULT_AUDIO,
    subtitles_path: Path = DEFAULT_SUBTITLES,
    output_path: Path = DEFAULT_OUTPUT,
    font_size: int = 28,
    is_vertical: bool = True,
) -> bool:
    clip_files = sorted(clips_dir.glob("clip_*.mp4"))
    if not clip_files:
        print(f"❌ Error: No clips found in {clips_dir}/ matching clip_*.mp4")
        return False

    if not audio_path.exists():
        print(f"❌ Error: Voiceover audio not found at {audio_path}")
        return False

    audio_duration = get_duration(audio_path)
    if audio_duration <= 0.0:
        print(f"❌ Error: Invalid audio duration for {audio_path}")
        return False

    clip_duration = audio_duration / len(clip_files)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mode_text = "YouTube Shorts (9:16 Vertical 1080x1920)" if is_vertical else "Landscape (16:9 1920x1080)"
    target_scale = "1080:1920" if is_vertical else "1920:1080"
    res_x = 1080 if is_vertical else 1920
    res_y = 1920 if is_vertical else 1080
    margin_v = 70 if is_vertical else 30

    print(f"🎬 Assembling Video in {mode_text}...")
    print(f"  • Clips count: {len(clip_files)}")
    print(f"  • Voiceover duration: {audio_duration:.2f}s")
    print(f"  • Duration per clip: {clip_duration:.2f}s")
    print(f"  • Subtitle placement: VERY BOTTOM (MarginV={margin_v})")

    inputs = []
    filter_parts = []

    for i, clip in enumerate(clip_files):
        inputs.extend(["-i", str(clip)])
        filter_parts.append(
            f"[{i}:v]scale={target_scale}:force_original_aspect_ratio=increase,"
            f"crop={target_scale},setsar=1,"
            f"trim=duration={clip_duration},setpts=PTS-STARTPTS[v{i}]"
        )

    # Concat clips
    concat_inputs = "".join(f"[v{i}]" for i in range(len(clip_files)))
    filter_parts.append(f"{concat_inputs}concat=n={len(clip_files)}:v=1:a=0[merged]")

    # Subtitles burn-in: Clean white text right at the very bottom (Alignment=2, MarginV=70)
    if subtitles_path.exists():
        sub_escaped = escape_ffmpeg_path(subtitles_path)
        style = (
            f"PlayResX={res_x},PlayResY={res_y},"
            f"FontName=Helvetica,FontSize={font_size},"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,"
            f"BorderStyle=1,Outline=1.2,Shadow=0,"
            f"Alignment=2,MarginV={margin_v},Bold=1,Spacing=0.5"
        )
        filter_parts.append(f"[merged]subtitles='{sub_escaped}':force_style='{style}'[final]")
        final_video_label = "[final]"
    else:
        print("⚠️ Warning: Subtitles file not found. Rendering video without subtitles.")
        final_video_label = "[merged]"

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", final_video_label,
        "-map", f"{len(clip_files)}:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"❌ FFmpeg assembly error:\n{res.stderr}")
            return False
    except Exception as e:
        print(f"❌ Subprocess failed: {e}")
        return False

    final_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"🎉 Final Video successfully created!")
    print(f"  • File: {output_path}")
    print(f"  • Size: {final_size_mb:.2f} MB")
    print(f"  • Format: {mode_text}")
    print(f"  • Total Duration: {audio_duration:.2f}s")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assemble clips and audio into final video")
    parser.add_argument("--clips", type=Path, default=DEFAULT_CLIPS_DIR, help="Clips directory")
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO, help="Voiceover audio path")
    parser.add_argument("--subtitles", type=Path, default=DEFAULT_SUBTITLES, help="SRT subtitles path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Final output MP4 path")
    parser.add_argument("--font-size", type=int, default=28, help="Subtitles font size")
    parser.add_argument("--landscape", action="store_true", help="Render landscape 16:9 instead of vertical 9:16")

    args = parser.parse_args()
    success = assemble_video(
        args.clips,
        args.audio,
        args.subtitles,
        args.output,
        font_size=args.font_size,
        is_vertical=not args.landscape
    )
    sys.exit(0 if success else 1)
