from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from src.config import Config

class CommandHandler:
    def __init__(self, config: Config):
        self.config = config
        self.logger = config.get_logger()
        self.commands: list[BotCommand] = []
        self.register_commands()

    def register_commands(self):
        self.register_command(BotCommand(self.config, "add_bad_word", add_bad_word_to_filter))
        self.register_command(BotCommand(self.config, "add_good_word", add_good_word_to_filter))

    # checks for bluesky messages that contain command keywords
    def parse_commands(self, text: str) -> bool:
        split = text.split()
        if not split:
            return False
        command = split[0].lower()
        args = "".join(split[1:]).strip()
        if not args or not command:
            return False
        for cmd in self.commands:
            if cmd.command_string == command:
                cmd.command_func(self.config, args)
                return True
        return False

    def register_command(self, cmd: BotCommand):
        self.commands.append(cmd)


class BotCommand:
    def __init__(self, config: Config, cmd_str: str, cmd_func: Callable):
        self.config = config
        self.command_string = cmd_str
        self.command_func = cmd_func

    def execute_command(self, config: Config, args: str):
        self.command_func(config, args)


# Basic Commands:

# Example message: add_bad_word istanbul
def add_bad_word_to_filter(config: Config, word: str):
    config.add_bad_word(word)

def add_good_word_to_filter(config: Config, word: str):
    config.add_good_word(word)