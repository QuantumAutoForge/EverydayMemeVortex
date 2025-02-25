import praw
import json
import os
import requests
import pytesseract
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# 🔹 Set up Reddit API
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# 🔹 Load existing posted memes
POSTED_MEMES_FILE = "posted_memes.json"

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def load_posted_memes():
    return set(load_json(POSTED_MEMES_FILE))

def save_posted_memes(memes):
    save_json(POSTED_MEMES_FILE, list(memes))

# 🔹 Fetch memes from past year & prevent duplicates
def fetch_memes():
    subreddits = ["memes", "dankmemes", "wholesomememes"]
    memes = []
    
    approved_memes = load_json("approved_memes.json")
    rejected_memes = load_json("rejected_memes.json")
    already_posted_memes = load_posted_memes()
    existing_memes = load_json("memes_for_review.json")  # Keep already scraped memes

    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.top(time_filter="year", limit=50):  # 🔹 Get top memes from past year
            if len(memes) >= 10:
                break
            if submission.stickied or not submission.url.endswith(("jpg", "png")):
                continue

            meme = {
                "id": submission.id,
                "title": submission.title,
                "url": submission.url,
                "author": submission.author.name if submission.author else "unknown",
                "permalink": f"https://reddit.com{submission.permalink}"
            }

            # 🔹 Skip meme if already in approved, rejected, posted, or review list
            if meme["url"] in [m["url"] for m in approved_memes + rejected_memes + existing_memes] or meme["url"] in already_posted_memes:
                continue

            memes.append(meme)

    return memes

# 🔹 Check watermarks using OCR
def check_watermark(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    text = pytesseract.image_to_string(img).lower()
    
    banned_keywords = ["instagram", "tiktok", "©", "all rights reserved"]
    return not any(word in text for word in banned_keywords)

# 🔹 Append new memes instead of overwriting
def save_memes_for_review(memes):
    existing_memes = load_json("memes_for_review.json")
    new_memes = existing_memes + memes  # 🔹 Append instead of overwriting
    save_json("memes_for_review.json", new_memes)
    print(f"✅ {len(new_memes)} memes now available for review!")

# 🔹 Main Execution
if __name__ == "__main__":
    memes = fetch_memes()
    verified_memes = [meme for meme in memes if check_watermark(meme["url"])]
    save_memes_for_review(verified_memes)

