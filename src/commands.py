from __future__ import annotations
from dataclasses import dataclass
import shlex
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
        self.register_command(BotCommand(self.config, "help", help_command))
        self.register_command(BotCommand(self.config, "add_bad_word", add_bad_word_to_filter))
        self.register_command(BotCommand(self.config, "add_good_word", add_good_word_to_filter))
        self.register_command(BotCommand(self.config, "list_tag_keywords", list_keywords_for_tag))

    # checks text for any command keywords, and executes the command if found
    def parse_commands(self, text: str) -> CommandResponse | None:
        self.config.logger.debug(f"Evaluating message text for command keywords: {text}")
        split = shlex.split(text)
        if not split:
            return None
        args = split[1:]
        command = split[0].lower()
        if not command:
            self.config.logger.debug("No commands found")
            return None
        for cmd in self.commands:
            if cmd.command_string == command:
                self.config.logger.debug(f"Found command {cmd.command_string}, passing args: {args}")
                return_value = cmd.command_func(self.config, args)
                return return_value
        return None

    def register_command(self, cmd: BotCommand):
        self.commands.append(cmd)


class BotCommand:
    def __init__(self, config: Config, cmd_str: str, cmd_func: Callable[[Config, list[str]], CommandResponse]):
        self.config = config
        self.command_string = cmd_str
        self.command_func = cmd_func

    def execute_command(self, config: Config, args: list[str]) -> CommandResponse:
        return self.command_func(config, args)

@dataclass
class CommandResponse:
    success: bool
    response: str

# Basic Commands:
def help_command(config: Config, args: list[str]) -> CommandResponse:
    cmds = config.get_bsky_account().get_chat_handler().command_handler.commands
    if not cmds or len(cmds) == 0:
        return CommandResponse(False, "I have no registered commands. This seems to be a bug.")
    reply = "I have the following commands registered:\n"
    for cmd in cmds:
        cmd_str = f" {cmd.command_string}\n"
        reply = reply + cmd_str
    reply = reply + "\n\nType a command by itself for syntax hints."
    return CommandResponse(True, reply.rstrip())

# Example message: add_bad_word istanbul
def add_bad_word_to_filter(config: Config, args: list[str]) -> CommandResponse:
    if not args or len(args) == 0:
        return CommandResponse(False, 'Syntax: add_bad_word word1 "word two" ...')
    for s in args:
        config.add_bad_word(s)
    return CommandResponse(True, f"Added {len(args)} bad words")

def add_good_word_to_filter(config: Config, args: list[str]) -> CommandResponse:
    if not args:
        return CommandResponse(False, 'Syntax: add_good_word word1 "word two" ...')
    for s in args:
        config.add_good_word(s)
    return CommandResponse(True, f"Added {len(args)} good words")

def list_keywords_for_tag(config: Config, args: list[str]) -> CommandResponse:
    if not args or len(args) != 1:
        return CommandResponse(False, 'Syntax: list_tag_keywords tagNameWithoutHashtag')

    keyword_string = config.get_tag_keywords(args[0])
    if not keyword_string:
        return CommandResponse(False, f"I do not have any keywords for #{args[0]}")
    return CommandResponse(True, keyword_string)

