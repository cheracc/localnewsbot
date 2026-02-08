# LocalNewsBot 📰🤖

A Python-based bot that automatically fetches news articles from RSS feeds and HTML sources, filters them based on configurable criteria, and posts them to Bluesky.

**Live bot:** [@hbgpalocalnews.bsky.social](https://bsky.app/profile/hbgpalocalnews.bsky.social)

## Features

- **Multi-source article fetching**: Supports RSS feeds and HTML-based news sources
- **Intelligent filtering**: Removes spam, duplicates, and unwanted content using configurable word filters
- **Admin commands**: Accept commands via Bluesky DMs to manage filters and bot behavior
- **AI summarization**: Optional Google GenAI integration for article summaries
- **Database tracking**: Keeps records of posted and excluded articles
- **Comprehensive logging**: Full debug logging with file and console output
- **Automated scheduling**: Run via cron job for continuous operation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/localnewsbot.git
cd localnewsbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `config.yml` in the root directory with your configuration

4. Set up your Bluesky credentials and API keys in the config

## Configuration

Create a `config.yml` file with the following structure:

```yaml
bluesky:
  handle: your-handle.bsky.social
  password: your-app-password

gemini:
  api_key: your-gemini-api-key

rss_feeds:
  feed_name:
    url: https://example.com/feed.xml
    tag: news

html_sources:
  source_name:
    url: https://example.com/news
    tag: news

filters:
  bad_words:
    - spam
    - clickbait
  good_words:
    - breaking
    - exclusive

delay_between_posts: 2
log_level: INFO
```

## Usage

### Run once (fetch and post articles):
```bash
python3 bot.py
```

### Run without posting (check articles only):
```bash
python3 bot.py --no-posts
```

### Schedule with cron (every minute except multiples of 5):
```bash
* * * * * [ $(($(date +\%M) \% 5)) -ne 0 ] && cd /home/shawn/localnewsbot && /usr/bin/python3 bot.py --no-posts
```

## Admin Commands

Send commands via Bluesky DMs to manage the bot:

- `/help` - Display available commands
- `/addbadword <word>` - Add a word to the filter blacklist
- `/removebadword <word>` - Remove a word from the filter blacklist

## Project Structure

```
localnewsbot/
├── bot.py                      # Main entry point
├── config.yml                  # Configuration file
├── database.sqlite             # Article tracking database
├── log/                        # Daily log files
└── src/
    ├── config.py               # Configuration loader
    ├── bsky_account.py         # Bluesky authentication
    ├── bsky_chat_handler.py    # Command handling via DMs
    ├── bsky_post_handler.py    # Article posting
    ├── bsky_post.py            # BskyPost data class
    ├── rsssource.py            # RSS feed fetching
    ├── htmlsource.py           # HTML source scraping
    ├── newsfilter.py           # Article filtering logic
    ├── aisummary.py            # AI-powered summarization
    ├── commands.py             # Command definitions
    └── data.py                 # Database management
```

## Logging

Logs are written to `log/bot_YYYYMMDD.log` with timestamps and log levels. Set `log_level` in `config.yml` to control verbosity:

- `DEBUG` - Detailed information for development
- `INFO` - General informational messages
- `WARNING` - Warning messages and non-critical errors
- `ERROR` - Error messages with full stack traces

## Database

The bot maintains a SQLite database (`database.sqlite`) with two tables:

- `posts` - Tracks articles that have been posted
- `excluded` - Tracks articles that were filtered out

This prevents duplicate posts and allows for analysis of filtered content.

## Disclaimer

This project is offered as-is without support. Use at your own risk.