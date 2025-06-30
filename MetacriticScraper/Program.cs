using AngleSharp;
using AngleSharp.Dom;
using CsvHelper;
using System.Globalization;

internal record Game(string? Rank, string? Title, DateTime? ReleaseDate, int? Metascore, string? Url);

internal static class Program
{
    private static async Task<string?> FetchPageAsync(HttpClient client, string url, double delay)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        try
        {
            using var resp = await client.GetAsync(url);
            var text = await resp.Content.ReadAsStringAsync();
            sw.Stop();
            var kb = text.Length / 1024.0;
            if (resp.IsSuccessStatusCode)
            {
                Console.WriteLine($"⬇️  {url} — OK {sw.Elapsed.TotalSeconds:F2}s • {kb:F1} KB");
                await Task.Delay(TimeSpan.FromSeconds(delay + new Random().NextDouble()));
                return text;
            }
            Console.WriteLine($"⚠️  {url} — HTTP {(int)resp.StatusCode} {sw.Elapsed.TotalSeconds:F2}s");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"⚠️  {url} — ERRO {ex.Message}");
        }
        return null;
    }

    private static List<Game> ParseGames(string html, int pageIdx)
    {
        var context = BrowsingContext.New(Configuration.Default);
        var doc = context.OpenAsync(req => req.Content(html)).GetAwaiter().GetResult();
        var cards = doc.QuerySelectorAll("a.c-finderProductCard_container");
        Console.WriteLine($"   🔍 {cards.Length} cartões totais na página {pageIdx}");
        var games = new List<Game>();
        int idx = 0;
        foreach (var card in cards)
        {
            idx++;
            if (card.QuerySelector("img[alt='must-play']") is null)
                continue;
            var title = card.QuerySelector(".c-finderProductCard_titleHeading span:nth-of-type(2)")?.TextContent.Trim();
            var rank = card.QuerySelector(".c-finderProductCard_titleHeading span:nth-of-type(1)")?.TextContent.Trim();
            var dateText = card.QuerySelector(".c-finderProductCard_meta span:nth-of-type(1)")?.TextContent.Trim();
            var metascoreText = card.QuerySelector(".c-siteReviewScore span")?.TextContent.Trim();
            string? url = card.GetAttribute("href");
            if (!string.IsNullOrEmpty(url) && url.StartsWith("/"))
                url = "https://www.metacritic.com" + url;
            DateTime? date = null;
            if (DateTime.TryParseExact(dateText, "MMM dd, yyyy", CultureInfo.InvariantCulture, DateTimeStyles.None, out var d))
                date = d;
            int? metascore = int.TryParse(metascoreText, out var ms) ? ms : null;
            var paddedTitle = (title ?? "—").PadRight(45);
            if (paddedTitle.Length > 45) paddedTitle = paddedTitle[..45];
            games.Add(new Game(rank, title, date, metascore, url));
            Console.WriteLine($"      ➕  [{pageIdx}.{idx}] Rank {rank,3} • {paddedTitle} • MS {metascore}");
        }
        Console.WriteLine($"   ✔️  {games.Count} must-plays filtrados na página {pageIdx}\n");
        return games;
    }

    private static async Task<List<Game>> ScrapeAsync(int start, int end, double delay, int concurrency)
    {
        Console.WriteLine("🚀 Scraping Metacritic Must-Play — parâmetros:");
        Console.WriteLine($"    páginas {start}-{end}, delay base {delay}s, concurrency {concurrency}\n");
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("User-Agent", "Mozilla/5.0");
        var tasks = new List<Task<string?>>();
        var results = new List<string?>();

        for (int page = start; page <= end; page++)
        {
            Console.WriteLine($"➡️  PÁGINA {page}");
            var url = $"https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2025&page={page}";
            tasks.Add(FetchPageAsync(client, url, delay));
            if (tasks.Count == concurrency)
            {
                results.AddRange(await Task.WhenAll(tasks));
                tasks.Clear();
            }
        }
        if (tasks.Count > 0)
            results.AddRange(await Task.WhenAll(tasks));

        var allGames = new List<Game>();
        int idx = start;
        foreach (var html in results)
        {
            if (html is null)
            {
                Console.WriteLine("   ⤬ Página ignorada\n");
                idx++;
                continue;
            }
            var games = ParseGames(html, idx++);
            if (games.Count == 0)
            {
                Console.WriteLine("   ⤬ Nenhum must-play, encerrando loop.\n");
                continue;
            }
            allGames.AddRange(games);
            Console.WriteLine($"   📊 Total acumulado: {allGames.Count} jogos\n");
        }
        Console.WriteLine("✅ Scraping finalizado.\n");
        return allGames;
    }

    private static void SaveCsv(IEnumerable<Game> games, string filename)
    {
        using var writer = new StreamWriter(filename);
        writer.WriteLine("# Data scraped from Metacritic. Licensed under the MIT License.");
        using var csv = new CsvWriter(writer, CultureInfo.InvariantCulture);
        csv.WriteHeader<Game>();
        csv.NextRecord();
        foreach (var g in games)
        {
            csv.WriteRecord(g);
            csv.NextRecord();
        }
        Console.WriteLine($"📁 CSV salvo em {filename}\n");
    }

    private static async Task<int> Main(string[] args)
    {
        int start = 1;
        int end = 16;
        string output = $"metacritic_must_play_{DateTime.Today:yyyy-MM-dd}.csv";
        double delay = 1.0;
        int concurrency = 1;

        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--start":
                    if (i + 1 < args.Length && int.TryParse(args[++i], out var s)) start = s;
                    break;
                case "--end":
                    if (i + 1 < args.Length && int.TryParse(args[++i], out var e)) end = e;
                    break;
                case "--output":
                    if (i + 1 < args.Length) output = args[++i];
                    break;
                case "--delay":
                    if (i + 1 < args.Length && double.TryParse(args[++i], out var dlay)) delay = dlay;
                    break;
                case "--concurrency":
                    if (i + 1 < args.Length && int.TryParse(args[++i], out var c)) concurrency = c;
                    break;
            }
        }

        var gamesList = await ScrapeAsync(start, end, delay, concurrency);
        var orderedGames = gamesList.OrderBy(g => int.TryParse(g.Rank?.Trim('.'), out var r) ? r : 0).ToList();
        Console.WriteLine($"🔢 Total final: {orderedGames.Count} jogos válidos\n");
        SaveCsv(orderedGames, output);
        Console.WriteLine("🏁 Concluído.");
        return 0;
    }
}
