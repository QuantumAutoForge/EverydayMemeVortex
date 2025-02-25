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

# 🔹 File Names
REVIEW_FILE = "memes_for_review.json"
APPROVED_FILE = "approved_memes.json"
REJECTED_FILE = "rejected_memes.json"
POSTED_FILE = "already_posted_memes.json"

# 🔹 Load JSON Data
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

# 🔹 Save JSON Data
def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# 🔹 Fetch memes from past year & prevent duplicates
def fetch_memes():
    subreddits = ["memes", "dankmemes", "wholesomememes"]
    memes = []

    # 🔹 Load existing meme lists
    approved_memes = load_json(APPROVED_FILE)
    rejected_memes = load_json(REJECTED_FILE)
    posted_memes = load_json(POSTED_FILE)
    existing_memes = load_json(REVIEW_FILE)

    print(f"📂 Loaded Memes - Approved: {len(approved_memes)}, Rejected: {len(rejected_memes)}, Posted: {len(posted_memes)}, Review: {len(existing_memes)}")

    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.top(time_filter="year", limit=100):  # 🔹 Get top memes from past year
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

            # 🔹 Skip duplicates
            all_existing_memes = [m["url"] for m in approved_memes + rejected_memes + posted_memes + existing_memes]
            if meme["url"] in all_existing_memes:
                print(f"⚠️ Skipping duplicate: {meme['url']}")
                continue

            memes.append(meme)

    print(f"✅ New memes scraped: {len(memes)}")
    return memes

# 🔹 Check watermarks using OCR
def check_watermark(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    text = pytesseract.image_to_string(img).lower()
    
    banned_keywords = ["instagram", "tiktok", "©", "all rights reserved"]
    if any(word in text for word in banned_keywords):
        print(f"🚨 Watermark detected in {image_url}, skipping.")
        return False
    return True

# 🔹 Append new memes instead of overwriting
def save_memes_for_review(memes):
    existing_memes = load_json(REVIEW_FILE)
    print(f"📂 Existing memes before saving: {len(existing_memes)}")
    
    new_memes = existing_memes + memes  # 🔹 Append instead of overwriting
    save_json(REVIEW_FILE, new_memes)

    print(f"✅ Total memes in review after saving: {len(new_memes)}")

# 🔹 Main Execution
if __name__ == "__main__":
    memes = fetch_memes()
    verified_memes = [meme for meme in memes if check_watermark(meme["url"])]
    
    if verified_memes:
        save_memes_for_review(verified_memes)
    else:
        print("❌ No new verified memes found.")
