# LocalNewsBot

LocalNewsBot is a Python bot that collects articles from RSS feeds and websites, filters them, and posts selected local news to **Bluesky**. If configured, it can generate AI summaries of articles before posting, and can be controlled via commands sent to the bot via DM.

---

## Features

- Fetches news from multiple RSS and HTML sources  
- Filters duplicates and unwanted content  
- Posts automatically to Bluesky
- Optional GenAI summaries (uses Google AI Studio which has free limits way higher than needed for this)
- Admin control via Bluesky DMs  
- SQLite database to track posted articles  

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
