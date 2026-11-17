#!/usr/bin/env python3
"""
generate_metadata.py
--------------------
Generates YouTube-ready metadata (SEO titles, description, tags, thumbnail prompts)
from the video script and saves it to output/metadata.json.
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SCRIPT = Path("scripts/script.md")
DEFAULT_OUTPUT = Path("output/metadata.json")


def analyze_script(script_text: str):
    """Extracts title, hook, key scenes, and main topics from script."""
    lines = [line.strip() for line in script_text.splitlines() if line.strip()]

    # Topic from first header or line
    main_topic = "Educational Breakdown"
    for line in lines:
        if line.startswith("#"):
            main_topic = line.lstrip("#").strip()
            break

    # Extract hook (first spoken paragraph)
    hook = ""
    for line in lines:
        if not line.startswith("#") and not line.startswith("["):
            hook = line
            break

    # Extract scenes
    scenes = re.findall(r"\[(?:SCENE|VISUAL|B-ROLL):(?:\s*)(.*?)\]", script_text, flags=re.IGNORECASE)

    return {
        "topic": main_topic,
        "hook": hook,
        "scenes": scenes,
    }


def create_metadata(script_path: Path = DEFAULT_SCRIPT, output_path: Path = DEFAULT_OUTPUT) -> bool:
    if not script_path.exists():
        print(f"❌ Error: Script not found at {script_path}")
        return False

    script_text = script_path.read_text(encoding="utf-8")
    info = analyze_script(script_text)
    topic = info["topic"]
    hook = info["hook"]

    # Clean topic words for tag generation
    clean_words = re.findall(r"\b[A-Za-z]{4,}\b", f"{topic} {hook}".lower())
    keyword_set = list(dict.fromkeys(clean_words))[:8]
    clean_tag = re.sub(r"[^a-zA-Z0-9]", "", topic).lower()

    metadata = {
        "video_topic": topic,
        "title_options": [
            f"{topic} (Explained Simply)",
            f"The Truth About {topic}",
            f"{topic}: What You Need To Know",
            f"Why {topic} Matters More Than You Think",
        ],
        "description": (
            f"{hook}\n\n"
            f"In this video, we break down {topic} so you understand "
            f"how it works and why it matters.\n\n"
            f"🔔 Subscribe for more quick educational breakdowns!\n\n"
            f"#shorts #education #explained #{clean_tag}"
        ),
        "tags": [
            topic.lower(),
            f"what is {topic.lower()}",
            f"{topic.lower()} explained",
            "shorts",
            "educational video",
            "learn",
            *keyword_set,
        ],
        "thumbnail_concept": {
            "headline_text": topic.upper()[:24],
            "composition": f"High-contrast visual representing {topic} with vibrant colors and bold focal point.",
            "generation_prompt": f"Dramatic cinematic visual representing {topic}, clean modern lighting, high detail, vibrant contrast, 9:16 vertical ratio.",
        },
        "scenes_summary": info["scenes"],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"✅ YouTube Metadata saved to {output_path}")
    print(f"  • Recommended Title: \"{metadata['title_options'][0]}\"")
    print(f"  • Tags generated: {len(metadata['tags'])}")
    print(f"  • Thumbnail Prompt ready for image generation!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate YouTube metadata from script")
    parser.add_argument("--script", type=Path, default=DEFAULT_SCRIPT, help="Path to script")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output metadata JSON path")

    args = parser.parse_args()
    success = create_metadata(args.script, args.output)
    sys.exit(0 if success else 1)
