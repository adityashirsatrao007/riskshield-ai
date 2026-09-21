#!/usr/bin/env python3
"""
RiskShield AI — Full 5-Minute Pitch Video Recorder (v2)
Records a continuous browser session with 5 minutes of timed sections.
Usage: python scripts/record_pitch.py
Output: demo_videos/pitch_demo.webm (~5 min)
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
VIDEOS_DIR = PROJECT_ROOT / "demo_videos"
API_KEY = "riskshield-admin-8KGMzLQdmvfiYcoQ3fTS_Q"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin"


async def hold(page, seconds, label=""):
    """Wait for a given duration, printing progress."""
    if label:
        print(f"   waiting {seconds}s — {label}")
    await page.wait_for_timeout(seconds * 1000)


async def scroll_and_hold(page, y, hold_s, label=""):
    """Scroll to y position and hold."""
    await page.evaluate(f"window.scrollTo(0, {y})")
    await hold(page, hold_s, label)


async def record():
    VIDEOS_DIR.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            record_video_dir=str(VIDEOS_DIR),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        # Set API key up front
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.evaluate(f"localStorage.setItem('riskshield_api_key', '{API_KEY}')")

        # ══════════════════════════════════════════════════════════════
        # SECTION 1: Problem Statement (0:00 — 0:40)  [40s]
        # ══════════════════════════════════════════════════════════════
        print("[0:00] Section 1: Problem Statement")
        await page.goto("http://localhost:8000/health", wait_until="networkidle")
        await hold(page, 8, "showing backend health — intro voiceover")
        await scroll_and_hold(page, 200, 10, "scrolling health details")
        await scroll_and_hold(page, 0, 12, "back to top — explain ₹1,800Cr fraud problem")
        await hold(page, 10, "holding — problem statement closing")

        # ══════════════════════════════════════════════════════════════
        # SECTION 2: Introduce RiskShield (0:40 — 1:20)  [40s]
        # ══════════════════════════════════════════════════════════════
        print("[0:40] Section 2: Introduce RiskShield")
        await page.goto("http://localhost:8000/docs", wait_until="networkidle")
        await hold(page, 8, "Swagger docs loaded — introduce the platform")
        for y in range(0, 1200, 300):
            await scroll_and_hold(page, y, 6, f"scrolling to API section {y}")
        await hold(page, 10, "holding — explain 34 ML features, Razorpay integration")

        # ══════════════════════════════════════════════════════════════
        # SECTION 3: Live Demo — Razorpay (1:20 — 2:20)  [60s]
        # ══════════════════════════════════════════════════════════════
        print("[1:20] Section 3: Live Demo — Razorpay Checkout")
        await page.goto("http://localhost:3000/demo.html", wait_until="networkidle")
        await hold(page, 10, "checkout page loaded — explain server-side order creation")
        # hover on pay button
        pay_btn = page.locator("text=Pay ₹499 with Razorpay")
        if await pay_btn.count() > 0:
            await pay_btn.first.hover()
            await hold(page, 8, "hovering pay button — explain Razorpay SDK")
        await scroll_and_hold(page, 400, 10, "scrolling to test card info")
        await scroll_and_hold(page, 0, 12, "back to top — explain HMAC-SHA256 verification")
        await hold(page, 10, "holding — explain webhook → RiskShield scoring flow")
        await hold(page, 10, "holding — explain real-time fraud detection on capture")

        # ══════════════════════════════════════════════════════════════
        # SECTION 4: Dashboard (2:20 — 3:10)  [50s]
        # ══════════════════════════════════════════════════════════════
        print("[2:20] Section 4: Dashboard")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await hold(page, 12, "dashboard loaded — explain stat cards: 192 txns, 12 flagged")
        await scroll_and_hold(page, 300, 10, "scrolling to charts — fraud timeline")
        await scroll_and_hold(page, 450, 10, "risk distribution bar chart")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await hold(page, 12, "scrolled to alerts — explain recent alerts")
        await hold(page, 8, "holding — explain fraud rate, potential savings")

        # ══════════════════════════════════════════════════════════════
        # SECTION 5: Transactions (3:10 — 3:30)  [20s]
        # ══════════════════════════════════════════════════════════════
        print("[3:10] Section 5: Transactions")
        await page.goto("http://localhost:3000/transactions", wait_until="networkidle")
        await hold(page, 8, "transactions list — explain 34-feature scoring")
        await scroll_and_hold(page, 400, 6, "scrolling transaction rows")
        await scroll_and_hold(page, 800, 6, "more rows — real-time risk scores visible")

        # ══════════════════════════════════════════════════════════════
        # SECTION 6: Alert Center (3:30 — 4:00)  [30s]
        # ══════════════════════════════════════════════════════════════
        print("[3:30] Section 6: Alert Center")
        await page.goto("http://localhost:3000/alerts", wait_until="networkidle")
        await hold(page, 10, "alert center — 12 open alerts, critical risk scores")
        await scroll_and_hold(page, 400, 10, "scrolling — explain V14, V10, V17 feature importances")
        await hold(page, 10, "holding — explain explainability, acknowledge/resolve workflow")

        # ══════════════════════════════════════════════════════════════
        # SECTION 7: Analytics (4:00 — 4:15)  [15s]
        # ══════════════════════════════════════════════════════════════
        print("[4:00] Section 7: Analytics")
        await page.goto("http://localhost:3000/analytics", wait_until="networkidle")
        await hold(page, 8, "analytics page — risk distribution, fraud trends")
        await scroll_and_hold(page, 400, 7, "scrolling charts")

        # ══════════════════════════════════════════════════════════════
        # SECTION 8: Grafana Monitoring (4:15 — 4:45)  [30s]
        # ══════════════════════════════════════════════════════════════
        print("[4:15] Section 8: Grafana Monitoring")
        await page.goto("http://localhost:3001/login", wait_until="networkidle")
        await hold(page, 2, "grafana login page")
        await page.fill('input[name="user"]', GRAFANA_USER)
        await page.fill('input[name="password"]', GRAFANA_PASS)
        await page.click('button[type="submit"]')
        await hold(page, 3, "logging in...")
        await page.goto(
            "http://localhost:3001/d/riskshield-fraud-dashboard/riskshield---fraud-monitoring?orgId=1",
            wait_until="networkidle",
        )
        await hold(page, 12, "grafana dashboard — 9 panels, 6.09K predictions, 31.5% fraud rate")
        await scroll_and_hold(page, 300, 10, "scrolling — stacked risk chart, drift detection, latency")

        # ══════════════════════════════════════════════════════════════
        # SECTION 9: MLflow (4:45 — 4:55)  [10s]
        # ══════════════════════════════════════════════════════════════
        print("[4:45] Section 9: MLflow")
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await hold(page, 5, "mlflow — experiment tracking")
        exp = page.locator("text=RiskShield Fraud Detection v2")
        if await exp.count() > 0:
            await exp.first.click()
            await hold(page, 5, "model v2 run — AUC-ROC 0.982, F1 0.747")

        # ══════════════════════════════════════════════════════════════
        # SECTION 10: Prometheus + Metrics (4:55 — 5:00)  [5s]
        # ══════════════════════════════════════════════════════════════
        print("[4:55] Section 10: Prometheus + Metrics")
        await page.goto("http://localhost:9090/targets", wait_until="networkidle")
        await hold(page, 3, "prometheus targets — scraping every 15s")
        await page.goto("http://localhost:8000/metrics", wait_until="networkidle")
        await hold(page, 3, "raw metrics endpoint")

        # ══════════════════════════════════════════════════════════════
        # SECTION 11: Closing (5:00 — 5:10)  [10s]
        # ══════════════════════════════════════════════════════════════
        print("[5:00] Section 11: Closing")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await hold(page, 3, "back to dashboard")
        await page.evaluate("window.scrollTo(0, 0)")
        await hold(page, 7, "closing statement — defense-only, explainable, production-ready")

        # Finalize
        await context.close()
        await browser.close()

        video_files = list(VIDEOS_DIR.glob("*.webm"))
        if video_files:
            latest = max(video_files, key=lambda f: f.stat().st_mtime)
            size_mb = latest.stat().st_size / (1024 * 1024)
            print(f"\n Video: {latest}")
            print(f"   Size: {size_mb:.1f} MB")
            print(f"   Duration: ~5 minutes 10 seconds")
        else:
            print("\n  No video file found.")


if __name__ == "__main__":
    asyncio.run(record())
