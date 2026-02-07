from __future__ import annotations
from atproto import Client, IdResolver, models

from src.commands import CommandHandler
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config

class BskyChatHandler:
    def __init__(self, config: Config):
        self.config = config
        self.admin_did = None
        self.client = Client()
        user, paswd = self.config.get_handle_password()
        print(self.client.login(user, paswd))
        self.dm_client = self.client.with_bsky_chat_proxy()
        self.dm = self.dm_client.chat.bsky.convo
        self.command_handler = CommandHandler(config)

    def check_for_commands(self):
        convo = self.get_admin_convo()
        messages = self.get_admin_messages(convo)
        self.parse_messages(messages, convo.id)    

    def get_admin_did(self) -> str:
        if not self.admin_did:
            id_resolver = IdResolver()
            self.admin_did = id_resolver.handle.resolve(self.config.get_admin_handle())
        return self.admin_did if self.admin_did else ""

    def get_admin_convo(self) -> models.ChatBskyConvoDefs.ConvoView:
        convo = self.dm.get_convo_for_members(models.ChatBskyConvoGetConvoForMembers.Params(members=[self.get_admin_did()]),).convo
        return convo

    def get_admin_messages(self, convo) -> models.ChatBskyConvoGetMessages.Response:
        messages = self.dm.get_messages(models.ChatBskyConvoGetMessages.Params(convo_id=convo.id))
        return messages

    def parse_messages(self, messages: models.ChatBskyConvoGetMessages.Response, convo_id: str):
        for message in messages.messages:
            if isinstance(message, models.ChatBskyConvoDefs.MessageView):
                if not message.reactions:
                    text = message.text
                    if self.command_handler.parse_commands(text):
                        self.dm.add_reaction(models.ChatBskyConvoAddReaction.Data(convo_id=convo_id, message_id=message.id, value="👍"))


            
