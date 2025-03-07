from fastapi import FastAPI, Query
import requests
import httpx
from pydantic import BaseModel
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


@app.get("/anime/episode")
def get_episode_details(url: str = Query(..., title="Episode URL")):
    """Fetch episode details, streaming links, background image, and related episodes"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": "Failed to fetch episode details"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Scrape Background Image
    background_image = soup.find("img", class_="TPostBg")
    background_image_url = background_image["src"] if background_image else "No Background Image Found"

    # Scrape Episode Title and Thumbnail
    episode_title = soup.title.text if soup.title else "No Title Found"
    episode_thumbnail = soup.find("figure").find("img")["src"] if soup.find("figure") else "No Thumbnail Found"

    # Scrape Streaming Server Links
    server_links = [iframe["src"] for iframe in soup.select("iframe") if "src" in iframe.attrs]

    # Scrape Related Episodes
    related_episodes = [{"title": ep.text.strip(), "url": ep["href"]} for ep in soup.select("ul#episode_by_temp li a")]

    return {
        "episode_title": episode_title,
        "episode_thumbnail": episode_thumbnail,
        "background_image": background_image_url,
        "streaming_servers": server_links,
        "related_episodes": related_episodes
    }


@app.get("/anime/categories")
def get_anime_categories():
    """Scrape categorized anime data from anime-world.co"""
    url = "https://anime-world.co"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": "Failed to fetch anime categories"}

    soup = BeautifulSoup(response.text, "html.parser")

    categories = {
        "New Anime Arrivals": [],
        "Most-Watched Shows": [],
        "On-Air Shows": [],
        "Newest Drops": []
    }

    def extract_anime(section, category_name):
        for article in section.find_all("article", class_="post dfx fcl movies"):
            title_tag = article.find("h2", class_="entry-title")
            img_tag = article.find("img")
            link_tag = article.find("a", class_="lnk-blk")
            season_tag = article.find("span", class_="post-ql")
            episode_tag = article.find("span", class_="year")

            if title_tag and img_tag and link_tag:
                anime = {
                    "title": title_tag.text.strip(),
                    "image": img_tag["src"],
                    "link": link_tag["href"],
                    "season": season_tag.text.strip() if season_tag else "Unknown",
                    "episode": episode_tag.text.strip() if episode_tag else "Unknown"
                }
                categories[category_name].append(anime)

    for category in categories.keys():
        section_header = soup.find("h3", class_="section-title", text=category)
        if section_header:
            section = section_header.find_parent("section")
            if section:
                extract_anime(section, category)

    return categories

def scrape_anime(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {"error": "Failed to fetch the page."}
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Scrape Title
    title = soup.find("h1", class_="entry-title").text.strip() if soup.find("h1", class_="entry-title") else "N/A"
    
    # Scrape Description
    description_div = soup.find("div", class_="description")
    description = description_div.text.strip() if description_div else "N/A"
    
    # Scrape Thumbnail
    thumbnail = soup.find("img", alt=f"Image {title}")["src"] if soup.find("img", alt=f"Image {title}") else "N/A"
    
    # Scrape Genre
    genre_div = soup.find("p", class_="genres")
    genres = [a.text for a in genre_div.find_all("a")] if genre_div else []
    
    # Scrape Rating
    rating_span = soup.find("span", class_="num")
    rating = rating_span.text if rating_span else "N/A"
    
    # Scrape Episodes
    episodes = []
    episode_list = soup.select("ul#episode_by_temp li article.post")
    
    for ep in episode_list:
        episode_title = ep.find("h2", class_="entry-title").text.strip() if ep.find("h2", class_="entry-title") else "N/A"
        episode_thumbnail = ep.find("img")["src"] if ep.find("img") else "N/A"
        episode_link = ep.find("a", class_="lnk-blk")["href"] if ep.find("a", class_="lnk-blk") else "N/A"
        
        episodes.append({
            "title": episode_title,
            "thumbnail": episode_thumbnail,
            "link": episode_link
        })
    
     # Extract Post ID (Fix)
    post_id_element = soup.select_one("ul.aa-cnt.sub-menu li a")
    post_id = post_id_element["data-post"] if post_id_element and "data-post" in post_id_element.attrs else "N/A"
    # Extract Seasons
    season_list = soup.select("ul.aa-cnt.sub-menu li a")
    total_seasons = len(season_list) if season_list else 0

    # Extract Current Season
    current_season_element = soup.find("dt", class_="n_s")
    current_season = current_season_element.text.strip() if current_season_element else "N/A"
    
    return {
        "title": title,
        "description": description,
        "thumbnail": thumbnail,
        "genres": genres,
        "rating": rating,
        "post_id": post_id,
        "total_seasons": total_seasons,
        "current_season": current_season,
        "episodes": episodes
    }

@app.get("/anime/detailss")
def get_anime_details(url: str = Query(..., title="Anime URL")):
    return scrape_anime(url)

def scrape_anime_episode(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Failed to fetch page: {response.status_code}"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Get episode title
    title = soup.find("title").text.strip() if soup.find("title") else "Unknown Title"

    # Get thumbnail image
    thumbnail_tag = soup.select_one(".post-thumbnail img")
    thumbnail = thumbnail_tag["src"] if thumbnail_tag else "No Image"

    # Get streaming sources
    sources = []
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src") or iframe.get("data-src")  # Check both src and data-src
        if src:
            sources.append(src)

    # Get other episodes
    episodes = []
    for episode in soup.select(".post.episodes"):
        episode_title_tag = episode.select_one(".entry-title")
        episode_link_tag = episode.select_one(".lnk-blk")
        episode_image_tag = episode.select_one(".post-thumbnail img")

        if episode_title_tag and episode_link_tag and episode_image_tag:
            episodes.append({
                "title": episode_title_tag.text.strip(),
                "link": episode_link_tag["href"],
                "image": episode_image_tag["src"]
            })

    return {
        "title": title,
        "thumbnail": thumbnail,
        "streaming_sources": sources,
        "other_episodes": episodes
    }


@app.get("/anime/episodess")
def get_anime_episode(url: str = Query(..., title="Episode URL")):
    return scrape_anime_episode(url)
    
async def fetch_season_data(season: int, post: int):
    url = "https://anime-world.co/wp-admin/admin-ajax.php"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }
    data = {
        "action": "action_select_season",
        "season": season,
        "post": post
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)

        if response.status_code != 200:
            return {"error": f"Failed to fetch page: {response.status_code}"}

        soup = BeautifulSoup(response.text, "html.parser")

        # Get episode title
        title = soup.find("title").text.strip() if soup.find("title") else "Unknown Title"

        # Get thumbnail image
        thumbnail_tag = soup.select_one(".post-thumbnail img")
        thumbnail = thumbnail_tag["src"] if thumbnail_tag else "No Image"

        # Get streaming sources
        sources = []
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src") or iframe.get("data-src")  # Check both src and data-src
            if src:
                sources.append(src)

        # Get other episodes
        episodes = []
        for episode in soup.select(".post.episodes"):
            episode_title_tag = episode.select_one(".entry-title")
            episode_link_tag = episode.select_one(".lnk-blk")
            episode_image_tag = episode.select_one(".post-thumbnail img")

            if episode_title_tag and episode_link_tag and episode_image_tag:
                episodes.append({
                    "title": episode_title_tag.text.strip(),
                    "link": episode_link_tag["href"],
                    "image": episode_image_tag["src"]
                })

        return {
            "title": title,
            "thumbnail": thumbnail,
            "streaming_sources": sources,
            "other_episodes": episodes
        }
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/anime/season")
async def get_season_episodes(season: int = Query(...), post: int = Query(...)):
    data = await fetch_season_data(season, post)
    return data




def scrape_anime_details(search_query):
    url = f"https://anime-world.co/?s={search_query}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "Failed to retrieve data"}

    soup = BeautifulSoup(response.text, "html.parser")
    anime_list = []

    for item in soup.find_all("li", class_="series"):
        title_elem = item.find("h2", class_="entry-title")
        year_elem = item.find("span", class_="year")
        img_elem = item.find("img")
        link_elem = item.find("a", class_="lnk-blk")

        title = title_elem.text.strip() if title_elem else "N/A"
        year = year_elem.text.strip() if year_elem else "N/A"
        image = f"https:{img_elem['src']}" if img_elem else "N/A"
        link = link_elem["href"] if link_elem else "N/A"

        anime_list.append({
            "Title": title,
            "Year": year,
            "Image": image,
            "Link": link
        })

    return anime_list

@app.get("/search/")
def search_anime(q: str):
    return scrape_anime_details(q)


def scrape_epi_details(search_query):
    url = f"https://aniwa.vercel.app/api/v2/hianime/anime/${search_query}/episodes"
    response = requests.get(url)

    # Return the raw response content directly
    return response.json() if response.status_code == 200 else {"error": "Failed to retrieve data"}

@app.get("/searchep/")
def search_ep(q: str):
    return scrape_epi_details(q)

def scrape_epi_s(search_query):
    url = f"https://aniwa.vercel.app/api/v2/hianime/episode/servers?animeEpisodeId={search_query}"
    response = requests.get(url)

    # Return the raw response content directly
    return response.json() if response.status_code == 200 else {"error": "Failed to retrieve data"}

@app.get("/searchserv/")
def search_epserv(q: str):
    return scrape_epi_s(q)


# Define request model for user input
class EpisodeRequest(BaseModel):
    episode_id: str
    server_id: str

# Function to make a GET request to the external API
def scrape_epi_slist(episode_id: str, server_id: str):
    url = f"https://aniwa.vercel.app/api/v2/hianime/episode/sources?animeEpisodeId={episode_id}&server={server_id}"
    response = requests.get(url)

    # Return JSON response if successful, else return an error message
    return response.json() if response.status_code == 200 else {"error": "Failed to retrieve data"}

# POST request from the user, but internally calls the GET request
@app.post("/searchservlist/")
def search_epservlist(request: EpisodeRequest):
    return scrape_epi_slist(request.episode_id, request.server_id)
