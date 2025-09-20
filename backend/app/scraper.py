import os
import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
import json
from models import Reel

logger = logging.getLogger("scraper")

MAX_PAGES = int(os.getenv("MAX_CONCURRENT_PAGES", "6"))
HEADLESS_MODE = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

# ✅ CORRECTED CODE: Go up one directory level to find auth_state.json
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_script_dir)
# Join the parent directory with the filename
storage_state = os.path.join(parent_dir, "auth_state.json")

# ... rest of your code remains the same
# async def extract_reels_from_profile...
# async def scrape_user_profile...

async def extract_reels_from_profile(page: Page, limit: Optional[int] = None) -> List[Reel]:
    reels: List[Reel] = []
    found_hrefs = set()

    try:
        await page.wait_for_selector("main[role='main']", timeout=20000)
    except PlaywrightTimeoutError:
        logger.error("Timeout waiting for main content. Profile might be unavailable or private.")
        return []

    last_count = -1
    max_scrolls = 10  # Increased scrolls to find more reels
    scroll_count = 0
    while len(found_hrefs) < limit and scroll_count < max_scrolls:
        anchors = await page.query_selector_all("main[role='main'] div a[href^='/reel/']")
        if not anchors:
            anchors = await page.query_selector_all("article a[href^='/reel/']")
        
        current_hrefs = {await a.get_attribute('href') for a in anchors if await a.get_attribute('href')}
        new_hrefs = current_hrefs - found_hrefs
        found_hrefs.update(new_hrefs)
        
        logger.info(f"Scroll {scroll_count + 1}: Found {len(new_hrefs)} new reel links. Total unique: {len(found_hrefs)}")
        
        if len(found_hrefs) == last_count:
            break

        last_count = len(found_hrefs)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2500)
        scroll_count += 1

    hrefs = list(found_hrefs)
    if limit:
        hrefs = hrefs[:limit]

    logger.info(f"Final count of reel links to process: {len(hrefs)}")

    sem = asyncio.Semaphore(MAX_PAGES)

    async def fetch_reel(href: str) -> Optional[Reel]:
        async with sem:
            context = page.context
            new_page = await context.new_page()
            try:
                url = f"https://www.instagram.com{href}"
                await new_page.goto(url, wait_until='domcontentloaded', timeout=15000)
                await new_page.wait_for_timeout(1000)

                id_value = href.strip('/').split('/')[-1]
                caption_text, video_url, thumb, posted_at, views, likes, comments = (None,) * 7
                
                scripts = await new_page.query_selector_all('script[type="application/ld+json"]')
                for s in scripts:
                    try:
                        data = json.loads(await s.inner_text())
                        if data.get('@type') in ('VideoObject', 'MediaObject'):
                            caption_text = data.get('description')
                            video_url = data.get('contentUrl')
                            thumb = data.get('thumbnailUrl')
                            if data.get('uploadDate'):
                                posted_at = datetime.fromisoformat(data['uploadDate'].replace('Z', '+00:00'))
                            
                            for interaction in data.get('interactionStatistic', []):
                                if interaction.get('interactionType') == 'http://schema.org/LikeAction':
                                    likes = interaction.get('userInteractionCount')
                                elif interaction.get('interactionType') == 'http://schema.org/CommentAction':
                                    comments = interaction.get('userInteractionCount')
                                elif interaction.get('interactionType') == 'http://schema.org/ViewAction':
                                    views = interaction.get('userInteractionCount')
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue

                # Fallbacks if JSON data is incomplete
                if not video_url:
                    og_video = await new_page.query_selector("meta[property='og:video']")
                    if og_video: 
                        video_url = await og_video.get_attribute('content')
                if not thumb:
                    og_image = await new_page.query_selector("meta[property='og:image']")
                    if og_image: 
                        thumb = await og_image.get_attribute('content')
                if not caption_text:
                    caption_el = await new_page.query_selector("meta[property='og:title']")
                    if caption_el: 
                        caption_text = (await caption_el.get_attribute('content'))

                if not video_url:
                    logger.warning(f"Could not find video URL for reel: {url}")
                    return None
                
                return Reel(
                    id=id_value,
                    reel_url=url,
                    video_url=video_url,
                    thumbnail_url=thumb,
                    caption=caption_text,
                    posted_at=posted_at,
                    views=views,
                    likes=likes,
                    comments=comments
                )
            except Exception as e:
                logger.exception(f"Error fetching reel {href}: {e}")
                return None
            finally:
                await new_page.close()

    tasks = [fetch_reel(h) for h in hrefs]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r]


async def scrape_user_profile(username: str, limit: Optional[int] = 20):
    logger.info(f"Starting playwright for user: {username}. Headless: {HEADLESS_MODE}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS_MODE,
            args=["--no-sandbox"]
        )
        ctx = await browser.new_context(
            storage_state=storage_state , # ✅ load your saved login session
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()

        profile_url = f"https://www.instagram.com/{username}/reels/"
        try:
            await page.goto(profile_url, wait_until='networkidle', timeout=30000)
        except PlaywrightTimeoutError:
            logger.warning(
                f"Timeout on initial load for {username}/reels/. Trying profile root."
            )
            profile_url = f"https://www.instagram.com/{username}/"
            await page.goto(profile_url, wait_until='networkidle', timeout=30000)

        # --- 🔎 DEBUG BLOCK START ---
        content = await page.content()
        debug_html = f"debug_{username}.html"
        debug_png = f"debug_{username}.png"

        with open(debug_html, "w", encoding="utf-8") as f:
            f.write(content)
        await page.screenshot(path=debug_png, full_page=True)

        anchor_count = await page.evaluate(
            "() => document.querySelectorAll('a[href*=\"/reel/\"]').length"
        )
        logger.info(f"Anchor count (evaluate): {anchor_count}")

        body_text = await page.evaluate("() => document.body.innerText")
        if "Log in" in body_text or "Log in to see" in body_text:
            logger.warning("⚠️ Login wall probably present on the profile page.")
        # --- 🔎 DEBUG BLOCK END ---

        if (
            "Sorry, this page isn't available" in content
            or "This Account is Private" in content
        ):
            await browser.close()
            raise ValueError("profile_not_accessible")

        reels = await extract_reels_from_profile(page, limit=limit)
        await browser.close()
        return reels
