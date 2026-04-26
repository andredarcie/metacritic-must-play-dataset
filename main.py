"""Scrape Metacritic must-play games (listagem apenas) — agora com log detalhado."""

from __future__ import annotations

import argparse
import asyncio
import csv
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import aiohttp
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


@dataclass
class Game:
    rank: Optional[str]
    title: Optional[str]
    release_date: Optional[datetime]
    metascore: Optional[int]
    url: Optional[str] = None


def sort_games_by_rank(games: Iterable["Game"]) -> List["Game"]:
    return sorted(
        games,
        key=lambda g: (
            int(g.rank.rstrip(".")) if g.rank and g.rank.rstrip(".").isdigit() else 0
        ),
    )


def fetch_page(url: str, timeout: int = 10) -> Optional[str]:
    """Baixa página e apresenta log de tempo e tamanho."""
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        elapsed = time.time() - start
        kb = len(resp.content) / 1024
        if resp.status_code == 200:
            print(f"⬇️  {url} — OK {elapsed:.2f}s • {kb:.1f} KB")
            return resp.text
        print(f"⚠️  {url} — HTTP {resp.status_code} {elapsed:.2f}s")
    except requests.RequestException as exc:
        print(f"⚠️  {url} — ERRO {exc}")
    return None


async def fetch_page_async(
    session: aiohttp.ClientSession,
    url: str,
    delay: float,
    timeout: int = 10,
    retries: int = 3,
) -> Optional[str]:
    """Async version of fetch_page using aiohttp with exponential backoff on 429/5xx."""
    for attempt in range(1, retries + 1):
        start = time.time()
        try:
            async with session.get(url, headers=HEADERS, timeout=timeout) as resp:
                text = await resp.text()
                elapsed = time.time() - start
                kb = len(text.encode()) / 1024
                if resp.status == 200:
                    print(f"⬇️  {url} — OK {elapsed:.2f}s • {kb:.1f} KB")
                    await asyncio.sleep(random.uniform(delay, delay + 1))
                    return text
                if resp.status in (429, 500, 502, 503, 504) and attempt < retries:
                    wait = 2 ** attempt + random.uniform(0, 1)
                    print(f"⚠️  {url} — HTTP {resp.status}, tentativa {attempt}/{retries}, aguardando {wait:.1f}s")
                    await asyncio.sleep(wait)
                    continue
                print(f"⚠️  {url} — HTTP {resp.status} {elapsed:.2f}s")
        except aiohttp.ClientError as exc:
            if attempt < retries:
                wait = 2 ** attempt + random.uniform(0, 1)
                print(f"⚠️  {url} — ERRO {exc}, tentativa {attempt}/{retries}, aguardando {wait:.1f}s")
                await asyncio.sleep(wait)
                continue
            print(f"⚠️  {url} — ERRO {exc}")
        break
    return None


def parse_games(html: str, page_idx: int) -> List[Game]:
    soup = BeautifulSoup(html, "html.parser")
    # New Metacritic layout uses Tailwind utility classes instead of BEM identifiers.
    # Cards are <a> tags with the grid-cols utility that defines the cover+info layout.
    cards = [
        a for a in soup.find_all("a")
        if "grid-cols-[5.5rem_auto]" in " ".join(a.get("class", []))
    ]
    print(f"   🔍 {len(cards)} cartões totais na página {page_idx}")
    games: List[Game] = []

    for idx, card in enumerate(cards, 1):
        if not card.find("img", alt="must-play"):
            continue

        # Spans without classes hold rank, title, and date in DOM order.
        plain_spans = [s for s in card.find_all("span") if not s.get("class")]
        rank_text = plain_spans[0].get_text(strip=True) if len(plain_spans) > 0 else None
        title_text = plain_spans[1].get_text(strip=True) if len(plain_spans) > 1 else None
        date_text = plain_spans[2].get_text(strip=True) if len(plain_spans) > 2 else None

        score_elem = card.select_one(".c-siteReviewScore span")

        url = card.get("href")
        if url and url.startswith("/"):
            url = "https://www.metacritic.com" + url

        date: Optional[datetime] = None
        if date_text:
            for fmt in ("%b %d, %Y", "%B %d, %Y"):
                try:
                    date = datetime.strptime(date_text, fmt)
                    break
                except ValueError:
                    pass

        score: Optional[int] = None
        if score_elem:
            try:
                score = int(score_elem.get_text(strip=True))
            except ValueError:
                pass

        game = Game(
            rank=rank_text,
            title=title_text,
            release_date=date,
            metascore=score,
            url=url,
        )
        games.append(game)
        print(
            f"      ➕  [{page_idx}.{idx}] "
            f"Rank {game.rank or '?':>3} • "
            f"{(game.title or '—')[:45]:<45} • "
            f"MS {game.metascore or '?'}"
        )
    print(f"   ✔️  {len(games)} must-plays filtrados na página {page_idx}\n")
    return games


def _browse_url(page: int) -> str:
    year = datetime.today().year
    return (
        f"https://www.metacritic.com/browse/game/?releaseYearMin=1958"
        f"&releaseYearMax={year}&page={page}"
    )


def scrape_games(start: int, end: int, delay: float = 1.0) -> List[Game]:
    print("🚀 Scraping Metacritic Must-Play — parâmetros:")
    print(f"    páginas {start}-{end}, delay base {delay}s\n")

    all_games: List[Game] = []
    for page in range(start, end + 1):
        print(f"➡️  PÁGINA {page}")
        url = _browse_url(page)
        html = fetch_page(url)
        if not html:
            print("   ⤬ Página ignorada\n")
            continue

        games = parse_games(html, page)
        if not games:
            print("   ⤬ Nenhum must-play, encerrando loop.\n")
            break

        all_games.extend(games)
        print(f"   📊 Total acumulado: {len(all_games)} jogos\n")
        time.sleep(random.uniform(delay, delay + 1))

    print("✅ Scraping finalizado.\n")
    return all_games


async def scrape_games_async(
    start: int, end: int, delay: float = 1.0, concurrency: int = 5
) -> List[Game]:
    """Fetch multiple pages concurrently respecting the delay."""
    print("🚀 Scraping Metacritic Must-Play — parâmetros:")
    print(
        f"    páginas {start}-{end}, delay base {delay}s, concurrency {concurrency}\n"
    )

    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for page in range(start, end + 1):
            print(f"➡️  PÁGINA {page}")
            tasks.append(fetch_page_async(session, _browse_url(page), delay))

        html_pages = await asyncio.gather(*tasks)

    all_games: List[Game] = []
    for page_idx, html in enumerate(html_pages, start):
        if not html:
            print("   ⤬ Página ignorada\n")
            continue

        games = parse_games(html, page_idx)
        if not games:
            print("   ⤬ Nenhum must-play, encerrando loop.\n")
            break

        all_games.extend(games)
        print(f"   📊 Total acumulado: {len(all_games)} jogos\n")

    print("✅ Scraping finalizado.\n")
    return all_games


def save_csv(games: Iterable[Game], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        f.write("# Data scraped from Metacritic. Licensed under the MIT License.\n")
        writer = csv.DictWriter(
            f, fieldnames=["rank", "title", "release_date", "metascore"]
        )
        writer.writeheader()
        for g in games:
            writer.writerow(
                {
                    "rank": g.rank,
                    "title": g.title,
                    "release_date": (
                        g.release_date.strftime("%Y-%m-%d") if g.release_date else ""
                    ),
                    "metascore": g.metascore,
                }
            )
    print(f"📁 CSV salvo em {filename}\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", type=int, default=1, help="Primeira página (inclusive).")
    p.add_argument("--end", type=int, default=16, help="Última página (inclusive).")
    p.add_argument(
        "--output",
        type=str,
        default=datetime.today().strftime("data/metacritic_must_play_%Y-%m-%d.csv"),
        help="Arquivo CSV de saída.",
    )
    p.add_argument(
        "--delay", type=float, default=1.0, help="Delay base entre requests."
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Número de requisições concorrentes (usa asyncio + aiohttp).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    start_time = time.time()

    if args.concurrency > 1:
        games = asyncio.run(
            scrape_games_async(
                args.start, args.end, delay=args.delay, concurrency=args.concurrency
            )
        )
    else:
        games = scrape_games(args.start, args.end, delay=args.delay)
    games = sort_games_by_rank(games)
    print(f"🔢 Total final: {len(games)} jogos válidos\n")

    save_csv(games, args.output)
    print(f"🏁 Concluído em {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    main()
