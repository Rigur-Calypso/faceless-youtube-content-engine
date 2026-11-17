#!/usr/bin/env python3
"""
generate_voice.py
-----------------
Converts a Markdown script into spoken audio (MP3) and synchronized subtitles (SRT)
using Microsoft Edge Neural TTS (edge-tts). Completely free, no API keys needed.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_VOICE = "en-US-GuyNeural"
DEFAULT_SCRIPT = Path("scripts/script.md")
DEFAULT_AUDIO = Path("audio/voiceover.mp3")
DEFAULT_SRT = Path("audio/voiceover.srt")


def clean_script_for_tts(script_text: str) -> str:
    """
    Extracts purely spoken narration:
    - Removes [SCENE: ...] and [VISUAL: ...] director markers
    - Removes markdown header markers (#, ##, ###) while preserving spoken titles if appropriate,
      or skips section meta-headers.
    - Strips markdown formatting (*, _, `, etc.)
    """
    lines = script_text.splitlines()
    spoken_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip scene markers
        if re.match(r"^\[(?:SCENE|VISUAL|B-ROLL|IMAGE|CLIP):.*?\]$", stripped, re.IGNORECASE):
            continue

        # Skip markdown horizontal rules
        if stripped in ("---", "***", "___"):
            continue

        # If it's a section header like "# Section 1: Title", skip if it's purely structural
        if stripped.startswith("#"):
            # If the heading is something like "# Title: ...", skip
            # If it's educational content that should be spoken, keep without '#'
            header_text = stripped.lstrip("#").strip()
            if re.match(r"^(hook|section \d+|scene \d+|call to action|outro|intro|cta):?$", header_text, re.IGNORECASE):
                continue
            # Otherwise, keep header text as spoken transition
            stripped = header_text

        # Remove inline [SCENE: ...] markers if any exist inline
        cleaned = re.sub(r"\[(?:SCENE|VISUAL|B-ROLL|IMAGE|CLIP):.*?\]", "", stripped, flags=re.IGNORECASE)

        # Remove bold / italics markdown
        cleaned = re.sub(r"[*_~`]", "", cleaned)
        cleaned = cleaned.strip()

        if cleaned:
            spoken_lines.append(cleaned)

    return "\n\n".join(spoken_lines)


def generate_voiceover(
    script_path: Path = DEFAULT_SCRIPT,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    audio_path: Path = DEFAULT_AUDIO,
    srt_path: Path = DEFAULT_SRT,
) -> bool:
    if not script_path.exists():
        print(f"❌ Error: Script file not found at {script_path}")
        return False

    script_text = script_path.read_text(encoding="utf-8")
    spoken_text = clean_script_for_tts(script_text)

    if not spoken_text.strip():
        print(f"❌ Error: No spoken text found in {script_path}")
        return False

    audio_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    temp_spoken_file = audio_path.parent / "spoken_text.txt"
    temp_spoken_file.write_text(spoken_text, encoding="utf-8")

    word_count = len(spoken_text.split())
    print(f"🎙️ Generating voiceover with voice '{voice}' ({word_count} words)...")

    cmd = [
        "edge-tts",
        "-f", str(temp_spoken_file),
        "-v", voice,
        "--rate", rate,
        "--write-media", str(audio_path),
        "--write-subtitles", str(srt_path),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"❌ edge-tts failed with error:\n{e.stderr.decode()}")
        return False
    except FileNotFoundError:
        print("❌ edge-tts command not found. Run: pip install edge-tts")
        return False

    print(f"✅ Voiceover created: {audio_path}")
    print(f"✅ Subtitles created: {srt_path}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate voiceover and subtitles from script")
    parser.add_argument("--script", type=Path, default=DEFAULT_SCRIPT, help="Path to markdown script")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE, help="edge-tts voice name")
    parser.add_argument("--rate", type=str, default="+0%", help="Speed rate (e.g. +10%% or -10%%)")
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO, help="Output MP3 path")
    parser.add_argument("--srt", type=Path, default=DEFAULT_SRT, help="Output SRT path")

    args = parser.parse_args()
    success = generate_voiceover(args.script, args.voice, args.rate, args.audio, args.srt)
    sys.exit(0 if success else 1)
