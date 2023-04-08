from __future__ import annotations

from abc import ABC

from pydantic import BaseModel, Field


class ApiObject(BaseModel, ABC):
    ...

class Update(ApiObject):
    update_id: int
    message: Message | None


class Message(ApiObject):
    message_id: int
    date: int
    from_user: User | None = Field(alias='from')
    chat: Chat
    text: str | None
    entities: list[MessageEntity] | None


class Chat(ApiObject):
    id: int


class User(ApiObject):
    id: int
    first_name: str
    last_name: str | None
    username: str | None


class MessageEntity(ApiObject):
    type: str
    offset: int
    length: int
    url: str | None
    user: User | None
    language: str | None
    custom_emoji_id: str | None


Update.update_forward_refs()
Message.update_forward_refs()
Chat.update_forward_refs()
User.update_forward_refs()
MessageEntity.update_forward_refs()