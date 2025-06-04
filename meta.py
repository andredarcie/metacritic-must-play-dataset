"""Analyze a Metacritic must-play CSV file."""

from __future__ import annotations

import argparse
import glob
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


def find_latest_csv(pattern: str = "metacritic_must_play_games_*.csv") -> Optional[str]:
    """Return the newest CSV filename matching ``pattern`` or ``None``."""
    files = sorted(Path(".").glob(pattern))
    return str(files[-1]) if files else None


@dataclass
class Stats:
    total: int
    by_decade: pd.Series
    by_year: pd.Series
    score_distribution: pd.Series
    oldest: pd.Series
    newest: pd.Series
    recent: pd.DataFrame


def load_data(csv_file: str) -> pd.DataFrame:
    """Load the CSV and return a cleaned ``DataFrame``."""
    df = pd.read_csv(csv_file, quotechar='"')
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["year"] = df["release_date"].dt.year
    df["decade"] = (df["year"] // 10) * 10
    return df


def compute_stats(df: pd.DataFrame) -> Stats:
    """Compute statistics used in the report."""
    by_decade = df["decade"].value_counts().sort_index()
    by_year = df["year"].value_counts().head(5).sort_values(ascending=False)
    score_distribution = df["metascore"].value_counts().sort_index()
    oldest = df.sort_values("release_date").iloc[0]
    newest = df.sort_values("release_date", ascending=False).iloc[0]
    recent = df[df["year"] >= 2020]
    return Stats(
        total=len(df),
        by_decade=by_decade,
        by_year=by_year,
        score_distribution=score_distribution,
        oldest=oldest,
        newest=newest,
        recent=recent,
    )


def print_report(stats: Stats) -> None:
    """Display a formatted report on the console."""
    print(f"\n🎮 Total must-play games: {stats.total}")

    print("\n📊 Games by decade:")
    print(stats.by_decade)

    print("\n📅 Top 5 years with most must-play games:")
    print(stats.by_year)

    print("\n🏆 Metascore distribution:")
    print(stats.score_distribution)

    print("\n📌 Oldest must-play game:")
    print(stats.oldest)

    print("\n📌 Newest must-play game:")
    print(stats.newest)

    recent_games = stats.recent
    print(f"\n🆕 Must-play games released after 2020: {len(recent_games)}")
    for _, row in recent_games.iterrows():
        date_str = row["release_date"].strftime("%Y-%m-%d") if pd.notnull(row["release_date"]) else ""  
        print(f"{row['title']} ({date_str}) - Metascore: {row['metascore']}")

    print("\n📅 By year (with average Metascore):")
    for year in sorted(recent_games["year"].unique()):
        games_in_year = recent_games[recent_games["year"] == year]
        count = len(games_in_year)
        avg = games_in_year["metascore"].mean()
        print(f"{year} = {count} games | Avg Metascore: {avg:.1f}")

    print("\n🎮 Games by year:")
    for year in sorted(recent_games["year"].unique()):
        games_in_year = recent_games[recent_games["year"] == year]
        titles = ", ".join(games_in_year["title"])
        print(f"{year} = {titles}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv",
        nargs="?",
        default=None,
        help="CSV file to analyze (latest by default)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_file = args.csv or find_latest_csv()
    if not csv_file:
        raise SystemExit("No CSV files found to analyze.")

    print(f"Analyzing {csv_file}...")
    df = load_data(csv_file)
    stats = compute_stats(df)
    print_report(stats)


if __name__ == "__main__":
    main()
