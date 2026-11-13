import sys
import requests
import json
from lxml import html

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def search_web_ddg(query: str, max_results: int = 5):
    url = "https://html.duckduckgo.com/html/?q=" + requests.utils.quote(query)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            tree = html.fromstring(r.text)
            results = []
            # Find results
            links = tree.xpath('//a[@class="result__url"]')
            titles = tree.xpath('//h2[@class="result__title"]/a')
            snippets = tree.xpath('//a[@class="result__snippet"]')
            for i in range(min(len(titles), max_results)):
                title = titles[i].text_content().strip() if i < len(titles) else ""
                href = titles[i].get("href", "") if i < len(titles) else ""
                snippet = snippets[i].text_content().strip() if i < len(snippets) else ""
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet
                })
            return results
        return []
    except Exception as e:
        return [{"error": str(e)}]

res = search_web_ddg("Python 3.13 features", 3)
print("Results:", json.dumps(res, indent=2))
