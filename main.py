"""Scrape Metacritic must-play games (listagem apenas) — agora com log detalhado."""

from __future__ import annotations

import argparse
import csv
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


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
        key=lambda g: int(g.rank.rstrip(".")) if g.rank and g.rank.rstrip(".").isdigit() else 0,
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


def parse_games(html: str, page_idx: int) -> List[Game]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("a.c-finderProductCard_container")
    print(f"   🔍 {len(cards)} cartões totais na página {page_idx}")
    games: List[Game] = []

    for idx, card in enumerate(cards, 1):
        if not card.select_one('img[alt="must-play"]'):
            continue
        title_elem = card.select_one(".c-finderProductCard_titleHeading span:nth-of-type(2)")
        rank_elem = card.select_one(".c-finderProductCard_titleHeading span:nth-of-type(1)")
        date_elem = card.select_one(".c-finderProductCard_meta span:nth-of-type(1)")
        metascore_elem = card.select_one(".c-siteReviewScore span")

        url = card.get("href")
        if url and url.startswith("/"):
            url = "https://www.metacritic.com" + url

        date: Optional[datetime] = None
        if date_elem:
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
        print(
            f"      ➕  [{page_idx}.{idx}] "
            f"Rank {game.rank or '?':>3} • "
            f"{(game.title or '—')[:45]:<45} • "
            f"MS {game.metascore or '?'}"
        )
    print(f"   ✔️  {len(games)} must-plays filtrados na página {page_idx}\n")
    return games


def scrape_games(start: int, end: int, delay: float = 1.0) -> List[Game]:
    print("🚀 Scraping Metacritic Must-Play — parâmetros:")
    print(f"    páginas {start}-{end}, delay base {delay}s\n")

    all_games: List[Game] = []
    for page in range(start, end + 1):
        print(f"➡️  PÁGINA {page}")
        url = (
            "https://www.metacritic.com/browse/game/?releaseYearMin=1958"
            f"&releaseYearMax=2025&page={page}"
        )
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


def save_csv(games: Iterable[Game], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "title", "release_date", "metascore"])
        writer.writeheader()
        for g in games:
            writer.writerow(
                {
                    "rank": g.rank,
                    "title": g.title,
                    "release_date": g.release_date.strftime("%Y-%m-%d") if g.release_date else "",
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
        default=datetime.today().strftime("metacritic_must_play_%Y-%m-%d.csv"),
        help="Arquivo CSV de saída.",
    )
    p.add_argument("--delay", type=float, default=1.0, help="Delay base entre requests.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    start_time = time.time()

    games = scrape_games(args.start, args.end, delay=args.delay)
    games = sort_games_by_rank(games)
    print(f"🔢 Total final: {len(games)} jogos válidos\n")

    save_csv(games, args.output)
    print(f"🏁 Concluído em {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    main()
