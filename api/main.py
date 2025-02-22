from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/anime")
def get_anime():
    url = "https://anime-world.co"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Failed to fetch the page. Status code: {response.status_code}"}

    soup = BeautifulSoup(response.text, "lxml")

    anime_data = []
    for anime in soup.find_all("article", class_="post dfx fcl movies"):
        title_tag = anime.find("h2", class_="entry-title")
        link_tag = anime.find("a", class_="lnk-blk")
        image_tag = anime.find("img")
        description = anime.find("span", class_="post-ql")

        title = title_tag.text.strip() if title_tag else "N/A"
        link = link_tag["href"] if link_tag else "N/A"
        image = image_tag["src"] if image_tag else "N/A"
        desc = description.text.strip() if description else "N/A"

        anime_data.append({
            "title": title,
            "link": link,
            "image": image,
            "description": desc
        })

    return {"anime": anime_data}
