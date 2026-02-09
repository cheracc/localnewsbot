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
        self.config.logger.debug("Checking chat messages for admin commands:")
        convo = self.__get_admin_convo()
        messages = self.__get_admin_messages(convo)
        if self.__parse_messages(messages, convo.id):
            self.config.logger.info(" Processed admin chat messages")
        else:
            self.config.logger.info(" No admin chat messages to process")    

    def __get_admin_did(self) -> str:
        admin_handle = self.config.get_admin_handle()

        if not self.admin_did:
            id_resolver = IdResolver()
            self.admin_did = id_resolver.handle.resolve(admin_handle)

        if self.admin_did:
            self.config.logger.debug(f"  Resolved admin user: {admin_handle}: {self.admin_did}")
            return self.admin_did
        
        self.config.logger.warning(f"Could not resolve admin user: {admin_handle}")
        return ""

    def __get_admin_convo(self) -> models.ChatBskyConvoDefs.ConvoView:
        try:
            admin_did = self.__get_admin_did()
            params = models.ChatBskyConvoGetConvoForMembers.Params(members=[admin_did])
            convo = self.dm.get_convo_for_members(params=params).convo
            self.config.logger.debug(f"  Found chat with admin {self.config.get_admin_handle().split(".")[0]}")
            return convo
        except AtProtocolError as e:
            self.config.logger.error(f"Error fetching conversations: {e}")
            raise

    def __get_admin_messages(self, convo) -> models.ChatBskyConvoGetMessages.Response:
        try:
            response = self.dm.get_messages(models.ChatBskyConvoGetMessages.Params(convo_id=convo.id))
            self.config.logger.debug(f"  Retrieved {len(response.messages)} messages in the chat")
            return response
        except AtProtocolError as e:
            self.config.logger.error(f"Error fetching messages: {e}")
            raise

    def __parse_messages(self, messages: models.ChatBskyConvoGetMessages.Response, convo_id: str) -> bool:
        did_something = False
        for message in messages.messages:
            if isinstance(message, models.ChatBskyConvoDefs.MessageView):
                if (message.reactions and message.sender.did == self.admin_did) or message.sender.did == self.config.get_bsky_account().get_did():
                    self.dm.delete_message_for_self(models.ChatBskyConvoDeleteMessageForSelf.Data(convo_id=convo_id, message_id=message.id))
                    did_something = True
                if not message.reactions and message.sender.did == self.admin_did:
                    text = message.text
                    if (response := self.command_handler.parse_commands(text)):
                        # A command was found and we got a response
                        if response:
                            # react with a thumbs-up to show the command was successful
                            try:
                                self.dm.add_reaction(models.ChatBskyConvoAddReaction.Data(convo_id=convo_id, message_id=message.id, value="👍"))
                                self.dm.delete_message_for_self(models.ChatBskyConvoDeleteMessageForSelf.Data(convo_id=convo_id, message_id=message.id))
                                did_something = True
                            except AtProtocolError as e:
                                self.config.logger.warning(f"Error marking completed command: {e}")
                        
                        if response.response and len(response.response) > 0 and len(response.response) < 999:
                            try:
                                self.dm.send_message(models.ChatBskyConvoSendMessage.Data(
                                    convo_id=convo_id, 
                                    message=models.ChatBskyConvoDefs.MessageInput(text=response.response)))
                                did_something = True
                            except AtProtocolError as e:
                                self.config.logger.error(f"Error replying to convo: {e}")
                        # can only post 1000 grapheme messages, so this splits it if its longer:
                        elif response.response and len(response.response) > 999:
                            try:
                                message_texts = split_pipe_string(response.response)
                                msg_datas = []
                                for msg_txt in message_texts:
                                    message_data = models.ChatBskyConvoSendMessageBatch.BatchItem(
                                        convo_id=convo_id,
                                        message=models.ChatBskyConvoDefs.MessageInput(text=msg_txt)
                                    )
                                    msg_datas.append(message_data)
                                self.dm.send_message_batch(models.ChatBskyConvoSendMessageBatch.Data(items=msg_datas))
                                did_something = True
                            except AtProtocolError as e:
                                self.config.logger.error(f"Error replying to convo: {e}")
                    else:
                        # No command found, react with a question mark to indicate unrecognized command
                        try:                            
                            self.dm.add_reaction(models.ChatBskyConvoAddReaction.Data(convo_id=convo_id, message_id=message.id, value="❓"))
                            self.dm.delete_message_for_self(models.ChatBskyConvoDeleteMessageForSelf.Data(convo_id=convo_id, message_id=message.id))
                            did_something = True
                        except AtProtocolError as e:
                            self.config.logger.warning(f"Error marking unrecognized command: {e}")
        return did_something

def split_pipe_string(s: str, max_len: int = 999) -> list[str]:
    parts = s.split('|')
    chunks = []
    current = ""

    for part in parts:
        # If current is empty, try starting with this part
        if not current:
            if len(part) > max_len:
                raise ValueError(f"Single segment exceeds max length: {part[:50]}...")
            current = part
        else:
            # Try adding "|part" to the current chunk
            candidate = current + "|" + part
            if len(candidate) <= max_len:
                current = candidate
            else:
                chunks.append(current)
                if len(part) > max_len:
                    raise ValueError(f"Single segment exceeds max length: {part[:50]}...")
                current = part

    if current:
        chunks.append(current)

    return chunks

            
