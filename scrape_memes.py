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

def load_posted_memes():
    if os.path.exists(POSTED_MEMES_FILE):
        with open(POSTED_MEMES_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted_memes(memes):
    with open(POSTED_MEMES_FILE, "w") as f:
        json.dump(list(memes), f, indent=4)

# 🔹 Fetch memes
def fetch_memes():
    subreddits = ["memes", "dankmemes", "wholesomememes"]
    memes = []

    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.hot(limit=50):
            if len(memes) >= 10:  # Collect only 10 verified memes
                break
            if submission.stickied or not submission.url.endswith(("jpg", "png")):
                continue

            memes.append({
                "id": submission.id,
                "title": submission.title,
                "url": submission.url,
                "author": submission.author.name if submission.author else "unknown",
                "permalink": f"https://reddit.com{submission.permalink}"
            })

    return memes

# 🔹 Check watermarks using OCR
def check_watermark(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    text = pytesseract.image_to_string(img).lower()
    
    banned_keywords = ["instagram", "tiktok", "©", "all rights reserved"]
    return not any(word in text for word in banned_keywords)

# 🔹 Save memes for manual review
def save_memes_for_review(memes):
    with open("memes_for_review.json", "w") as f:
        json.dump(memes, f, indent=4)
    print(f"✅ {len(memes)} memes saved for review!")

# 🔹 Main Execution
if __name__ == "__main__":
    memes = fetch_memes()
    verified_memes = [meme for meme in memes if check_watermark(meme["url"])]
    save_memes_for_review(verified_memes)
