from __future__ import annotations
from atproto import IdResolver, models
from atproto.exceptions import AtProtocolError
from src.commands import CommandHandler
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config

class BskyChatHandler:
    def __init__(self, config: Config):
        self.config = config
        self.admin_did = None
        self.client = config.get_bsky_account().client
        self.command_handler = CommandHandler(config)

        self.config.get_bsky_account().login()
        self.dm_client = self.client.with_bsky_chat_proxy()
        self.dm = self.dm_client.chat.bsky.convo

    def check_for_commands(self):
        self.config.logger.debug("Checking chat messages for admin commands")
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
            admin_did = self.__get_admin_did()
            self.config.logger.debug(f"Admin did: {admin_did}")
            params = models.ChatBskyConvoGetConvoForMembers.Params(members=[admin_did])
            convo = self.dm.get_convo_for_members(params=params).convo
            self.config.logger.debug(f"Found chat with admin {self.config.get_admin_handle().split(".")[0]}")
            return convo
        except AtProtocolError as e:
            self.config.logger.error(f"Error fetching conversations: {e}")
            raise

    def __get_admin_messages(self, convo) -> models.ChatBskyConvoGetMessages.Response:
        try:
            response = self.dm.get_messages(models.ChatBskyConvoGetMessages.Params(convo_id=convo.id))
            self.config.logger.debug(f"Retrieved {len(response.messages)} messages in the chat")
            return response
        except AtProtocolError as e:
            self.config.logger.error(f"Error fetching messages: {e}")
            raise

    def __parse_messages(self, messages: models.ChatBskyConvoGetMessages.Response, convo_id: str) -> None:
        for message in messages.messages:
            if isinstance(message, models.ChatBskyConvoDefs.MessageView):
                if not message.reactions and message.sender.did == self.admin_did:
                    text = message.text
                    if (response := self.command_handler.parse_commands(text)):
                        # A command was found and we got a response
                        if response:
                            # react with a thumbs-up to show the command was successful
                            try:
                                self.dm.add_reaction(models.ChatBskyConvoAddReaction.Data(convo_id=convo_id, message_id=message.id, value="👍"))
                            except AtProtocolError as e:
                                self.config.logger.warning(f"Error marking completed command: {e}")
                        
                        if response.response and len(response.response) > 0:
                            try:
                                self.dm.send_message(models.ChatBskyConvoSendMessage.Data(
                                    convo_id=convo_id, 
                                    message=models.ChatBskyConvoDefs.MessageInput(text=response.response)))
                            except AtProtocolError as e:
                                self.config.logger.error(f"Error replying to convo: {e}")


            
