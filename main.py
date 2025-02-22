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



@app.get("/anime/details")
def get_anime_details(url: str = Query(..., title="Anime URL")):
    """Fetch anime details from the given URL"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": "Failed to fetch anime details"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract anime details
    title = soup.find("h1", class_="entry-title").text.strip()
    overview = "\n".join([p.text.strip() for p in soup.select(".description p")]) or "N/A"
    genres = [a.text.strip() for a in soup.select(".genres a")]
    languages = [a.text.strip() for a in soup.select(".loadactor a")]
    year = soup.select_one(".year .overviewCss").text.strip() if soup.select_one(".year .overviewCss") else "N/A"
    network = soup.select_one(".network a img")["alt"] if soup.select_one(".network a img") else "N/A"

    # Extract episode details
    episodes = []
    for episode in soup.select("#episode_by_temp li"):
        ep_num = episode.select_one(".num-epi").text.strip()
        ep_title = episode.select_one(".entry-title").text.strip()
        ep_link = episode.select_one("a.lnk-blk")["href"]
        episodes.append({"episode": ep_num, "title": ep_title, "link": ep_link})

    return {
        "title": title,
        "overview": overview,
        "genres": genres,
        "languages": languages,
        "year": year,
        "network": network,
        "episodes": episodes
    }
