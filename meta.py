"""Analyze the latest Metacritic CSV and inject stats into README.md.

Usage
-----
python meta.py                 # uses most recent *.csv in the folder
python meta.py path/to/file.csv
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


# ───────────────────────── CSV discovery ─────────────────────────
def find_latest_csv() -> Optional[str]:
    """Return the most recently modified *.csv file in the current folder."""
    csv_files = [p for p in Path(".").glob("*.csv") if p.is_file()]
    return str(max(csv_files, key=lambda p: p.stat().st_mtime)) if csv_files else None


# ───────────────────────── data classes ──────────────────────────
@dataclass
class Stats:
    total: int
    by_decade: pd.Series
    by_year: pd.Series
    score_distribution: pd.Series
    oldest: pd.Series
    newest: pd.Series
    recent: pd.DataFrame


# ───────────────────────── data pipeline ─────────────────────────
def load_data(csv_file: str) -> pd.DataFrame:
    df = pd.read_csv(csv_file)
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["year"] = df["release_date"].dt.year
    df["decade"] = (df["year"] // 10) * 10
    return df


def compute_stats(df: pd.DataFrame) -> Stats:
    return Stats(
        total=len(df),
        by_decade=df["decade"].value_counts().sort_index(),
        by_year=df["year"].value_counts().head(5).sort_values(ascending=False),
        score_distribution=df["metascore"].value_counts().sort_index(),
        oldest=df.sort_values("release_date").iloc[0],
        newest=df.sort_values("release_date", ascending=False).iloc[0],
        recent=df[df["year"] >= 2020],
    )


# ─────────────────────── markdown helpers ───────────────────────
def series_to_md(series: pd.Series) -> str:
    return "\n".join(f"{idx}: {val}" for idx, val in series.items())


def games_list_md(df: pd.DataFrame) -> str:
    lines: list[str] = []
    grouped = df.groupby("year")

    for year in sorted(grouped.groups.keys()):
        lines.append(f"#### {year}")
        group = grouped.get_group(year).sort_values("metascore", ascending=False)

        for i, (_, row) in enumerate(group.iterrows()):
            date = (
                row["release_date"].strftime("%Y-%m-%d")
                if pd.notnull(row["release_date"])
                else "??"
            )
            title_line = f"- **{row['title']}** ({date}) — Metascore: {row['metascore']}"
            if i == 0:
                title_line += " 🌟 *Possible GOTY*"
            lines.append(title_line)

        lines.append("")  # linha em branco entre anos

    return "\n".join(lines)

def build_stats_block(stats: Stats) -> str:
    return "\n".join(
        [
            "<!-- STATS_START -->",
            f"🎮 **Total must-play games:** {stats.total}",
            "",
            "### Games by decade",
            series_to_md(stats.by_decade),
            "",
            "### Top 5 years (most must-plays)",
            series_to_md(stats.by_year),
            "",
            "### Metascore distribution",
            series_to_md(stats.score_distribution),
            "",
            "### Oldest must-play game",
            f"- {stats.oldest['title']} ({stats.oldest['release_date'].date()}) "
            f"— Metascore {stats.oldest['metascore']}",
            "",
            "### Newest must-play game",
            f"- {stats.newest['title']} ({stats.newest['release_date'].date()}) "
            f"— Metascore {stats.newest['metascore']}",
            "",
            f"### Must-plays released 2020+ ({len(stats.recent)})",
            games_list_md(stats.recent),
            "<!-- STATS_END -->",
            "",
        ]
    )


# ─────────────────────── README handling ────────────────────────
def find_readme(base: Path) -> Path:
    """Return first README*.md (case-insensitive) or default README.md path."""
    for p in base.iterdir():
        if p.is_file() and p.name.lower().startswith("readme") and p.suffix.lower() == ".md":
            return p
    return base / "README.md"


def update_readme(block: str, project_root: Path = Path.cwd()) -> None:
    readme_path = find_readme(project_root)

    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
    else:
        print("ℹ️  README inexistente — criando um novo.")
        text = "# Metacritic Must-play dataset\n\n"

    if "<!-- STATS_START -->" in text and "<!-- STATS_END -->" in text:
        before, _start, rest = text.partition("<!-- STATS_START -->")
        _old, _end, after = rest.partition("<!-- STATS_END -->")
        new_text = before + block + after
    else:
        new_text = text.rstrip() + "\n\n" + block

    readme_path.write_text(new_text, encoding="utf-8")
    print(f"✅ README atualizado: {readme_path}")


# ───────────────────────────── CLI ──────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv", nargs="?", default=None, help="CSV a analisar (opcional).")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    csv_file = args.csv or find_latest_csv()
    if not csv_file:
        raise SystemExit("Nenhum arquivo .csv encontrado para análise.")

    print(f"📊 Analisando {csv_file} …")
    df = load_data(csv_file)
    stats = compute_stats(df)

    block = build_stats_block(stats)
    update_readme(block)

    print("🏁 Fim.")


if __name__ == "__main__":
    main()