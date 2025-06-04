"""Scrape Metacritic must-play games and save them to CSV."""

from __future__ import annotations

import argparse
import asyncio
import csv
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional
import re

import requests
from bs4 import BeautifulSoup
import aiohttp


HEADERS = {"User-Agent": "Mozilla/5.0"}


@dataclass
class Game:
    """Representation of a must-play game scraped from Metacritic."""

    rank: Optional[str]
    title: Optional[str]
    release_date: Optional[datetime]
    metascore: Optional[int]
    url: Optional[str] = None
    critic_reviews: Optional[int] = None


def sort_games_by_rank(games: Iterable[Game]) -> List[Game]:
    """Return games ordered numerically by their rank."""
    def rank_key(game: Game) -> int:
        if game.rank and game.rank.rstrip('.').isdigit():
            return int(game.rank.rstrip('.'))
        return 0

    return sorted(games, key=rank_key)


def fetch_page(url: str, *, timeout: int = 10) -> Optional[str]:
    """Return page HTML if the request succeeds, otherwise ``None``."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return resp.text
        print(f"⚠️ Request for {url} returned status {resp.status_code}.")
    except requests.RequestException as exc:
        print(f"⚠️ Request for {url} failed: {exc}")
    return None


async def fetch_page_async(session: aiohttp.ClientSession, url: str, *, timeout: int = 10) -> Optional[str]:
    """Asynchronously return page HTML if the request succeeds."""
    try:
        async with session.get(url, timeout=timeout) as resp:
            if resp.status == 200:
                return await resp.text()
            print(f"⚠️ Request for {url} returned status {resp.status}.")
    except aiohttp.ClientError as exc:
        print(f"⚠️ Request for {url} failed: {exc}")
    return None


def parse_games(html: str) -> List[Game]:
    """Extract must-play games from HTML and return them as ``Game`` objects."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("a.c-finderProductCard_container")

    games: List[Game] = []
    for card in cards:
        if card.select_one('img[alt="must-play"]') is None:
            continue

        title_elem = card.select_one(
            ".c-finderProductCard_titleHeading span:nth-of-type(2)"
        )
        rank_elem = card.select_one(
            ".c-finderProductCard_titleHeading span:nth-of-type(1)"
        )
        date_elem = card.select_one(
            ".c-finderProductCard_meta span:nth-of-type(1)"
        )
        metascore_elem = card.select_one(".c-siteReviewScore span")
        url = card.get("href")
        if url and url.startswith("/"):
            url = "https://www.metacritic.com" + url

        date: Optional[datetime] = None
        if date_elem and date_elem.text.strip():
            try:
                date = datetime.strptime(date_elem.text.strip(), "%b %d, %Y")
            except ValueError:
                pass

        game = Game(
            rank=rank_elem.text.strip() if rank_elem else None,
            title=title_elem.text.strip() if title_elem else None,
            release_date=date,
            metascore=int(metascore_elem.text.strip()) if metascore_elem else None,
            url=url,
        )
        games.append(game)

    return games


def parse_critic_reviews(html: str) -> Optional[int]:
    """Return critic review count parsed from a game page."""
    soup = BeautifulSoup(html, "html.parser")
    elem = soup.select_one('a[data-testid="critic-path"] span')
    if elem:
        match = re.search(r"(\d+)\s+Critic", elem.get_text(strip=True))
        if match:
            return int(match.group(1))
    return None


def fetch_critic_reviews(game: Game, *, delay: float = 1.0) -> None:
    """Populate ``game.critic_reviews`` by scraping its page."""
    if not game.url:
        return
    html = fetch_page(game.url)
    if html:
        game.critic_reviews = parse_critic_reviews(html)
    time.sleep(random.uniform(delay, delay + 1))


async def fetch_critic_reviews_async(
    session: aiohttp.ClientSession, game: Game, *, delay: float = 1.0
) -> None:
    """Asynchronously populate ``game.critic_reviews`` from its page."""
    if not game.url:
        return
    html = await fetch_page_async(session, game.url)
    if html:
        game.critic_reviews = parse_critic_reviews(html)
    await asyncio.sleep(random.uniform(delay, delay + 1))


def fetch_reviews_for_games(games: Iterable[Game], *, delay: float = 1.0) -> None:
    """Sequentially populate critic reviews for each game."""
    for game in games:
        fetch_critic_reviews(game, delay=delay)


async def fetch_reviews_for_games_async(
    games: Iterable[Game], *, delay: float = 1.0, concurrency: int = 5
) -> None:
    """Asynchronously populate critic reviews for each game."""
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        tasks = [fetch_critic_reviews_async(session, game, delay=delay) for game in games]
        await asyncio.gather(*tasks)


def scrape_games(start: int, end: int, *, delay: float = 1.0) -> List[Game]:
    """Scrape games between ``start`` and ``end`` pages inclusive."""
    print("🔎 Starting scraping Metacritic must-play games...\n")
    all_games: List[Game] = []

    for page in range(start, end + 1):
        print(f"🔎 Accessing page {page}...")
        url = (
            "https://www.metacritic.com/browse/game/?releaseYearMin=1958"
            f"&releaseYearMax=2025&page={page}"
        )

        html = fetch_page(url)
        if html is None:
            print("⚠️ Skipping page due to request failure.")
            continue

        games = parse_games(html)
        if not games:
            print("⚠️ No game cards found. Stopping.")
            break

        all_games.extend(games)

        wait = random.uniform(delay, delay + 1)
        time.sleep(wait)

    print("\n✅ Scraping completed.\n")
    return all_games


async def scrape_games_async(
    start: int,
    end: int,
    *,
    delay: float = 1.0,
    concurrency: int = 5,
) -> List[Game]:
    """Asynchronously scrape games between ``start`` and ``end`` pages."""
    print("🔎 Starting scraping Metacritic must-play games...\n")
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        tasks = []
        for page in range(start, end + 1):
            url = (
                "https://www.metacritic.com/browse/game/?releaseYearMin=1958"
                f"&releaseYearMax=2025&page={page}"
            )
            tasks.append(fetch_page_async(session, url))
            await asyncio.sleep(random.uniform(delay, delay + 1))

        pages = await asyncio.gather(*tasks)

    all_games: List[Game] = []
    for html in pages:
        if html is None:
            print("⚠️ Skipping page due to request failure.")
            continue
        games = parse_games(html)
        if not games:
            print("⚠️ No game cards found. Stopping.")
            break
        all_games.extend(games)

    print("\n✅ Scraping completed.\n")
    return all_games


def save_csv(games: Iterable[Game], filename: str) -> None:
    """Write scraped games to ``filename``."""
    with open(filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "rank",
                "title",
                "release_date",
                "metascore",
                "critic_reviews",
            ],
        )
        writer.writeheader()
        for game in games:
            writer.writerow(
                {
                    "rank": game.rank,
                    "title": game.title,
                    "release_date": game.release_date.strftime("%Y-%m-%d")
                    if game.release_date
                    else None,
                    "metascore": game.metascore,
                    "critic_reviews": game.critic_reviews,
                }
            )


def parse_args() -> argparse.Namespace:
    """Return parsed command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="First page to scrape (inclusive).",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=16,
        help="Last page to scrape (inclusive).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=datetime.today().strftime("metacritic_must_play_games_%Y-%m-%d.csv"),
        help="Output CSV filename.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Base delay between requests in seconds.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of concurrent requests (1 = sequential).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.concurrency > 1:
        games = asyncio.run(
            scrape_games_async(
                args.start,
                args.end,
                delay=args.delay,
                concurrency=args.concurrency,
            )
        )
    else:
        games = scrape_games(args.start, args.end, delay=args.delay)

    if args.concurrency > 1:
        asyncio.run(
            fetch_reviews_for_games_async(
                games, delay=args.delay, concurrency=args.concurrency
            )
        )
    else:
        fetch_reviews_for_games(games, delay=args.delay)

    games = sort_games_by_rank(games)
    save_csv(games, args.output)
    print(f"📁 CSV file saved: {args.output}")


if __name__ == "__main__":
    main()
