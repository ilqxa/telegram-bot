from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Update(BaseModel):
    update_id: int
    message: Message | None = None
    channel_post: Message | None = None
    poll: Poll | None = None
    poll_answer: PollAnswer | None = None
    callback_query: CallbackQuery | None = None


class CallbackQuery(BaseModel):
    id: str
    from_user: User = Field(alias="from")
    message: Message | None = None
    inline_message_id: str | None = None
    chat_instance: str | None = None
    data: str | None = None
    game_short_name: str | None = None


class Message(BaseModel):
    message_id: int
    message_thread_id: int | None = None
    date: int
    from_user: User | None = Field(alias="from")
    chat: Chat
    text: str | None = None
    entities: list[MessageEntity] | None = None
    poll: Poll | None = None


class Chat(BaseModel):
    id: int
    type: Literal["private", "group", "supergroup", "channel"]
    title: str | None = None


class User(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None


class MessageEntity(BaseModel):
    type: str
    offset: int
    length: int
    url: str | None = None
    user: User | None = None
    language: str | None = None
    custom_emoji_id: str | None = None


class Poll(BaseModel):
    id: str
    question: str
    options: list[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str
    allows_multiple_answers: bool
    correct_option_id: int | None = None
    explanation: str | None = None
    explanation_entities: list[MessageEntity] | None = None
    open_period: int | None = None
    close_date: int | None = None


class PollOption(BaseModel):
    text: str | None = None
    voter_count: int


class PollAnswer(BaseModel):
    poll_id: str
    user: User
    option_ids: list[int]


class InlineKeyboardMarkup(BaseModel):
    inline_keyboard: list[list[InlineKeyboardButton]]


class InlineKeyboardButton(BaseModel):
    text: str
    url: str | None = None
    callback_data: str | None = None
    web_app: str | None = None
    login_url: str | None = None
    switch_inline_query: str | None = None
    switch_inline_query_current_chat: str | None = None
    callback_game: str | None = None
    pay: bool | None = None


class BotCommand(BaseModel):
    command: str = Field(max_length=32)
    description: str = Field(max_length=256)


class BotCommandScope(BaseModel): ...


class BotCommandScopeChat(BotCommandScope):
    type: str = "chat"
    chat_id: int | str
