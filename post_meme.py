import tweepy
import json
import os
import requests
from PIL import Image
from io import BytesIO
import random
from datetime import datetime

POSTED_MEMES_FILE = "already_posted_memes.json"
APPROVED_MEMES_FILE = "approved_memes.json"

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

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def post_meme():
    approved_memes = load_json(APPROVED_MEMES_FILE)
    posted_memes = load_json(POSTED_MEMES_FILE)

    if not approved_memes:
        print("❌ No approved memes left to post!")
        return

    # 🔹 Check if any meme is scheduled
    scheduled_meme = next((m for m in approved_memes if m.get("scheduled", False)), None)
    meme = scheduled_meme if scheduled_meme else random.choice(approved_memes)  # Pick scheduled meme or random one

    response = requests.get(meme["url"])
    img = Image.open(BytesIO(response.content))
    img.save("meme.jpg")

    # 🔹 Upload media using `API`
    '''media = api.media_upload(filename="meme.jpg")

    # 🔹 Remove Reddit Link & Only Tweet Title
    tweet_text = f"{meme['title']}"  # ✅ Removed 🔗 Source: {meme['permalink']}
    tweet = client.create_tweet(text=tweet_text, media_ids=[media.media_id_string])'''

    print(f"✅ Meme posted: {tweet.data}")

    # 🔹 Move posted meme to `already_posted_memes.json` with timestamp
    meme["posted_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    posted_memes.append(meme)

    # 🔹 Remove meme from approved list & Save Both Files
    approved_memes = [m for m in approved_memes if m["id"] != meme["id"]]

    save_json(POSTED_MEMES_FILE, posted_memes)
    save_json(APPROVED_MEMES_FILE, approved_memes)  # ✅ Ensure updated list is saved

    print(f"✅ Meme moved to {POSTED_MEMES_FILE} with timestamp & removed from {APPROVED_MEMES_FILE}")

def move_meme_back_to_approved(meme_id):
    """ Moves a meme from `already_posted_memes.json` back to `approved_memes.json` for reposting """
    approved_memes = load_json(APPROVED_MEMES_FILE)
    posted_memes = load_json(POSTED_MEMES_FILE)

    meme = next((m for m in posted_memes if m["id"] == meme_id), None)
    if meme:
        approved_memes.append(meme)
        save_json(APPROVED_MEMES_FILE, approved_memes)
        print(f"✅ Meme {meme_id} moved back to Approved Memes for reposting.")
    else:
        print(f"❌ Meme {meme_id} not found in Posted Memes.")

post_meme()

