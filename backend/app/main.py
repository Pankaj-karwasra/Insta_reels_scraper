from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os
from pydantic import BaseModel

# Use an alias to resolve the function name mismatch
from .scraper import scrape_user_profile as scrape_username
from models import ScrapeResponse
from cache import set_cached, get_cached
from logging_config import configure_logging

from dotenv import load_dotenv
load_dotenv()

configure_logging()
logger = logging.getLogger("backend")

app = FastAPI(title="Fast Instagram Reels Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for the POST request body
class ScrapeRequest(BaseModel):
    username: str
    limit: int = 10

async def perform_scrape(username: str, limit: int) -> ScrapeResponse:
    """Shared scraping logic to avoid code duplication."""
    logger.info(f"Scraping request received for user: {username} with limit: {limit}")

    # Check cache first
    cache_key = f"{username}:{limit}"
    cached_data = get_cached(cache_key)
    if cached_data:
        logger.info(f"Serving from cache for user: {username}")
        return cached_data

    # Scrape data if not in cache
    try:
        reels = await scrape_username(username, limit=limit)
        scrape_response = ScrapeResponse(
            username=username,
            scraped_at=datetime.now(),
            count=len(reels),
            reels=reels
        )
        set_cached(cache_key, scrape_response)
        return scrape_response
    except ValueError as e:
        if "profile_not_accessible" in str(e):
            raise HTTPException(status_code=404, detail="User profile not found or is private.")
        logger.error(f"Scraping failed for {username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during scraping.")
    except Exception as e:
        logger.error(f"An unexpected error occurred for {username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")


@app.get("/scrape", response_model=ScrapeResponse)
async def scrape_get(
    username: str = Query(..., description="The Instagram username to scrape."),
    limit: int = Query(20, description="The maximum number of reels to return."),
):
    return await perform_scrape(username, limit)


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_post(request: ScrapeRequest = Body(...)):
    return await perform_scrape(request.username, request.limit)

@app.get("/")
def read_root():
    return {"status": "API is running"}