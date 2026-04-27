# Metacritic Must-Play Dataset

A dataset of all Metacritic **Must-Play** games — titles that achieved a Metascore of **90 or higher** based on at least 15 professional critic reviews, signaling universal acclaim.

> **Why it matters**
> - **Nintendo** promoted Breath of the Wild as having “more perfect scores than any game in Metacritic history.”
> - **Sony** targets 90+ Metacritic scores on major titles, as noted by ex-art director Rafael Grassetti.
> - **Xbox** highlights “200+ games rated 85+” on Game Pass to showcase critical value.

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the scraper sequentially:

```bash
python main.py --start 1 --end 16
```

Run with concurrent requests (faster):

```bash
python main.py --concurrency 5
```

The generated CSV is saved to the `data/` folder. Stats in this README are updated automatically every week via GitHub Actions.

<!-- STATS_START -->
🎮 **Total must-play games:** 337

### Games by decade
1990: 26
2000: 180
2010: 87
2020: 44

### Top 5 years (most must-plays)
2000: 25
2001: 25
2002: 21
2003: 20
2007: 18

### Metascore distribution
90: 83
91: 64
92: 61
93: 45
94: 35
95: 17
96: 17
97: 12
98: 2
99: 1

### Oldest must-play game
- GoldenEye 007 (1997-08-25) — Metascore 96

### Newest must-play game
- Hades II (2025-09-25) — Metascore 95

### Must-plays released 2020+ (44)
#### 2020
- **Persona 5 Royal** (2020-03-31) — Metascore: 95 🌟 *Possible GOTY*
- **The Last of Us Part II** (2020-06-19) — Metascore: 93
- **Half-Life: Alyx** (2020-03-23) — Metascore: 93
- **Hades** (2020-09-17) — Metascore: 93
- **Demon's Souls** (2020-11-11) — Metascore: 92
- **Microsoft Flight Simulator** (2020-08-18) — Metascore: 91
- **Crusader Kings III** (2020-09-01) — Metascore: 91
- **Animal Crossing: New Horizons** (2020-03-20) — Metascore: 90
- **Ori and the Will of the Wisps** (2020-03-11) — Metascore: 90

#### 2021
- **Forza Horizon 5** (2021-11-05) — Metascore: 92 🌟 *Possible GOTY*
- **Final Fantasy XIV: Endwalker** (2021-12-07) — Metascore: 92
- **Chicory: A Colorful Tale** (2021-06-10) — Metascore: 90

#### 2022
- **Elden Ring** (2022-02-25) — Metascore: 96 🌟 *Possible GOTY*
- **God of War: Ragnarok** (2022-11-09) — Metascore: 94
- **Chained Echoes** (2022-12-08) — Metascore: 90
- **The Stanley Parable: Ultra Deluxe** (2022-04-27) — Metascore: 90

#### 2023
- **Baldur's Gate 3** (2023-08-03) — Metascore: 96 🌟 *Possible GOTY*
- **The Legend of Zelda: Tears of the Kingdom** (2023-05-12) — Metascore: 96
- **Metroid Prime Remastered** (2023-02-08) — Metascore: 94
- **Resident Evil 4** (2023-03-24) — Metascore: 93
- **Super Mario Bros. Wonder** (2023-10-20) — Metascore: 92
- **Street Fighter 6** (2023-06-02) — Metascore: 92
- **Against the Storm** (2023-12-08) — Metascore: 91
- **Slay the Princess** (2023-10-23) — Metascore: 90
- **Marvel's Spider-Man 2** (2023-10-20) — Metascore: 90
- **DAVE THE DIVER** (2023-06-28) — Metascore: 90

#### 2024
- **Astro Bot** (2024-09-06) — Metascore: 94 🌟 *Possible GOTY*
- **Elden Ring: Shadow of the Erdtree** (2024-06-21) — Metascore: 94
- **Metaphor: ReFantazio** (2024-10-11) — Metascore: 94
- **Final Fantasy VII Rebirth** (2024-02-29) — Metascore: 92
- **UFO 50** (2024-09-18) — Metascore: 91
- **Satisfactory** (2024-09-10) — Metascore: 91
- **Animal Well** (2024-05-09) — Metascore: 90
- **Balatro** (2024-02-20) — Metascore: 90
- **The Last of Us Part II Remastered** (2024-01-19) — Metascore: 90
- **Tekken 8** (2024-01-26) — Metascore: 90

#### 2025
- **The Legend of Zelda: Tears of the Kingdom - Nintendo Switch 2 Edition** (2025-06-05) — Metascore: 95 🌟 *Possible GOTY*
- **Hades II** (2025-09-25) — Metascore: 95
- **The Legend of Zelda: Breath of the Wild - Nintendo Switch 2 Edition** (2025-06-05) — Metascore: 94
- **Clair Obscur: Expedition 33** (2025-04-24) — Metascore: 92
- **Blue Prince** (2025-04-10) — Metascore: 92
- **Split Fiction** (2025-03-06) — Metascore: 91
- **Donkey Kong Bananza** (2025-07-17) — Metascore: 91
- **Hollow Knight: Silksong** (2025-09-04) — Metascore: 90

<!-- STATS_END -->




## Data License

The scraped CSV files are available under the [MIT License](LICENSE).
