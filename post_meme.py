import tweepy
import json
import os
import requests
from PIL import Image
from io import BytesIO

POSTED_MEMES_FILE = "posted_memes.json"

# 🔹 Twitter API Setup
client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)

# 🔹 Load Memes
def load_memes():
    if os.path.exists("memes.json"):
        with open("memes.json", "r") as f:
            return json.load(f)
    return []

def load_posted_memes():
    if os.path.exists(POSTED_MEMES_FILE):
        with open(POSTED_MEMES_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted_memes(memes):
    with open(POSTED_MEMES_FILE, "w") as f:
        json.dump(list(memes), f, indent=4)

# 🔹 Post Meme
def post_meme():
    memes = load_memes()
    posted_memes = load_posted_memes()

    if not memes:
        print("❌ No memes left to post!")
        return

    meme = memes.pop(0)
    posted_memes.add(meme["id"])

    response = requests.get(meme["url"])
    img = Image.open(BytesIO(response.content))
    img.save("meme.jpg")

    media = client.media_upload(filename="meme.jpg")
    tweet_text = f"{meme['title']}\n\n🔗 Source: {meme['permalink']}"

    tweet = client.create_tweet(text=tweet_text, media_ids=[media.media_id])

    with open("memes.json", "w") as f:
        json.dump(memes, f, indent=4)
    
    save_posted_memes(posted_memes)
    print(f"✅ Meme posted: {tweet.data}")

post_meme()
