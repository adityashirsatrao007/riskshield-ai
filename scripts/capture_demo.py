#!/usr/bin/env python3
"""
RiskShield AI - Automated Pitch Demo Capture
Uses Playwright to take screenshots and record video of the demo flow.
Usage: python scripts/capture_demo.py [--video] [--screenshots]
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "demo_screenshots"
VIDEOS_DIR = PROJECT_ROOT / "demo_videos"


async def capture_screenshots(headless=True):
    """Capture screenshots of all key pages for the pitch deck."""
    from playwright.async_api import async_playwright

    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    print(f" Screenshots will be saved to: {SCREENSHOTS_DIR}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()

        # 1. Backend Health
        print(" Capturing backend health...")
        await page.goto("http://localhost:8000/health", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "01_backend_health.png"), full_page=True)
        print("  ✓ 01_backend_health.png")

        # 2. Swagger API Docs
        print(" Capturing Swagger docs...")
        await page.goto("http://localhost:8000/docs", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "02_swagger_docs.png"), full_page=False)
        print("  ✓ 02_swagger_docs.png")

        # 3. Demo Checkout Page
        print(" Capturing demo checkout...")
        await page.goto("http://localhost:3000/demo.html", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "03_demo_checkout.png"), full_page=False)
        print("  ✓ 03_demo_checkout.png")

        # 4. Dashboard (main view) — need to set API key first
        print(" Capturing dashboard...")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        # Fill in the API key on the login screen
        api_key = "riskshield-admin-8KGMzLQdmvfiYcoQ3fTS_Q"
        await page.evaluate(f"localStorage.setItem('riskshield_api_key', '{api_key}')")
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "04_dashboard.png"), full_page=False)
        print("  ✓ 04_dashboard.png")

        # 5. Dashboard - scrolled to alerts
        print(" Capturing dashboard alerts...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "05_dashboard_alerts.png"), full_page=False)
        print("  ✓ 05_dashboard_alerts.png")

        # 6. Transactions page
        print(" Capturing transactions...")
        await page.goto("http://localhost:3000/transactions", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "06_transactions.png"), full_page=False)
        print("  ✓ 06_transactions.png")

        # 7. Alerts page
        print(" Capturing alerts center...")
        await page.goto("http://localhost:3000/alerts", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "07_alerts.png"), full_page=False)
        print("  ✓ 07_alerts.png")

        # 8. Analytics page
        print(" Capturing analytics...")
        await page.goto("http://localhost:3000/analytics", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "08_analytics.png"), full_page=False)
        print("  ✓ 08_analytics.png")

        # 9. Grafana Dashboard — log in first
        print(" Capturing Grafana...")
        await page.goto("http://localhost:3001/login", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.fill('input[name="user"]', "admin")
        await page.fill('input[name="password"]', "admin")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        # Navigate to dashboard after login
        await page.goto("http://localhost:3001/d/riskshield-fraud-dashboard/riskshield---fraud-monitoring?orgId=1", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "09_grafana.png"), full_page=False)
        print("  ✓ 09_grafana.png")

        # 10. Prometheus Metrics
        print(" Capturing Prometheus...")
        await page.goto("http://localhost:9090/graph", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "10_prometheus.png"), full_page=False)
        print("  ✓ 10_prometheus.png")

        # 11. MLflow
        print(" Capturing MLflow...")
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "11_mlflow.png"), full_page=False)
        print("  ✓ 11_mlflow.png")

        # 12. Prometheus Metrics endpoint (raw)
        print(" Capturing /metrics endpoint...")
        await page.goto("http://localhost:8000/metrics", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "12_metrics_endpoint.png"), full_page=True)
        print("  ✓ 12_metrics_endpoint.png")

        await browser.close()
        print(f"\n All screenshots saved to {SCREENSHOTS_DIR}/")


async def record_video():
    """Record a video of the full demo flow (useful for pitch video)."""
    from playwright.async_api import async_playwright

    VIDEOS_DIR.mkdir(exist_ok=True)
    print(f" Video will be saved to: {VIDEOS_DIR}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            record_video_dir=str(VIDEOS_DIR),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        # 1. Backend Health
        print(" Recording: Backend health...")
        await page.goto("http://localhost:8000/health", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 2. Swagger
        print(" Recording: Swagger docs...")
        await page.goto("http://localhost:8000/docs", wait_until="networkidle")
        await page.wait_for_timeout(4000)

        # 3. Demo checkout
        print(" Recording: Demo checkout...")
        await page.goto("http://localhost:3000/demo.html", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 4. Dashboard — set API key first
        print(" Recording: Dashboard...")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        api_key = "riskshield-admin-8KGMzLQdmvfiYcoQ3fTS_Q"
        await page.evaluate(f"localStorage.setItem('riskshield_api_key', '{api_key}')")
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(4000)

        # 5. Scroll down
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        # 6. Transactions
        print(" Recording: Transactions...")
        await page.goto("http://localhost:3000/transactions", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 7. Alerts
        print(" Recording: Alerts...")
        await page.goto("http://localhost:3000/alerts", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 8. Analytics
        print(" Recording: Analytics...")
        await page.goto("http://localhost:3000/analytics", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 9. Grafana — log in first
        print(" Recording: Grafana...")
        await page.goto("http://localhost:3001/login", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.fill('input[name="user"]', "admin")
        await page.fill('input[name="password"]', "admin")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        await page.goto(
            "http://localhost:3001/d/riskshield-fraud-dashboard/riskshield---fraud-monitoring?orgId=1",
            wait_until="networkidle",
        )
        await page.wait_for_timeout(5000)

        # 10. Prometheus
        print(" Recording: Prometheus...")
        await page.goto("http://localhost:9090/graph", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 11. MLflow
        print(" Recording: MLflow...")
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 12. Metrics endpoint
        print(" Recording: Metrics endpoint...")
        await page.goto("http://localhost:8000/metrics", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Close to finalize video
        await context.close()
        await browser.close()

        # Find the recorded video
        video_files = list(VIDEOS_DIR.glob("*.webm"))
        if video_files:
            print(f"\n Video recorded: {video_files[0]}")
            print(f"   Duration: ~60 seconds (full demo flow)")
        else:
            print("\n  No video file found. Check if recording was enabled.")


async def main():
    args = sys.argv[1:]
    do_video = "--video" in args
    do_screenshots = "--screenshots" in args or not args

    if do_screenshots:
        await capture_screenshots(headless=True)
    if do_video:
        await record_video()


if __name__ == "__main__":
    asyncio.run(main())
