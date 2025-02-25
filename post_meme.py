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

# 🔹 Tweepy v4+ Requires `API` for Media Upload
auth = tweepy.OAuth1UserHandler(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)
api = tweepy.API(auth)

def load_memes():
    if os.path.exists("approved_memes.json"):
        with open("approved_memes.json", "r") as f:
            return json.load(f)
    return []

def post_meme():
    memes = load_memes()
    if not memes:
        print("❌ No approved memes left to post!")
        return

    meme = memes.pop(0)

    response = requests.get(meme["url"])
    img = Image.open(BytesIO(response.content))
    img.save("meme.jpg")

    # 🔹 Upload media using `API` instead of `Client`
    media = api.media_upload(filename="meme.jpg")

    # 🔹 Post Tweet using `Client`
    tweet_text = f"{meme['title']}\n\n🔗 Source: {meme['permalink']}"
    tweet = client.create_tweet(text=tweet_text, media_ids=[media.media_id_string])

    # 🔹 Save remaining memes
    with open("approved_memes.json", "w") as f:
        json.dump(memes, f, indent=4)

    print(f"✅ Meme posted: {tweet.data}")

post_meme()
