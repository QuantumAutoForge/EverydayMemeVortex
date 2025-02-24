import tweepy
import json
import os
import requests
from PIL import Image
from io import BytesIO

# 🔹 Twitter API Credentials
client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)

# 🔹 Load Memes from Repo
def load_memes():
    with open("memes.json", "r") as f:
        return json.load(f)

# 🔹 Post Meme to Twitter
def post_meme():
    memes = load_memes()
    if not memes:
        print("❌ No memes left to post!")
        return

    meme = memes.pop(0)  # Get first meme
    image_url, title, source = meme["url"], meme["title"], meme["permalink"]

    # 🔹 Download and Save Image
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img.save("meme.jpg")

    # 🔹 Upload Image to Twitter
    media = client.media_upload(filename="meme.jpg")

    # 🔹 Include Reddit URL in Tweet
    tweet_text = f"{title}\n\n🔗 Source: {source}"

    tweet = client.create_tweet(text=tweet_text, media_ids=[media.media_id])

    # 🔹 Save Updated Meme List
    with open("memes.json", "w") as f:
        json.dump(memes, f, indent=4)

    print(f"✅ Meme tweeted: {tweet.data}")

post_meme()
