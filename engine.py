#!/usr/bin/env python3
"""
engine.py
---------
Master Orchestrator for the Faceless YouTube Content Engine in Antigravity.

Usage:
  python3 engine.py --status       # Verify tools, environment, and pipeline status
  python3 engine.py --voice        # Stage 1: Generate voiceover MP3 & SRT subtitles
  python3 engine.py --clips        # Stage 2: Render 1080p Ken Burns animated clips
  python3 engine.py --assemble     # Stage 3: Assemble video with audio & burned captions
  python3 engine.py --metadata     # Stage 4: Generate YouTube SEO metadata
  python3 engine.py --run-all      # Execute the complete pipeline end-to-end!
  python3 engine.py --clean        # Clean build artifacts to start a new video
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
SCRIPT_PATH = BASE_DIR / "scripts" / "script.md"
AUDIO_PATH = BASE_DIR / "audio" / "voiceover.mp3"
SRT_PATH = BASE_DIR / "audio" / "voiceover.srt"
IMAGES_DIR = BASE_DIR / "images"
CLIPS_DIR = BASE_DIR / "clips"
OUTPUT_DIR = BASE_DIR / "output"
FINAL_VIDEO = OUTPUT_DIR / "final_video.mp4"
METADATA_JSON = OUTPUT_DIR / "metadata.json"


def check_tool(name: str) -> bool:
    return shutil.which(name) is not None


def show_status():
    print("\n🔍 === FACELESS YOUTUBE CONTENT ENGINE STATUS ===")
    print("Environment:")
    print(f"  • Python 3:  {'✅ Available' if check_tool('python3') else '❌ Missing'}")
    print(f"  • FFmpeg:    {'✅ Available' if check_tool('ffmpeg') else '❌ Missing'}")
    print(f"  • edge-tts:  {'✅ Available' if check_tool('edge-tts') else '❌ Missing'}")

    print("\nProject Folders & Assets:")
    script_exists = SCRIPT_PATH.exists()
    print(f"  • scripts/script.md:  {'✅ Ready' if script_exists else '⏳ Missing (Create this first!)'}")
    audio_exists = AUDIO_PATH.exists() and SRT_PATH.exists()
    print(f"  • audio/ (MP3 + SRT): {'✅ Ready' if audio_exists else '⏳ Pending voice generation'}")
    
    clip_count = len(list(CLIPS_DIR.glob("clip_*.mp4"))) if CLIPS_DIR.exists() else 0
    print(f"  • clips/ (1080p MP4): {'✅ ' + str(clip_count) + ' clips ready' if clip_count > 0 else '⏳ Pending clip rendering'}")

    video_exists = FINAL_VIDEO.exists()
    print(f"  • output/final_video: {'✅ ' + str(FINAL_VIDEO.stat().st_size // (1024*1024)) + ' MB' if video_exists else '⏳ Pending assembly'}")
    meta_exists = METADATA_JSON.exists()
    print(f"  • output/metadata:    {'✅ Ready' if meta_exists else '⏳ Pending metadata generation'}")
    print("==================================================\n")


def clean_artifacts():
    print("🧹 Cleaning intermediate and output files...")
    for folder in [BASE_DIR / "audio", IMAGES_DIR, CLIPS_DIR, OUTPUT_DIR]:
        if folder.exists():
            for item in folder.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    item.unlink()
    print("✨ Clean complete! Ready for a fresh video.")


def run_stage(command: list, stage_name: str) -> bool:
    print(f"\n▶️ Starting {stage_name}...")
    res = subprocess.run(command, cwd=BASE_DIR)
    if res.returncode != 0:
        print(f"❌ {stage_name} encountered an error.")
        return False
    return True


def run_all(voice: str = "en-US-GuyNeural", rate: str = "+0%", font_size: int = 24):
    if not SCRIPT_PATH.exists():
        print(f"❌ Error: Please create your script at {SCRIPT_PATH} first!")
        return False

    print("🚀 === EXECUTING FULL PIPELINE ===")
    
    # 1. Voice & Subtitles
    if not run_stage([sys.executable, "generate_voice.py", "--voice", voice, "--rate", rate], "Stage 1: Voiceover & Subtitles"):
        return False

    # 2. Clips
    if not run_stage([sys.executable, "generate_clips.py"], "Stage 2: Ken Burns Animated Clips"):
        return False

    # 3. Assemble
    if not run_stage([sys.executable, "assemble.py", "--font-size", str(font_size)], "Stage 3: Video Assembly & Subtitle Burn-In"):
        return False

    # 4. Metadata
    if not run_stage([sys.executable, "generate_metadata.py"], "Stage 4: YouTube SEO Metadata"):
        return False

    print("\n🎉 === PRODUCTION COMPLETE! ===")
    print(f"  📹 Finished Video: {FINAL_VIDEO}")
    print(f"  📄 Metadata:       {METADATA_JSON}")
    print("===============================\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master orchestrator for Faceless YouTube Content Engine")
    parser.add_argument("--status", action="store_true", help="Check pipeline status and prerequisites")
    parser.add_argument("--voice", action="store_true", help="Generate voiceover and subtitles")
    parser.add_argument("--clips", action="store_true", help="Generate visual clips")
    parser.add_argument("--assemble", action="store_true", help="Assemble final video")
    parser.add_argument("--metadata", action="store_true", help="Generate YouTube metadata")
    parser.add_argument("--run-all", action="store_true", help="Run the entire pipeline end-to-end")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--voice-name", type=str, default="en-US-GuyNeural", help="TTS voice name")
    parser.add_argument("--font-size", type=int, default=24, help="Subtitles font size")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.clean:
        clean_artifacts()
    elif args.voice:
        run_stage([sys.executable, "generate_voice.py", "--voice", args.voice_name], "Voiceover Generation")
    elif args.clips:
        run_stage([sys.executable, "generate_clips.py"], "Clips Generation")
    elif args.assemble:
        run_stage([sys.executable, "assemble.py", "--font-size", str(args.font_size)], "Video Assembly")
    elif args.metadata:
        run_stage([sys.executable, "generate_metadata.py"], "Metadata Generation")
    elif args.run_all:
        run_all(voice=args.voice_name, font_size=args.font_size)
    else:
        show_status()
        print("💡 Run with --help or --run-all to execute the pipeline.")
