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
        self.register_command(BotCommand(self.config, "/help", help_command))
        self.register_command(BotCommand(self.config, "/addbadword", add_bad_word_to_filter))
        self.register_command(BotCommand(self.config, "/addgoodword", add_good_word_to_filter))
        self.register_command(BotCommand(self.config, "/listtagkeywords", list_keywords_for_tag))
        self.register_command(BotCommand(self.config, "/listbadwords", list_bad_words))
        self.register_command(BotCommand(self.config, "/listgoodwords", list_good_words))
        self.register_command(BotCommand(self.config, "/removebadword", remove_bad_words))
        self.register_command(BotCommand(self.config, "/removegoodword", remove_good_words))
        self.register_command(BotCommand(self.config, "/addkeywordstotag", add_keywords_to_tag))
        self.register_command(BotCommand(self.config, "/removekeywordsfromtag", remove_keywords_from_tag))
        self.register_command(BotCommand(self.config, "/showprompt", show_prompt))
        self.register_command(BotCommand(self.config, "/setprompt", set_prompt))

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

# Example message: /addbadword istanbul
def add_bad_word_to_filter(config: Config, args: list[str]) -> CommandResponse:
    if not args or len(args) == 0:
        return CommandResponse(False, 'Syntax: /addbadword word1 "word two" ...')
    config.add_bad_words(args)
    return CommandResponse(True, f"Added {len(args)} bad words")

def add_good_word_to_filter(config: Config, args: list[str]) -> CommandResponse:
    if not args:
        return CommandResponse(False, 'Syntax: /addgoodword word1 "word two" ...')
    config.add_good_words(args)
    return CommandResponse(True, f"Added {len(args)} good words")

def list_keywords_for_tag(config: Config, args: list[str]) -> CommandResponse:
    if not args or len(args) != 1:
        return CommandResponse(False, 'Syntax: /listtagkeywords tagNameWithoutHashtag')

    keyword_string = config.get_tag_keywords(args[0])
    if not keyword_string:
        return CommandResponse(False, f"I do not have any keywords for #{args[0]}")
    return CommandResponse(True, f"#{args[0]} will be added if any of these words are found:\n\n{keyword_string}")

def list_bad_words(config: Config, args: list[str]) -> CommandResponse:
    bad_words = "|".join(config.get_bad_words())
    response = f"Here are all the bad words:\n\n{bad_words}\n\nA bad word match is overridden if a good word is also present. Matching is case-insensitive."
    return CommandResponse(True, response)

def list_good_words(config: Config, args: list[str]) -> CommandResponse:
    good_words = "|".join(config.get_good_words())
    response = f"Here are all the good words:\n\n{good_words}\n\nA good word match overrides bad words. Matching is case-insensitive."
    return CommandResponse(True, response)

def remove_bad_words(config: Config, args: list[str]) -> CommandResponse:
    removed = config.remove_bad_words(args)
    if removed == 0:
        return CommandResponse(False, "None of those words were found in the bad words list.")
    else:
        return CommandResponse(True, f"Removed {removed} bad words.")
    
def remove_good_words(config: Config, args: list[str]) -> CommandResponse:
    removed = config.remove_good_words(args)
    if removed == 0:
        return CommandResponse(False, "None of those words were found in the good words list.")
    else:
        return CommandResponse(True, f"Removed {removed} good words.")

def remove_keywords_from_tag(config: Config, args: list[str]) -> CommandResponse:
    if not args or len(args) < 2:
        return CommandResponse(False, 'Syntax: /removekeywordsfromtag tagNameWithoutHashtag keyword1 "keyword two" ...')

    tag = args[0]
    keywords = args[1:]
    removed_count = config.remove_keywords_from_tag(tag, keywords)
    if removed_count == 0:
        return CommandResponse(False, f"None of those keywords were found for #{tag}")
    else:
        return CommandResponse(True, f"Removed {removed_count} keywords from #{tag}")
    
def add_keywords_to_tag(config: Config, args: list[str]) -> CommandResponse:
    if not args or len(args) < 2:
        return CommandResponse(False, 'Syntax: /addkeywordstotag tagNameWithoutHashtag keyword1 "keyword two" ...')

    tag = args[0]
    keywords = args[1:]
    if config.add_keywords_to_tag(tag, keywords):
        return CommandResponse(True, f"Created new tag #{tag} and added {len(keywords)} keywords to it.")
    return CommandResponse(True, f"Added {len(keywords)} keywords to existing tag #{tag}")

def show_prompt(config: Config, args: list[str]) -> CommandResponse:
    prompt = config.get_prompt()
    if not prompt:
        return CommandResponse(False, "No prompt is currently set.")
    return CommandResponse(True, f"The current AI summary prompt is:\n\n{prompt}")

def set_prompt(config: Config, args: list[str]) -> CommandResponse:
    if not args or len(args) == 0:
        return CommandResponse(False, 'Syntax: /setprompt "Your new prompt goes here"')
    new_prompt = " ".join(args)
    config.save_new_prompt(new_prompt)
    return CommandResponse(True, "AI summary prompt updated.")