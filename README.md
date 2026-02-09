# LocalNewsBot

LocalNewsBot is a Python bot that collects articles from RSS feeds and websites, filters them, and posts selected local news to **Bluesky**. If configured, it can generate AI summaries of articles before posting, and can be controlled via commands sent to the bot via DM.

---

## Features

- Fetches news from multiple RSS and HTML sources  
- Filters unwanted content using keywords or an AI-rating scale
- Posts automatically to Bluesky
- Optional GenAI summaries 
- Admin control via Bluesky DMs  
- SQLite database to track posted articles  

All of the AI features are initially configured to use Google AI Studio's Gemma-27B model (you just need to do a few clicks to get a free API key), which (for now) has quite high quotas for the free tier, so you can easily run this bot's AI features for free!

---

## Setup

1. Clone the repo

    git clone https://github.com/cheracc/localnewsbot.git  
    cd localnewsbot

2. Install dependencies

    pip install -r requirements.txt

3. Configure

    - Rename `config examples/` to `config/`
    - Edit:
      - `config.yml` (Bluesky credentials)
      - `feeds.yml` (news sources)
      - `filter.yml` (excluded keywords)

4. Run

    python3 bot.py

---

## Usage

Run normally:

    python3 bot.py

Run without posting:

    python3 bot.py --no-posts

Schedule with cron or another task runner for continuous operation.

---

## License

See `LICENSE` for details.

---

Created by **@cheracc**
