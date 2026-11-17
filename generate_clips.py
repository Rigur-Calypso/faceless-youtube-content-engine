#!/usr/bin/env python3
"""
generate_clips.py
-----------------
Generates Ken Burns animated video clips from images for each [SCENE: ...]
marker in scripts/script.md.
Supports both YouTube Shorts (9:16 vertical 1080x1920) and standard landscape (16:9 1920x1080).
If an image is missing, automatically creates a clean placeholder slide so the pipeline
runs reliably out of the box.
"""

import argparse
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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


def create_placeholder_image(output_path: Path, scene_num: int, scene_desc: str, is_vertical: bool = True):
    """Generates a stylish dark gradient placeholder slide when no user image exists."""
    width, height = (1080, 1920) if is_vertical else (1920, 1080)
    img = Image.new("RGB", (width, height), color=(18, 18, 24))
    draw = ImageDraw.Draw(img)

    # Simple background gradient
    for y in range(height):
        ratio = y / height
        r = int(15 + ratio * 20)
        g = int(20 + ratio * 30)
        b = int(35 + ratio * 45)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Center card border
    margin = 80 if is_vertical else 120
    draw.rectangle(
        [(margin, margin), (width - margin, height - margin)],
        outline=(50, 70, 100),
        width=3
    )

    # Text indicator
    label = f"SCENE {scene_num:02d}"
    clean_desc = scene_desc[:60] + ("..." if len(scene_desc) > 60 else "")

    try:
        font_large = ImageFont.load_default(size=44)
        font_small = ImageFont.load_default(size=26)
    except TypeError:
        font_large = ImageFont.load_default()
        font_small = font_large

    draw.text((width // 2, height // 2 - 40), label, fill=(220, 230, 255), anchor="mm", font=font_large)
    draw.text((width // 2, height // 2 + 40), clean_desc, fill=(140, 160, 190), anchor="mm", font=font_small)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=92)
    return output_path


def find_existing_image(images_dir: Path, scene_num: int, scene_desc: str = "", is_vertical: bool = True):
    """Check if an image exists for this scene, or auto-generate a fallback placeholder."""
    prefixes = [
        f"scene_{scene_num:02d}",
        f"frame_{scene_num:02d}",
        f"scene_{scene_num}",
        f"frame_{scene_num}",
    ]
    for ext in [".jpg", ".png", ".jpeg", ".webp"]:
        for prefix in prefixes:
            candidate = images_dir / f"{prefix}{ext}"
            if candidate.exists():
                return candidate

    # Fallback: create a placeholder slide so the pipeline runs seamlessly
    placeholder = images_dir / f"scene_{scene_num:02d}.jpg"
    print(f"  ℹ️ Auto-creating placeholder graphic for Scene {scene_num}...")
    create_placeholder_image(placeholder, scene_num, scene_desc, is_vertical=is_vertical)
    return placeholder


def render_ken_burns_clip(
    image_path: Path,
    output_clip_path: Path,
    duration: float = 8.0,
    motion_type: int = 0,
    fps: int = 25,
    is_vertical: bool = True,
) -> bool:
    """Renders an image into an MP4 clip with cinematic Ken Burns camera motion."""
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = max(25, int(duration * fps))
    target_res = "1080x1920" if is_vertical else "1920x1080"
    target_scale = "1080:1920" if is_vertical else "1920:1080"

    zoom_step = 0.15 / total_frames

    if is_vertical:
        if motion_type == 0:
            vf = (
                f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},"
                f"zoompan=z='min(zoom+{zoom_step:.6f},1.15)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={target_res},fps={fps}"
            )
        elif motion_type == 1:
            vf = (
                f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},"
                f"zoompan=z='if(lte(on,1),1.15,max(1.0,zoom-{zoom_step:.6f}))':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={target_res},fps={fps}"
            )
        elif motion_type == 2:
            vf = (
                f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},"
                f"zoompan=z=1.12:d={total_frames}:x='iw/2-(iw/zoom/2)':y='(on/{total_frames})*(ih-ih/zoom)':s={target_res},fps={fps}"
            )
        else:
            vf = (
                f"scale={target_scale}:force_original_aspect_ratio=increase,crop={target_scale},"
                f"zoompan=z=1.12:d={total_frames}:x='iw/2-(iw/zoom/2)':y='(1-(on/{total_frames}))*(ih-ih/zoom)':s={target_res},fps={fps}"
            )
    else:
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
        scenes = ["Introduction", "Core Insight", "Key Breakdown", "Important Takeaway", "Conclusion"]

    audio_dur = get_audio_duration(audio_path)
    if audio_dur > 0 and len(scenes) > 0:
        clip_duration = (audio_dur / len(scenes)) + 0.3
        print(f"⏱️ Audio duration: {audio_dur:.1f}s -> {clip_duration:.1f}s per scene clip")
    else:
        clip_duration = 8.0

    images_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    mode_label = "YouTube Shorts (9:16 Vertical 1080x1920)" if is_vertical else "Landscape (16:9 1920x1080)"
    print(f"🎬 Rendering {len(scenes)} clips in {mode_label}...")

    for i, desc in enumerate(scenes, 1):
        img_path = find_existing_image(images_dir, i, scene_desc=desc, is_vertical=is_vertical)
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
