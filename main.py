from fastapi import FastAPI
from bs4 import BeautifulSoup
import uvicorn

app = FastAPI()

@app.get("/scrape")
def scrape_anime():
    # Load the HTML file
    with open("response.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "lxml")

    # Extract anime details
    anime_data = []
    for anime in soup.find_all("article", class_="post dfx fcl movies"):
        title_tag = anime.find("h2", class_="entry-title")
        link_tag = anime.find("a", class_="lnk-blk")
        image_tag = anime.find("img")

        title = title_tag.text.strip() if title_tag else "N/A"
        link = link_tag["href"] if link_tag else "N/A"
        image = image_tag["src"] if image_tag else "N/A"
        description = anime.find("span", class_="post-ql")

        anime_data.append({
            "title": title,
            "link": link,
            "image": image,
            "description": description.text.strip() if description else "N/A",
        })

    return {"anime_list": anime_data}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
