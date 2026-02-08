from __future__ import annotations
from atproto import Client, IdResolver, models
from atproto.exceptions import AtProtocolError
from src.commands import CommandHandler
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config

class BskyChatHandler:
    def __init__(self, config: Config):
        self.config = config
        self.admin_did = None
        self.client = config.client
        self.command_handler = CommandHandler(config)
        user, paswd = self.config.get_handle_password()

        try:
            self.client.login(user, paswd)
        except AtProtocolError as e:
            self.config.logger.error(f"Could not login user {user}: {e}")
            raise

        self.dm_client = self.client.with_bsky_chat_proxy()
        self.dm = self.dm_client.chat.bsky.convo

    def check_for_commands(self):
        convo = self.__get_admin_convo()
        messages = self.__get_admin_messages(convo)
        self.__parse_messages(messages, convo.id)    

    def __get_admin_did(self) -> str:
        admin_handle = self.config.get_admin_handle()

        if not self.admin_did:
            id_resolver = IdResolver()
            self.admin_did = id_resolver.handle.resolve(admin_handle)

        if self.admin_did:
            self.config.logger.debug(f"Resolved admin user: {admin_handle}: {self.admin_did}")
            return self.admin_did
        
        self.config.logger.warning(f"Could not resolve admin user: {admin_handle}")
        return ""

    def __get_admin_convo(self) -> models.ChatBskyConvoDefs.ConvoView:
        try:
            convo = self.dm.get_convo_for_members(models.ChatBskyConvoGetConvoForMembers.Params(members=[self.__get_admin_did()]),).convo
            return convo
        except AtProtocolError as e:
            self.config.logger.error(f"Error fetching conversations: {e}")
            raise

    def __get_admin_messages(self, convo) -> models.ChatBskyConvoGetMessages.Response:
        try:
            messages = self.dm.get_messages(models.ChatBskyConvoGetMessages.Params(convo_id=convo.id))
            return messages
        except AtProtocolError as e:
            self.config.logger.error(f"Error fetching messages: {e}")
            raise

    def __parse_messages(self, messages: models.ChatBskyConvoGetMessages.Response, convo_id: str):
        for message in messages.messages:
            if isinstance(message, models.ChatBskyConvoDefs.MessageView):
                if not message.reactions:
                    text = message.text
                    if self.command_handler.parse_commands(text):
                        try:
                            self.dm.add_reaction(models.ChatBskyConvoAddReaction.Data(convo_id=convo_id, message_id=message.id, value="👍"))
                        except AtProtocolError as e:
                            self.config.logger.error(f"Error marking completed command: {e}")
                            raise


            
