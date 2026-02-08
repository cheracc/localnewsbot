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

3. Rename the 'config examples' folder to 'config'

4. Set up your Bluesky credentials and API keys in the config

5. Enter your RSS/HTML feed info in feeds.yml

6. You can edit filter words and tags/keywords in filter.yml and tags.yml (but you can also modify these by messaging the bot)

7. Run the bot "python3 bot.py". This will run only once. See how it does, modify keywords, etc.

8. Once you are happy, use cron to schedule it to run on an interval.

## Usage

### Run once (do everything: check DMs, fetch and post articles):
```bash
python3 bot.py
```
I run this every 5-10 minutes
### Run without posting (check DMs/Run commands only):
```bash
python3 bot.py --no-posts
```
I run this every minute

## Admin Commands

Send commands via Bluesky DMs to manage the bot. Commands are only accepted from the admin_bsky_handle in config.yml:

- `/help` - Display available commands

You can add/remove good/bad filter words, you can add tags (and keywords that trigger them), you can add/remove keywords from existing tags. The commands are fairly self-explanatory.


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

This project is offered as-is without support. Use at your own risk. If it has been updated recently, it's possible something is broken, just check back if it doesn't work.