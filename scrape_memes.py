import praw
import json
import os
import requests
import pytesseract
from PIL import Image
from io import BytesIO
from google.cloud import vision

# 🔹 Reddit API Credentials
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# 🔹 Google Vision Client
vision_client = vision.ImageAnnotatorClient()

# 🔹 Fetch Memes from r/memes
def fetch_memes():
    subreddit = reddit.subreddit("memes")
    memes = []
    
    for submission in subreddit.hot(limit=20):
        if not submission.stickied and submission.url.endswith(("jpg", "png")):
            memes.append({
                "title": submission.title,
                "url": submission.url,
                "author": submission.author.name,
                "permalink": f"https://reddit.com{submission.permalink}"
            })
    
    return memes

# 🔹 Check Watermarks Using OCR
def check_watermark(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    text = pytesseract.image_to_string(img).lower()
    
    # Keywords that indicate copyright issues
    banned_keywords = ["instagram", "tiktok", "©", "all rights reserved"]
    return not any(word in text for word in banned_keywords)

# 🔹 Check for Faces/Logos Using Google Vision API
def check_meme_content(image_url):
    image = vision.Image()
    image.source.image_uri = image_url

    # Detect faces (personal images)
    faces = vision_client.face_detection(image=image).face_annotations
    if faces:
        return False  # ❌ Avoid personal photos

    # Detect logos (brands)
    logos = vision_client.logo_detection(image=image).logo_annotations
    return not logos  # ❌ Avoid brand-related memes

# 🔹 Store Verified Memes
def save_verified_memes(memes):
    with open("memes.json", "w") as f:
        json.dump(memes, f, indent=4)
    print(f"✅ {len(memes)} memes saved!")

# 🔹 Main Execution
if __name__ == "__main__":
    memes = fetch_memes()
    verified_memes = []

    for meme in memes:
        print(f"🔍 Checking meme: {meme['title']}")
        
        if not check_watermark(meme["url"]):
            print(f"❌ Skipping {meme['title']} - Watermark detected!")
            continue

        if not check_meme_content(meme["url"]):
            print(f"❌ Skipping {meme['title']} - Contains brand logos or personal images!")
            continue

        verified_memes.append(meme)

    save_verified_memes(verified_memes)
