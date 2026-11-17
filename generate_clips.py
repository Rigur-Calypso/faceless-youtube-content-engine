#!/usr/bin/env python3
"""
generate_clips.py
-----------------
Generates Ken Burns animated video clips from images for each [SCENE: ...]
marker in scripts/script.md.
Supports both YouTube Shorts (9:16 vertical 1080x1920) and standard landscape (16:9 1920x1080).
"""

import argparse
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image

DEFAULT_SCRIPT = Path("scripts/script.md")
DEFAULT_IMAGES_DIR = Path("images")
DEFAULT_CLIPS_DIR = Path("clips")
DEFAULT_AUDIO_PATH = Path("audio/voiceover.mp3")


def get_audio_duration(audio_path: Path) -> float:
    """Read voiceover duration in seconds using ffprobe."""
    if not audio_path.exists():
        return 0.0
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", str(audio_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            return float(res.stdout.strip())
        except ValueError:
            pass
    return 0.0


def extract_scenes(script_path: Path):
    """Extract all [SCENE: description] markers from script."""
    if not script_path.exists():
        return []
    content = script_path.read_text(encoding="utf-8")
    matches = re.findall(r"\[(?:SCENE|VISUAL|B-ROLL):(?:\s*)(.*?)\]", content, flags=re.IGNORECASE)
    return [m.strip() for m in matches if m.strip()]


def find_existing_image(images_dir: Path, scene_num: int):
    """Check if an image already exists for this scene."""
    for ext in [".jpg", ".png", ".jpeg", ".webp"]:
        candidate = images_dir / f"scene_{scene_num:02d}{ext}"
        if candidate.exists():
            return candidate
    return None


def render_ken_burns_clip(
    image_path: Path,
    output_clip_path: Path,
    duration: float = 8.0,
    motion_type: int = 0,
    fps: int = 25,
    is_vertical: bool = True,
) -> bool:
    """
    Renders an image into an MP4 clip with cinematic Ken Burns motion.
    is_vertical: True for 1080x1920 (Shorts), False for 1920x1080 (Landscape).
    """
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = max(25, int(duration * fps))
    target_res = "1080x1920" if is_vertical else "1920x1080"
    target_scale = "1080:1920" if is_vertical else "1920:1080"

    zoom_step = 0.15 / total_frames  # Subtle, smooth zoom

    if is_vertical:
        # Vertical motion: subtle zoom and slight vertical drift
        if motion_type == 0:
            # Smooth Zoom In
            vf = (
                f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},"
                f"zoompan=z='min(zoom+{zoom_step:.6f},1.15)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={target_res},fps={fps}"
            )
        elif motion_type == 1:
            # Smooth Zoom Out
            vf = (
                f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},"
                f"zoompan=z='if(lte(on,1),1.15,max(1.0,zoom-{zoom_step:.6f}))':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={target_res},fps={fps}"
            )
        elif motion_type == 2:
            # Subtle Pan Down
            vf = (
                f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},"
                f"zoompan=z=1.12:d={total_frames}:x='iw/2-(iw/zoom/2)':y='(on/{total_frames})*(ih-ih/zoom)':s={target_res},fps={fps}"
            )
        else:
            # Subtle Pan Up
            vf = (
                f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},"
                f"zoompan=z=1.12:d={total_frames}:x='iw/2-(iw/zoom/2)':y='(1-(on/{total_frames}))*(ih-ih/zoom)':s={target_res},fps={fps}"
            )
    else:
        # Landscape motion
        if motion_type == 0:
            vf = f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},zoompan=z='min(zoom+{zoom_step:.6f},1.20)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={target_res},fps={fps}"
        elif motion_type == 1:
            vf = f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},zoompan=z='if(lte(on,1),1.20,max(1.0,zoom-{zoom_step:.6f}))':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={target_res},fps={fps}"
        elif motion_type == 2:
            vf = f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},zoompan=z=1.15:d={total_frames}:x='(on/{total_frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':s={target_res},fps={fps}"
        else:
            vf = f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},zoompan=z=1.15:d={total_frames}:x='(1-(on/{total_frames}))*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':s={target_res},fps={fps}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        str(output_clip_path),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error rendering clip {output_clip_path}:\n{e.stderr.decode()}")
        return False


def generate_all_clips(
    script_path: Path = DEFAULT_SCRIPT,
    images_dir: Path = DEFAULT_IMAGES_DIR,
    clips_dir: Path = DEFAULT_CLIPS_DIR,
    audio_path: Path = DEFAULT_AUDIO_PATH,
    is_vertical: bool = True,
):
    scenes = extract_scenes(script_path)
    if not scenes:
        scenes = ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5", "Scene 6"]

    audio_dur = get_audio_duration(audio_path)
    if audio_dur > 0 and len(scenes) > 0:
        clip_duration = (audio_dur / len(scenes)) + 0.3
        print(f"⏱️ Audio duration: {audio_dur:.1f}s -> {clip_duration:.1f}s per scene clip")
    else:
        clip_duration = 9.5

    images_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    mode_label = "YouTube Shorts (9:16 Vertical 1080x1920)" if is_vertical else "Landscape (16:9 1920x1080)"
    print(f"🎬 Rendering {len(scenes)} clips in {mode_label}...")

    for i, desc in enumerate(scenes, 1):
        img_path = find_existing_image(images_dir, i)
        if not img_path:
            print(f"⚠️ Warning: No image found for Scene {i} in {images_dir}/scene_{i:02d}.jpg")
            continue

        clip_path = clips_dir / f"clip_{i:02d}.mp4"
        motion_type = (i - 1) % 4
        motion_names = ["Zoom In", "Zoom Out", "Pan Down", "Pan Up"]
        print(f"  [{i}/{len(scenes)}] Animating {img_path.name} -> {clip_path.name} ({motion_names[motion_type]})...")
        render_ken_burns_clip(img_path, clip_path, duration=clip_duration, motion_type=motion_type, is_vertical=is_vertical)

    print(f"✅ Clips successfully generated in {clips_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Ken Burns animated clips")
    parser.add_argument("--script", type=Path, default=DEFAULT_SCRIPT, help="Path to markdown script")
    parser.add_argument("--images", type=Path, default=DEFAULT_IMAGES_DIR, help="Images directory")
    parser.add_argument("--clips", type=Path, default=DEFAULT_CLIPS_DIR, help="Clips directory")
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO_PATH, help="Audio path")
    parser.add_argument("--landscape", action="store_true", help="Render landscape 16:9 instead of vertical 9:16")

    args = parser.parse_args()
    generate_all_clips(args.script, args.images, args.clips, args.audio, is_vertical=not args.landscape)
