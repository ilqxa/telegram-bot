from __future__ import annotations

from abc import ABC

from pydantic import BaseModel, Field


class ApiObject(BaseModel, ABC):
    ...

class Update(ApiObject):
    update_id: int
    message: Message | None
    poll: Poll | None
    poll_answer: PollAnswer | None


class Message(ApiObject):
    message_id: int
    date: int
    from_user: User | None = Field(alias='from')
    chat: Chat
    text: str | None
    entities: list[MessageEntity] | None
    poll: Poll | None


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


class Poll(ApiObject):
    id: str
    question: str
    options: list[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str
    allows_multiple_answers: bool
    correct_option_id: int | None
    explanation: str | None
    explanation_entities: list[MessageEntity] | None
    open_period: int | None
    close_date: int | None


class PollOption(ApiObject):
    text: str | None
    voter_count: int


class PollAnswer(ApiObject):
    poll_id: str
    user: User
    option_ids: list[int]


Update.update_forward_refs()
Message.update_forward_refs()
Chat.update_forward_refs()
User.update_forward_refs()
MessageEntity.update_forward_refs()
Poll.update_forward_refs()
PollOption.update_forward_refs()
PollAnswer.update_forward_refs()