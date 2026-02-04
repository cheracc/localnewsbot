# LocalNewsBot 📰🤖

`LocalNewsBot` is an automated tool designed to scrape local news headlines and articles from various sources and post them directly to **Bluesky**. It helps keep local communities informed by bridging the gap between traditional news sites and the decentralized social web.

## 🚀 Features

* **Automated Scraping:** Each run checks local news websites for new stories.
* **Bluesky Integration:** Automatically formats and posts news updates to your Bluesky profile.
* **Rich Embeds:** Supports posting with titles, descriptions, and article links.
* **Deduplication:** Ensures the same news story isn't posted multiple times (uses sqlite).
* **Headless Operation:** This is a simple python script that can be run on anything that runs python.

## 🛠️ Tech Stack

* **Language:** Python
* **API:** [AT Protocol (atproto)](https://atproto.com/) for Bluesky interactions.
* **Scraping:** feedparser (RSS) / newspaper3k (HTML)
* **Scheduling:** cron etc.

## 📋 Prerequisites

Before running the bot, you will need:

* A Bluesky account for the bot to use.
* An **App Password** from Bluesky (Settings -> App Passwords).
* Python 3.x installed.

## ⚙️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/cheracc/localnewsbot.git
cd localnewsbot

```


2. **Install dependencies:**
```bash
pip install newspaper3k
pip install feedparser
pip install beautifulsoup4

```
and potentially any other ones it yells at you about


3. **Configuration:**

Rename the config.yml.example file to config.yml and add your information:
- bsky_handle
- bsky_password (must be an app password)
- edit/add rss or html feeds as needed
- bad_words and good_words (for filter)

## Filtering

use bad_words and good_words in config.yml. Filtering works like this:
1. any articles with a bad word in the title, description, or url are removed UNLESS they also contain a good word
2. any custom filters are run. Place these in a customfilters.py file with a filter(articles) function (see customfilters.py.example)

## Database

This uses an sqlite database to keep track and avoid duplicates. It will create this itself

## 🚀 Usage

To start the bot manually, run:

```bash
python bot.py

```

## 🤖 Deployment

use cron or some other service to run bot.py at the desired interval

## 📄 License

Distributed under the MIT NON-AI License. See `LICENSE` for more information.

---

### Contact

Please don't 🙅

**Project Link:** [https://github.com/cheracc/localnewsbot](https://www.google.com/search?q=https://github.com/cheracc/localnewsbot)

### This is offered as is, no support will be provided.