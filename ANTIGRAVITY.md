# Faceless YouTube Content Engine (Antigravity Edition)

An automated CLI and agent-driven video production pipeline that transforms a topic or script into a complete 1080p Full HD narrated YouTube video with synchronized subtitles, dynamic camera motion (Ken Burns effect), and YouTube SEO metadata.

---

## 📁 Project Architecture

```
├── scripts/
│   └── script.md            # Your video script with [SCENE: ...] visual markers
├── audio/
│   ├── voiceover.mp3        # High-definition neural AI narration (edge-tts)
│   ├── voiceover.srt        # Synchronized SubRip captions
│   └── spoken_text.txt      # Extracted clean spoken narration
├── images/
│   ├── scene_01.png         # High-res 16:9 images for each scene
│   └── ...
├── clips/
│   ├── clip_01.mp4          # 1080p animated clips with cinematic camera motion
│   └── ...
├── output/
│   ├── final_video.mp4      # Finished 1080p MP4 ready for YouTube
│   └── metadata.json        # SEO title options, description, tags, thumbnail prompt
├── generate_voice.py        # Voiceover & SRT generator (edge-tts)
├── generate_clips.py        # Ken Burns camera animator (FFmpeg)
├── assemble.py              # FFmpeg video, audio & subtitle compositor
├── generate_metadata.py     # YouTube SEO metadata generator
└── engine.py                # Master CLI orchestrator
```

---

## ⚡ Quick Start

### 1. Check Engine Health
```bash
python3 engine.py --status
```

### 2. Write Your Script
Save your script into `scripts/script.md`. Structure it with:
- A punchy 5-second **Hook**
- 3 to 4 explanatory **Sections**
- A closing **Call to Action (CTA)**
- `[SCENE: visual description]` markers before each section

### 3. Run the Full Pipeline
```bash
python3 engine.py --run-all
```

---

## 🎙️ Neural Voices (`edge-tts`)

The voice generator uses Microsoft Edge's neural TTS (100% free, zero API keys, no quotas):

| Voice Name | Gender / Accent | Style |
| :--- | :--- | :--- |
| `en-US-GuyNeural` *(Default)* | Male (US) | Natural, documentary, engaging |
| `en-US-AriaNeural` | Female (US) | Crisp, expressive, educational |
| `en-US-ChristopherNeural` | Male (US) | Serious, authoritative, deep |
| `en-GB-RyanNeural` | Male (UK) | Sophisticated, BBC-style documentary |
| `en-GB-SoniaNeural` | Female (UK) | Clear, polished, narrative |

To change voice or speed:
```bash
python3 engine.py --voice --voice-name "en-GB-RyanNeural"
# Or in generate_voice.py directly:
python3 generate_voice.py --voice "en-US-AriaNeural" --rate "+10%"
```

---

## 🎥 Camera Motion Filters (Ken Burns)

`generate_clips.py` cycles through 4 cinematic camera movements for each scene:
1. **Zoom In**: Draws viewer focus toward center details.
2. **Zoom Out**: Reveals the broader environment.
3. **Pan Left to Right**: Sweeping horizontal motion.
4. **Pan Right to Left**: Dynamic counter-panning.

All clips are rendered to standard YouTube 1920x1080 H.264 at 25 fps.

---

## 🛠️ Step-by-Step Commands

```bash
# Generate voice & subtitles only
python3 engine.py --voice

# Render clips only
python3 engine.py --clips

# Re-render clips in landscape mode (16:9)
python3 generate_clips.py --landscape

# Assemble video with custom subtitle font size
python3 engine.py --assemble --font-size 28

# Generate SEO metadata
python3 engine.py --metadata

# Clean build artifacts for a new video
python3 engine.py --clean
```
