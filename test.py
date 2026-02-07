from src.bsky_chat_handler import BskyChatHandler
from src.config import Config


def main():
    config = Config()
    chat_handler = BskyChatHandler(config)

    chat_handler.list_convos()

if __name__ == "__main__":
    main()