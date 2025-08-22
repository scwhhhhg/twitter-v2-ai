import os
import tweepy
import requests
from datetime import datetime
import time
import random
from urllib.parse import quote

# === Konfigurasi ===
api_key = os.getenv("TWITTER_API_KEY")
api_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
target_link = os.getenv("TARGET_LINK", "https://example.com")  # Ganti default jika perlu

# Autentikasi Twitter
client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    wait_on_rate_limit=True
)

auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
api = tweepy.API(auth)

# === Daftar topik trending untuk inspirasi ===
topics = [
    "AI", "tech", "future", "innovation", "science", "coding", "programming",
    "robot", "machine learning", "space", "crypto", "web3", "nft", "gaming"
]

# === 1. Ambil Trending Hashtag dari Twitter (lokasi: Worldwide) ===
def get_trending_hashtags():
    try:
        trends = api.get_place_trends(id=1)  # id=1 adalah Worldwide
        hashtags = []
        for trend in trends[0]["trends"]:
            if trend["name"].startswith("#") and len(hashtags) < 5:
                hashtags.append(trend["name"])
        return hashtags[:3]  # ambil 3 teratas
    except:
        return ["#AI", "#Tech", "#Future"]  # fallback

# === 2. Ambil gambar dari Pexels API (lebih stabil) ===
def generate_image(prompt):
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    if not PEXELS_API_KEY:
        print("❌ PEXELS_API_KEY not set in secrets.")
        return None

    # Mapping topik ke keyword Pexels
    keyword_map = {
        "AI": "artificial intelligence ai futuristic tech",
        "tech": "technology digital future innovation",
        "future": "futuristic concept advanced",
        "science": "science research lab experiment",
        "coding": "code programming developer laptop",
        "robot": "robot android machine automation",
        "space": "space universe cosmos stars galaxy",
        "crypto": "cryptocurrency bitcoin blockchain digital money",
        "gaming": "gaming video games esports",
        "web3": "web3 metaverse decentralized",
        "nft": "nft digital art crypto art",
        "machine learning": "machine learning deep learning data science"
    }

    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }

    # Tentukan query pencarian
    query = "futuristic abstract digital art"
    for key, value in keyword_map.items():
        if key.lower() in prompt.lower():
            query = value
            break

    url = f"https://api.pexels.com/v1/search?query={quote(query)}&per_page=1&orientation=landscape"
    print("🔍 Fetching from Pexels:", url)

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data["photos"]:
                img_url = data["photos"][0]["src"]["large"]  # 940x650+
                print("📥 Downloading image:", img_url)
                img_data = requests.get(img_url, timeout=30).content
                filename = f"pexels_{int(time.time())}.jpg"
                with open(filename, "wb") as f:
                    f.write(img_data)
                return filename
            else:
                print("🚫 No photos found on Pexels.")
        else:
            print("❌ Pexels API error:", response.status_code, response.text)
    except Exception as e:
        print("❌ Image fetch failed:", e)
    return None

# === 3. Buat tweet menarik dengan trending hashtag ===
def create_tweet():
    topic = random.choice(topics)
    mood = random.choice([
        "Mind-blowing",
        "This will change everything",
        "You won't believe this",
        "The future is here",
        "Wait until you see this",
        "Incredible",
        "Revolutionary"
    ])
    hashtags = get_trending_hashtags()
    hashtag_str = " ".join(hashtags)
    
    tweet_text = f"""
{mood} {topic} concept! 🤯

What would you use this for?

{hashtag_str}
    """.strip()
    
    return tweet_text, topic  # hanya kirim topik, nanti di map ke keyword

# === 4. Auto-reply ke tweet utama dengan link ===
def reply_with_link(tweet_id):
    reply_text = f"Want to learn how this was made? 👉 {target_link}"
    try:
        client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
        print("Replied with link!")
    except Exception as e:
        print("Reply failed:", e)

# === 5. Main Function ===
def main():
    print("🚀 Starting Twitter Bot...")
    
    # Buat tweet
    tweet_text, image_prompt = create_tweet()
    print("Tweet:", tweet_text)
    print("Image prompt:", image_prompt)
    
    # Generate gambar
    image_file = generate_image(image_prompt)
    if not image_file:
        print("❌ Failed to generate image. Exiting.")
        return
    
    # Upload gambar dan post tweet
    try:
        media = api.media_upload(image_file)
        response = client.create_tweet(text=tweet_text, media_ids=[media.media_id])
        tweet_id = response.data["id"]
        print("✅ Tweet posted successfully!")
        
        # Balas dengan link
        time.sleep(5)  # Jeda sebelum reply
        reply_with_link(tweet_id)
        
        # Hapus file gambar
        os.remove(image_file)
        
    except Exception as e:
        print("❌ Tweet failed:", e)

if __name__ == "__main__":
    main()
