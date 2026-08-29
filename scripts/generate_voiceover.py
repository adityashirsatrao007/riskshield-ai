#!/usr/bin/env python3
"""
RiskShield AI — AI Voiceover Generator + Video Merger
Uses Edge-TTS (Microsoft AI voices) to generate natural voiceover,
then merges with the demo video using ffmpeg.
Usage: python scripts/generate_voiceover.py [--voice VOICE] [--list-voices]
Output: demo_videos/pitch_final.mp4
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VIDEOS_DIR = PROJECT_ROOT / "demo_videos"
AUDIO_DIR = VIDEOS_DIR / "audio_segments"

# ─── VOICEOVER SCRIPT (section, start_time, text) ───
# start_time = seconds from video start where this section begins
SECTIONS = [
    {
        "name": "01_problem",
        "start": 0,
        "text": (
            "Indian merchants lose over 1,800 crore rupees every year to payment fraud, "
            "chargebacks, and returns. Traditional rule-based systems are reactive — "
            "they catch fraud after the money is already gone. "
            "Merchants need a system that stops fraud before it happens, in real-time, at the point of payment. "
            "RiskShield AI solves this. Let me show you how it works."
        ),
    },
    {
        "name": "02_introduce",
        "start": 40,
        "text": (
            "RiskShield AI is a full-stack AI-powered fraud detection platform "
            "built for the Razorpay AI Buildathon. "
            "It's a complete system — a machine learning model trained on 284,000 real transactions, "
            "a FastAPI backend scoring every payment in under 1 millisecond, "
            "a React dashboard with real-time alerts, "
            "and full production monitoring with Grafana, Prometheus, and MLflow. "
            "The API has 12 endpoints — order creation, payment verification, webhook handling, "
            "transaction scoring, alert management, and analytics. "
            "Every endpoint is authenticated, PCI-compliant, and documented here in Swagger."
        ),
    },
    {
        "name": "03_demo",
        "start": 80,
        "text": (
            "Here's the live demo. This is what a customer sees — "
            "a merchant's checkout page selling a Premium Widget for 499 rupees. "
            "When the customer clicks Pay with Razorpay, three things happen automatically. "
            "First, the server creates a Razorpay order using the SDK — server-side, never exposed to the client. "
            "Second, the Razorpay checkout opens, the customer enters their card details and pays. "
            "Third — and this is where RiskShield comes in — "
            "Razorpay fires a webhook to our system. "
            "We verify the webhook signature using HMAC-SHA256, "
            "then instantly score the transaction through our ML model. "
            "The entire flow — from payment to risk score — takes less than 130 milliseconds. "
            "If the transaction is flagged, an alert is created automatically. "
            "The merchant never loses money to fraud."
        ),
    },
    {
        "name": "04_dashboard",
        "start": 140,
        "text": (
            "This is the merchant dashboard. Right now we're tracking 192 transactions. "
            "12 have been flagged as suspicious — that's a 6.3 percent fraud rate. "
            "The system has identified 83.75 lakh rupees in potential savings from prevented fraud. "
            "The fraud attempts timeline shows activity over the last 30 days. "
            "The risk distribution chart breaks down transactions by severity — low, medium, high, and critical. "
            "Below that, you can see the most recent alerts, each with a risk score "
            "and the specific features that triggered the flag. "
            "Every metric you see is updated in real-time. "
            "This isn't a mockup — this is live data flowing through the system right now."
        ),
    },
    {
        "name": "05_transactions",
        "start": 190,
        "text": (
            "The transactions page shows every payment scored by the system. "
            "Each row displays the transaction ID, amount, merchant, risk score, and risk level. "
            "You can see scores ranging from low-risk green to critical red. "
            "The system processes all 34 ML features for every transaction — "
            "amount patterns, time-of-day analysis, velocity checks, and behavioral signals — "
            "all in real-time."
        ),
    },
    {
        "name": "06_alerts",
        "start": 210,
        "text": (
            "The Alert Center is where merchants take action. "
            "We have 12 open critical alerts right now. "
            "Each alert shows the exact risk score — 88 percent, 87.4 percent, 87.1 percent — "
            "and the specific features that caused the flag. "
            "For example, this alert was triggered because V14 — "
            "a PCA component encoding transaction velocity — had an importance of 0.18. "
            "V10 contributed 0.13, and V17 contributed 0.09. "
            "This is full explainability — the merchant knows exactly why each transaction was flagged. "
            "Merchants can acknowledge, resolve, or dismiss each alert. "
            "Every action is logged in the audit trail for compliance."
        ),
    },
    {
        "name": "07_analytics",
        "start": 240,
        "text": (
            "The analytics page gives merchants deeper insights — "
            "risk distribution over time, fraud rate trends, and false positive tracking. "
            "This helps merchants tune their risk thresholds and understand their fraud patterns over time."
        ),
    },
    {
        "name": "08_grafana",
        "start": 255,
        "text": (
            "For production operations, we have a full Grafana monitoring dashboard with 9 panels. "
            "Total transactions: 6,090. Fraud rate: 31.5 percent. "
            "Average inference latency: 0.132 milliseconds. "
            "Drift detection is active — currently zero drift alerts, meaning the model is performing consistently. "
            "The stacked area chart shows predictions by risk level over time — "
            "critical in blue, high in yellow, low in green. "
            "You can see the distribution changing throughout the day "
            "as different transaction patterns emerge. "
            "This is production-grade observability. "
            "Every metric is scraped from the backend every 15 seconds via Prometheus."
        ),
    },
    {
        "name": "09_mlflow",
        "start": 285,
        "text": (
            "All model training is tracked in MLflow. "
            "Our production model — fraud detector version 2 — is a Random Forest with 300 trees, "
            "trained on 284,807 transactions. "
            "Key metrics: AUC-ROC of 0.982, F1 score of 0.747, "
            "precision of 0.66, recall of 0.86. "
            "Every parameter, metric, and artifact is versioned and reproducible."
        ),
    },
    {
        "name": "10_prometheus_closing",
        "start": 295,
        "text": (
            "Prometheus is scraping the backend every 15 seconds. "
            "The raw metrics endpoint exposes predictions, latency histograms, drift signals, and alert counts — "
            "everything an SRE team needs. "
            "RiskShield AI is defense-only — it stops fraud without blocking legitimate customers. "
            "It has full Razorpay integration with server-side order creation and HMAC-verified webhooks. "
            "It's explainable AI — every alert shows which features triggered the flag. "
            "And it's production-ready — Docker Compose, CI/CD, monitoring, alerting, "
            "all running locally in 10 containers. "
            "RiskShield AI — stopping fraud before it happens. Thank you."
        ),
    },
]

# Available voices (run with --list-voices to see all)
DEFAULT_VOICE = "en-US-GuyNeural"  # Professional male voice
FEMALE_VOICE = "en-US-JennyNeural"  # Professional female voice


async def list_voices():
    """List all available Edge-TTS voices."""
    import edge_tts
    voices = await edge_tts.list_voices()
    print("\nAvailable voices:\n")
    for v in voices:
        if v["Locale"].startswith("en-"):
            print(f"  {v['ShortName']:30s}  {v['Gender']:8s}  {v['Locale']}")
    print()


async def generate_segment(text, voice, output_path):
    """Generate a single audio segment."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    await communicate.save(str(output_path))


async def generate_voiceover(voice=DEFAULT_VOICE):
    """Generate all voiceover segments."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    print(f" Voice: {voice}")
    print(f" Segments: {len(SECTIONS)}")
    print()

    for i, section in enumerate(SECTIONS):
        out = AUDIO_DIR / f"{section['name']}.mp3"
        print(f"  [{i+1}/{len(SECTIONS)}] {section['name']}...", end=" ", flush=True)
        await generate_segment(section["text"], voice, out)
        size_kb = out.stat().st_size / 1024
        print(f"✓ ({size_kb:.0f} KB)")

    print(f"\n All segments saved to {AUDIO_DIR}/")
    return True


def merge_audio_segments():
    """Merge all audio segments into one continuous audio file with correct timing."""
    merged_audio = VIDEOS_DIR / "voiceover_full.wav"

    # Build ffmpeg filter to place each segment at its correct timestamp
    inputs = []
    filter_parts = []
    last_end = 0

    for i, section in enumerate(SECTIONS):
        seg_path = AUDIO_DIR / f"{section['name']}.mp3"
        if not seg_path.exists():
            print(f"  Missing: {seg_path}")
            continue
        inputs.extend(["-i", str(seg_path)])
        start_s = section["start"]
        filter_parts.append(f"[{i}:a]adelay={start_s * 1000}|{start_s * 1000}[s{i}]")

    # Mix all delayed segments
    mix_inputs = "".join(f"[s{i}]" for i in range(len(SECTIONS)))
    filter_parts.append(f"{mix_inputs}amix=inputs={len(SECTIONS)}:duration=longest:dropout_transition=0[out]")

    filter_str = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "1",
        str(merged_audio),
    ]

    print("\n Merging audio segments...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-500:]}")
        return None

    size_mb = merged_audio.stat().st_size / (1024 * 1024)
    print(f"  ✓ Merged audio: {merged_audio} ({size_mb:.1f} MB)")
    return merged_audio


def merge_audio_video(audio_path):
    """Merge voiceover audio with the demo video."""
    # Find the latest demo video
    video_files = list(VIDEOS_DIR.glob("page@*.webm"))
    if not video_files:
        print("  No demo video found. Run: python scripts/record_pitch.py")
        return None

    video_path = max(video_files, key=lambda f: f.stat().st_mtime)
    output_path = VIDEOS_DIR / "pitch_final.mp4"

    print(f"\n Merging audio + video...")
    print(f"  Video: {video_path.name}")
    print(f"  Audio: {audio_path.name}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-500:]}")
        return None

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n Final video: {output_path}")
    print(f"   Size: {size_mb:.1f} MB")
    print(f"   Duration: ~5 minutes with AI voiceover")
    return output_path


async def main():
    args = sys.argv[1:]

    if "--list-voices" in args:
        await list_voices()
        return

    voice = DEFAULT_VOICE
    if "--voice" in args:
        idx = args.index("--voice")
        if idx + 1 < len(args):
            voice = args[idx + 1]

    if "--female" in args:
        voice = FEMALE_VOICE

    # Step 1: Generate voiceover segments
    await generate_voiceover(voice)

    # Step 2: Merge segments with correct timing
    audio_path = merge_audio_segments()
    if not audio_path:
        return

    # Step 3: Merge audio + video
    final = merge_audio_video(audio_path)
    if final:
        print(f"\n Done! Play with: mpv {final}")
        print(f"   Or: vlc {final}")


if __name__ == "__main__":
    asyncio.run(main())
