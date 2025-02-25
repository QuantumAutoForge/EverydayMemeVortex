import tweepy
import json
import os
import requests
from PIL import Image
from io import BytesIO

POSTED_MEMES_FILE = "already_posted_memes.json"

# Load Twitter API credentials from environment variables
auth = tweepy.OAuth1UserHandler(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)
api = tweepy.API(auth)

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def post_meme():
    approved_memes = load_json("approved_memes.json")
    posted_memes = load_json(POSTED_MEMES_FILE)

    if not approved_memes:
        print("❌ No approved memes left to post!")
        return

    meme = approved_memes.pop(0)
    response = requests.get(meme["url"])
    img = Image.open(BytesIO(response.content))
    img.save("meme.jpg")

    # Upload media
    media = api.media_upload(filename="meme.jpg")
    tweet_text = f"{meme['title']}\n\n🔗 Source: {meme['permalink']}"
    api.update_status(status=tweet_text, media_ids=[media.media_id_string])

    print("✅ Meme posted successfully!")

    # Move meme to already_posted_memes.json
    posted_memes.append(meme)
    save_json("already_posted_memes.json", posted_memes)
    save_json("approved_memes.json", approved_memes)

post_meme()
