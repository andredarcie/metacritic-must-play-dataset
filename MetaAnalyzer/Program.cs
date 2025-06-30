using CsvHelper;
using CsvHelper.Configuration;
using System.Globalization;

internal record Game(string? Rank, string? Title, DateTime? Release_date, int? Metascore);

internal class Stats
{
    public int Total { get; set; }
    public Dictionary<int, int> ByDecade { get; set; } = new();
    public Dictionary<int, int> ByYear { get; set; } = new();
    public Dictionary<int, int> ScoreDistribution { get; set; } = new();
    public Game? Oldest { get; set; }
    public Game? Newest { get; set; }
    public List<Game> Recent { get; set; } = new();
}

internal static class Program
{
    static string? FindLatestCsv()
    {
        var files = Directory.GetFiles(".", "*.csv");
        if (files.Length == 0) return null;
        Array.Sort(files, (a, b) => File.GetLastWriteTime(b).CompareTo(File.GetLastWriteTime(a)));
        return files[0];
    }

    static List<Game> LoadData(string csvFile)
    {
        using var reader = new StreamReader(csvFile);
        using var csv = new CsvReader(reader, new CsvConfiguration(CultureInfo.InvariantCulture) { HeaderValidated = null, MissingFieldFound = null });
        var records = csv.GetRecords<Game>().ToList();
        return records;
    }

    static Stats ComputeStats(List<Game> games)
    {
        var stats = new Stats();
        stats.Total = games.Count;
        foreach (var g in games)
        {
            var year = g.Release_date?.Year ?? 0;
            var decade = (year / 10) * 10;
            if (year > 0)
            {
                if (!stats.ByYear.ContainsKey(year)) stats.ByYear[year] = 0;
                stats.ByYear[year]++;
                if (!stats.ByDecade.ContainsKey(decade)) stats.ByDecade[decade] = 0;
                stats.ByDecade[decade]++;
                if (year >= 2020) stats.Recent.Add(g);
            }
            if (g.Metascore.HasValue)
            {
                if (!stats.ScoreDistribution.ContainsKey(g.Metascore.Value)) stats.ScoreDistribution[g.Metascore.Value] = 0;
                stats.ScoreDistribution[g.Metascore.Value]++;
            }
        }
        stats.ByYear = stats.ByYear.OrderByDescending(kv => kv.Value).Take(5).ToDictionary(kv => kv.Key, kv => kv.Value);
        stats.ByDecade = stats.ByDecade.OrderBy(kv => kv.Key).ToDictionary(kv => kv.Key, kv => kv.Value);
        stats.ScoreDistribution = stats.ScoreDistribution.OrderBy(kv => kv.Key).ToDictionary(kv => kv.Key, kv => kv.Value);
        stats.Oldest = games.Where(g => g.Release_date != null).OrderBy(g => g.Release_date).FirstOrDefault();
        stats.Newest = games.Where(g => g.Release_date != null).OrderByDescending(g => g.Release_date).FirstOrDefault();
        return stats;
    }

    static string SeriesToMd(Dictionary<int, int> series)
    {
        return string.Join("\n", series.Select(kv => $"{kv.Key}: {kv.Value}"));
    }

    static string GamesListMd(IEnumerable<Game> games)
    {
        var grouped = games.Where(g => g.Release_date != null).GroupBy(g => g.Release_date!.Value.Year).OrderBy(g => g.Key);
        var lines = new List<string>();
        foreach (var group in grouped)
        {
            lines.Add($"#### {group.Key}");
            var ordered = group.OrderByDescending(g => g.Metascore ?? 0).ToList();
            for (int i = 0; i < ordered.Count; i++)
            {
                var g = ordered[i];
                var date = g.Release_date?.ToString("yyyy-MM-dd") ?? "??";
                var line = $"- **{g.Title}** ({date}) — Metascore: {g.Metascore}";
                if (i == 0) line += " 🌟 *Possible GOTY*";
                lines.Add(line);
            }
            lines.Add(string.Empty);
        }
        return string.Join("\n", lines);
    }

    static string BuildStatsBlock(Stats stats)
    {
        return string.Join("\n", new[]
        {
            "<!-- STATS_START -->",
            $"🎮 **Total must-play games:** {stats.Total}",
            string.Empty,
            "### Games by decade",
            SeriesToMd(stats.ByDecade),
            string.Empty,
            "### Top 5 years (most must-plays)",
            SeriesToMd(stats.ByYear),
            string.Empty,
            "### Metascore distribution",
            SeriesToMd(stats.ScoreDistribution),
            string.Empty,
            "### Oldest must-play game",
            stats.Oldest is not null ? $"- {stats.Oldest.Title} ({stats.Oldest.Release_date:yyyy-MM-dd}) — Metascore {stats.Oldest.Metascore}" : "- N/A",
            string.Empty,
            "### Newest must-play game",
            stats.Newest is not null ? $"- {stats.Newest.Title} ({stats.Newest.Release_date:yyyy-MM-dd}) — Metascore {stats.Newest.Metascore}" : "- N/A",
            string.Empty,
            $"### Must-plays released 2020+ ({stats.Recent.Count})",
            GamesListMd(stats.Recent),
            "<!-- STATS_END -->",
            string.Empty
        });
    }

    static string FindReadmePath()
    {
        foreach (var file in Directory.GetFiles(".", "README*.md"))
        {
            return file;
        }
        return "README.md";
    }

    static void UpdateReadme(string block)
    {
        var path = FindReadmePath();
        string text = File.Exists(path) ? File.ReadAllText(path) : "# Metacritic Must-play dataset\n\n";
        if (text.Contains("<!-- STATS_START -->") && text.Contains("<!-- STATS_END -->"))
        {
            var before = text.Split("<!-- STATS_START -->")[0];
            var after = text.Split("<!-- STATS_END -->")[1];
            text = before + block + after;
        }
        else
        {
            text = text.Trim() + "\n\n" + block;
        }
        File.WriteAllText(path, text);
        Console.WriteLine($"✅ README atualizado: {path}");
    }

    static int Main(string[] args)
    {
        string? csvFile = args.Length > 0 ? args[0] : FindLatestCsv();
        if (csvFile is null)
        {
            Console.Error.WriteLine("Nenhum arquivo .csv encontrado para análise.");
            return 1;
        }
        Console.WriteLine($"📊 Analisando {csvFile} …");
        var games = LoadData(csvFile);
        var stats = ComputeStats(games);
        var block = BuildStatsBlock(stats);
        UpdateReadme(block);
        Console.WriteLine("🏁 Fim.");
        return 0;
    }
}
