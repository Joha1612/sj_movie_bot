import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

BASE_URL = "https://fibwatch.art"

session = cloudscraper.create_scraper()

VIDEO_FORMATS = (".mkv", ".mp4", ".avi", ".mov", ".webm")


# ================= COMMON SCRAPER =================

def extract_movies(url):

    r = session.get(url, timeout=20)

    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "lxml")

    movies = []

    cards = soup.select("div.video-thumb")

    for card in cards:

        try:
            link_tag = card.select_one("a[href*='/watch/']")
            img_tag = card.select_one("img")

            title_tag = card.find_next("p", class_="hptag")

            if not link_tag:
                continue

            link = urljoin(BASE_URL, link_tag["href"])

            title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

            poster = img_tag["src"] if img_tag else None

            movies.append({
                "title": title,
                "url": link,
                "poster": poster
            })

        except:
            continue

    return movies


# ================= SEARCH =================
def search_movie(query):

    search_url = f"{BASE_URL}/search?keyword={query}"

    r = session.get(search_url)

    soup = BeautifulSoup(r.text, "lxml")

    results = []

    cards = soup.select("div.video-latest-list, div.video-wrapper")

    for card in cards:

        a = card.select_one("a[href*='/watch/']")
        img = card.select_one("img")
        title_tag = card.select_one("p.hptag")

        if not a:
            continue

        title = None

        if title_tag:
            title = title_tag.get("title") or title_tag.text.strip()

        if not title:
            title = "Unknown Title"

        link = urljoin(BASE_URL, a["href"])

        poster = img["src"] if img else None

        results.append({
            "title": title,
            "url": link,
            "poster": poster
        })

    return results[:20]


def get_trending_movies():

    url = f"{BASE_URL}/videos/trending"

    r = session.get(url)

    soup = BeautifulSoup(r.text, "lxml")

    results = []

    cards = soup.select("div.video-latest-list, div.video-wrapper")

    for card in cards:

        a = card.select_one("a[href*='/watch/']")
        img = card.select_one("img")
        title_tag = card.select_one("p.hptag")

        if not a:
            continue

        title = title_tag.get("title") if title_tag else "Unknown Title"

        link = urljoin(BASE_URL, a["href"])

        poster = img["src"] if img else None

        results.append({
            "title": title,
            "url": link,
            "poster": poster
        })

    return results[:20]


def get_category_movies(category_url):

    r = session.get(category_url)

    soup = BeautifulSoup(r.text, "lxml")

    results = []

    cards = soup.select("div.video-latest-list, div.video-wrapper")

    for card in cards:

        a = card.select_one("a[href*='/watch/']")
        img = card.select_one("img")
        title_tag = card.select_one("p.hptag")

        if not a:
            continue

        title = title_tag.get("title") if title_tag else "Unknown Title"

        link = urljoin(BASE_URL, a["href"])

        poster = img["src"] if img else None

        results.append({
            "title": title,
            "url": link,
            "poster": poster
        })

    return results[:20]

def get_latest_movies():

    url = "https://fibwatch.art/videos/latest"

    r = session.get(url, timeout=20)

    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "lxml")

    movies = []

    items = soup.select("div.video-latest-list")

    for item in items:

        try:

            # movie page link
            link_tag = item.select_one("div.video-thumb a")

            # title
            title_tag = item.select_one("div.channel_details p.hptag")

            # poster
            img_tag = item.select_one("div.video-thumb img")

            if not link_tag:
                continue

            link = link_tag["href"]

            if not link.startswith("http"):
                link = "https://fibwatch.art" + link

            title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

            poster = img_tag["src"] if img_tag else None

            movies.append({
                "title": title,
                "url": link,
                "poster": poster
            })

        except:
            continue

    return movies

# ================= TITLE CLEAN =================

def clean_title(title):

    title = re.sub(r'\b(480p|720p|1080p)\b', '', title, flags=re.I)

    title = re.sub(
        r'\b(WEB-DL|HDTS|HDRip|BluRay|BongoBD|ZEE5|Netflix)\b',
        '',
        title,
        flags=re.I
    )

    title = re.sub(r'\s+', ' ', title).strip()

    return title


# ================= GROUP MOVIES =================

def group_movies(movie_list):

    grouped = {}

    for movie in movie_list:

        base_title = clean_title(movie["title"])

        if base_title not in grouped:
            grouped[base_title] = []

        grouped[base_title].append(movie)

    return grouped


# ================= DOWNLOAD LINKS =================

def detect_quality(url):

    if "1080" in url:
        return "1080p"
    if "720" in url:
        return "720p"
    if "480" in url:
        return "480p"

    return "Download"


def get_download_links(movie_url):

    r = session.get(movie_url, timeout=20)

    soup = BeautifulSoup(r.text, "lxml")

    downloads = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "urlshortlink" in href:
            continue

        if any(ext in href.lower() for ext in VIDEO_FORMATS):

            downloads.append({
                "quality": detect_quality(href),
                "url": href
            })

    return {"downloads": downloads}
