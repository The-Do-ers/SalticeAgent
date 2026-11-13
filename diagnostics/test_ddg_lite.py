import requests
from lxml import html

url = "https://lite.duckduckgo.com/lite/"
data = {"q": "Python 3.13 release"}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://lite.duckduckgo.com/"
}
r = requests.post(url, data=data, headers=headers, timeout=10)
print("Status:", r.status_code)
tree = html.fromstring(r.text)
snippets = tree.xpath('//td[@class="result-snippet"]/text()')
print("Snippets found:", len(snippets))
for s in snippets[:3]:
    print("-", s.strip())
