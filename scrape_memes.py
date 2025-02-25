import praw
import json
import os
import requests
import pytesseract
from PIL import Image
from io import BytesIO
from google.cloud import vision
from dotenv import load_dotenv

load_dotenv()

# 🔹 Set up Reddit API
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# 🔹 Initialize Google Vision API
vision_client = vision.ImageAnnotatorClient()
print("✅ Google Vision API connected successfully!")

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

# 🔹 Check subreddit repost policy
def check_subreddit_rules(subreddit_name):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        rules = [rule.description.lower() for rule in subreddit.rules]
        return not any(term in rules for term in ["no reposts", "original content only", "no reuploads"])
    except Exception as e:
        print(f"⚠️ Could not fetch rules for {subreddit_name}: {e}")
        return True  # Assume okay if rules cannot be fetched

# 🔹 Fetch memes
def fetch_memes():
    subreddits = ["memes", "dankmemes", "wholesomememes"]
    memes = []

    for subreddit_name in subreddits:
        if not check_subreddit_rules(subreddit_name):
            continue

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

# 🔹 Check meme content for faces/logos
def check_meme_content(image_url):
    image = vision.Image()
    image.source.image_uri = image_url

    faces = vision_client.face_detection(image=image).face_annotations
    logos = vision_client.logo_detection(image=image).logo_annotations

    return not faces and not logos  # ✅ Must not contain faces/logos

# 🔹 Save memes & prevent reposting
def save_verified_memes(memes):
    posted_memes = load_posted_memes()
    verified_memes = [meme for meme in memes if meme["id"] not in posted_memes]

    if verified_memes:
        with open("memes.json", "w") as f:
            json.dump(verified_memes, f, indent=4)
        print(f"✅ {len(verified_memes)} verified memes saved!")

    posted_memes.update(meme["id"] for meme in verified_memes)
    save_posted_memes(posted_memes)

# 🔹 Main Execution
if __name__ == "__main__":
    memes = fetch_memes()
    verified_memes = []

    for meme in memes:
        if not check_watermark(meme["url"]):
            continue
        if not check_meme_content(meme["url"]):
            continue
        verified_memes.append(meme)

    save_verified_memes(verified_memes)

