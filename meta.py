import pandas as pd

csv_filename = "metacritic_must_play_games_2025-05-04.csv"

# Corrige o parsing do CSV
df = pd.read_csv(csv_filename, names=["rank", "title", "release_date", "metascore"], quotechar='"', skiprows=1)

print("📂 Columns do CSV:", df.columns)

# Corrige a data
df["release_date"] = pd.to_datetime(df["release_date"], format="%b %d, %Y", errors="coerce")
df["year"] = df["release_date"].dt.year
df["decade"] = (df["year"] // 10) * 10

# Saída
print(f"\n🎮 Total must-play games: {len(df)}")

print("\n📊 Games by decade:")
print(df["decade"].value_counts().sort_index())

print("\n📅 Top 5 years with most must-play games:")
print(df["year"].value_counts().head(5).sort_values(ascending=False))

print("\n🏆 Metascore distribution:")
print(df["metascore"].value_counts().sort_index())

print("\n📌 Oldest must-play game:")
print(df.sort_values("release_date").iloc[0])

print("\n📌 Newest must-play game:")
print(df.sort_values("release_date", ascending=False).iloc[0])
