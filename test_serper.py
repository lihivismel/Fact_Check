import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("SERPER_API_KEY")

headers = {"X-API-KEY": api_key}
query = {"q": "האם שתיית קפה מזיקה ללב?"}

response = requests.post("https://google.serper.dev/search", headers=headers, json=query)

if response.status_code == 200:
    data = response.json()
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write("✅ success :\n\n")
        for i, result in enumerate(data.get("organic", [])[:5], 1):
            title = result.get("title","")
            link = result.get("link","")
            snippet = result.get("snippet","")
            f.write(f"{i}. {title}\n")
            f.write(f"   {link}\n")
            f.write(f"   {snippet}\n\n")

