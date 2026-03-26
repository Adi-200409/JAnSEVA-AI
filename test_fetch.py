import requests
import json
import re

URL = "https://www.myscheme.gov.in/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

try:
    response = requests.get(URL, headers=headers)
    print("Status:", response.status_code)
    html = response.text
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if match:
        data = json.loads(match.group(1))
        pageData = data.get("props", {}).get("pageProps", {})
        with open("e:/smart_community/smart_community/search_data.json", "w", encoding="utf-8") as f:
            json.dump(pageData, f, indent=2)
        print("Successfully extracted search_data.json")
    else:
        print("No script found")
except Exception as e:
    print("Error:", str(e))
