#!/usr/bin/env python3
"""
Fix voiceover: concatenate segments with proper silence gaps,
then merge with video. Simpler than adelay+amix.
"""
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VIDEOS_DIR = PROJECT_ROOT / "demo_videos"
AUDIO_DIR = VIDEOS_DIR / "audio_segments"

# Section start times (seconds from video start)
SECTIONS = [
    ("01_problem", 0),
    ("02_introduce", 40),
    ("03_demo", 80),
    ("04_dashboard", 140),
    ("05_transactions", 190),
    ("06_alerts", 210),
    ("07_analytics", 240),
    ("08_grafana", 255),
    ("09_mlflow", 285),
    ("10_prometheus_closing", 295),
]


def get_duration(path):
    """Get duration of an audio file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def build_voiceover():
    """Build one continuous voiceover WAV with correct timing."""
    output = VIDEOS_DIR / "voiceover_full.wav"

    # Build a concat file with silence gaps
    parts = []
    concat_list = VIDEOS_DIR / "concat.txt"
    silence_dir = VIDEOS_DIR / "silence"
    silence_dir.mkdir(exist_ok=True)

    # Generate silence segments for gaps between sections
    for i in range(len(SECTIONS)):
        name, start = SECTIONS[i]
        seg_path = AUDIO_DIR / f"{name}.mp3"
        if not seg_path.exists():
            print(f"  Missing: {seg_path}")
            continue

        seg_duration = get_duration(seg_path)

        # Calculate silence needed before this segment
        if i == 0:
            silence_before = start  # usually 0
        else:
            prev_name, prev_start = SECTIONS[i - 1]
            prev_seg = AUDIO_DIR / f"{prev_name}.mp3"
            prev_duration = get_duration(prev_seg)
            silence_before = start - (prev_start + prev_duration)

        # Add silence gap if needed
        if silence_before > 0.1:
            silence_path = silence_dir / f"silence_{i}.wav"
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"anullsrc=r=44100:cl=mono:d={silence_before}",
                str(silence_path)
            ], capture_output=True)
            parts.append(silence_path)

        # Convert segment to WAV and append
        seg_wav = silence_dir / f"{name}.wav"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(seg_path),
            "-ar", "44100", "-ac", "1", str(seg_wav)
        ], capture_output=True)
        parts.append(seg_wav)
        print(f"  {name}: silence={silence_before:.1f}s + speech={seg_duration:.1f}s")

    # Build concat file
    with open(concat_list, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")

    # Concatenate all parts
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-ar", "44100", "-ac", "1",
        str(output)
    ], capture_output=True)

    # Clean up temp files
    for p in parts:
        p.unlink(missing_ok=True)
    concat_list.unlink(missing_ok=True)
    silence_dir.rmdir()

    size_mb = output.stat().st_size / (1024 * 1024)
    dur = get_duration(output)
    print(f"\n Voiceover: {output.name} ({size_mb:.1f} MB, {dur:.0f}s)")
    return output


def merge_with_video(audio_path):
    """Merge voiceover with the demo video."""
    # Find the latest demo video
    video_files = list(VIDEOS_DIR.glob("page@*.webm"))
    video_path = max(video_files, key=lambda f: f.stat().st_mtime)
    output = VIDEOS_DIR / "pitch_final.mp4"

    print(f"\n Merging: {video_path.name} + voiceover")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr[-500:]}")
        return None

    dur = get_duration(output)
    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"\n Final: {output}")
    print(f"   Size: {size_mb:.1f} MB")
    print(f"   Duration: {int(dur//60)}m {int(dur%60)}s")
    print(f"\n Play: mpv {output}")
    return output


if __name__ == "__main__":
    print("=== Building voiceover ===\n")
    audio = build_voiceover()
    merge_with_video(audio)
