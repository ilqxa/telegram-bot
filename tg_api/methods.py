import io
import json
from typing import Any, Literal

import requests
from loguru import logger
from pydantic import TypeAdapter
from requests import Response

from tg_api.config import ApiConf
from tg_api.objects import (BotCommand, BotCommandScope, Message,
                            MessageEntity, Update)

config = ApiConf()  # type: ignore


def make_request(
    method: str,
    params: dict[str, Any],
    config: ApiConf = config,
) -> Response | None:
    with requests.Session() as session:
        response = session.post(
            url=config.url + "/" + method,
            headers=config.headers,
            params=params,
        )

    if response is None:
        logger.warning("Request hasn't returned any response")
        return None
    elif response.status_code != 200:
        logger.warning(f"Bad request: {response.status_code, response.text}")
        return response
    else:
        logger.info("Succesfull request")
        return response


def get_updates(
    offset: int | None = None,
    limit: int = 100,
    timeout: int = 0,
    allowed_updates: list | str = "chat_member",
) -> list[Update]:
    params = {
        "offset": offset,
        "limit": limit,
        "timeout": timeout,
        "allowed_updates": allowed_updates,
    }
    if resp := make_request(method="getUpdates", params=params):
        logger.info("Parsing result as list of updates")
        result = json.loads(resp.content.decode("utf-8"))["result"]
        expected = TypeAdapter(list[Update])
        return expected.validate_python(result)
    else:
        return []


def send_message(
    chat_id: int | str,
    text: str,
    message_thread_id: int | None = None,
    parse_mode: Literal["MarkdownV2", "Markdown", "HTML"] = "MarkdownV2",
    entities: list[MessageEntity] | None = None,
    disable_web_page_preview: bool | None = None,
    disable_notification: bool | None = None,
    protect_content: bool | None = None,
    reply_to_message_id: int | None = None,
    allow_sending_without_reply: bool | None = None,
    reply_markup: dict[str, Any] | None = None,
) -> Message | None:
    params = {
        "chat_id": chat_id,
        "text": text,
        "message_thread_id": message_thread_id,
        "parse_mode": parse_mode,
        "entites": entities,
        "disable_web_page_preview": disable_web_page_preview,
        "disable_notification": disable_notification,
        "protect_content": protect_content,
        "reply_to_message_id": reply_to_message_id,
        "allow_sending_without_reply": allow_sending_without_reply,
    }
    if reply_markup:
        params["reply_markup"] = reply_markup

    resp = make_request(method="sendMessage", params=params)
    if resp is not None and resp.status_code == 200:
        return Message.model_validate(resp.json()['result'])


def send_photo(
    chat_id: int | str,
    photo: io.BytesIO | str,
    message_thread_id: int | None = None,
    caption: str | None = None,
    has_spoiler: bool = False,
    reply_to_message_id: int | None = None,
    reply_markup: dict[str, Any] | None = None,
) -> Message:
    params = {
        "chat_id": chat_id,
        "photo": photo,
        "message_thread_id": message_thread_id,
        "caption": caption,
        "has_spoiler": has_spoiler,
        "reply_to_message_id": reply_to_message_id,
    }
    if reply_markup:
        params["reply_markup"] = reply_markup

    resp = make_request(method="sendPhoto", params=params)
    if resp is not None and resp.status_code == 200:
        return Message.model_validate(resp.json()['result'])


def send_poll(
    chat_id: int | str,
    question: str,
    options: list[str],
    message_thread_id: int | None = None,
    is_anonymous: bool = True,
    type: Literal["quiz", "regular"] = "regular",
    allows_multiple_answers: bool = True,
    correct_option_id: bool | None = None,
    explanation: str | None = None,
    explanation_parse_mode: str | None = None,
    explanation_entities: list[MessageEntity] | None = None,
    open_period: int | None = None,
    close_date: int | None = None,
    is_closed: bool | None = None,
    disable_notification: bool | None = None,
    protect_content: bool | None = None,
    reply_to_message_id: int | None = None,
    allow_sending_without_reply: bool | None = None,
    reply_markup: dict[str, Any] | None = None,
) -> bool:
    params = {
        "chat_id": chat_id,
        "question": question,
        "options": options,
        "message_thread_id": message_thread_id,
        "is_anonymous": is_anonymous,
        "type": type,
        "allows_multiple_answers": allows_multiple_answers,
        "correct_option_id": correct_option_id,
        "explanation": explanation,
        "explanation_parse_mode": explanation_parse_mode,
        "explanation_entities": explanation_entities,
        "open_period": open_period,
        "close_date": close_date,
        "is_closed": is_closed,
        "disable_notification": disable_notification,
        "protect_content": protect_content,
        "reply_to_message_id": reply_to_message_id,
        "allow_sending_without_reply": allow_sending_without_reply,
    }
    if reply_markup:
        params["reply_markup"] = reply_markup

    resp = make_request(method="sendPoll", params=params)
    return resp is not None and resp.status_code == 200


def answer_callback_query(
    callback_query_id: str,
    text: str | None = None,
    show_alert: bool = False,
    url: str | None = None,
    cache_time: int = 0,
) -> bool:
    params = {
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": show_alert,
        "url": url,
        "cache_time": cache_time,
    }

    resp = make_request(method="answerCallbackQuery", params=params)
    return resp is not None and resp.status_code == 200


def forward_message(
    chat_id: int | str,
    from_chat_id: int | str,
    message_id: int,
    message_thread_id: int | None,
    disable_notification: bool | None = None,
    protect_content: bool | None = None,
) -> bool:
    params = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        "message_thread_id": message_thread_id,
        "disable_notification": disable_notification,
        "protect_content": protect_content,
    }

    resp = make_request(method="forwardMessage", params=params)
    return resp is not None and resp.status_code == 200


def set_my_commands(
    commands: list[BotCommand],
    scope: BotCommandScope | None = None,
    language_code: str | None = None,
) -> bool:
    params: dict[str, Any] = {
        "commands": json.dumps([c.dict() for c in commands]),
    }
    if scope:
        params["scope"] = scope.json()
    if language_code:
        params["language_code"] = language_code

    resp = make_request(method="setMyCommands", params=params)
    return resp is not None and resp.status_code == 200


def delete_my_commands(
    scope: BotCommandScope | None = None,
    language_code: str | None = None,
) -> bool:
    params: dict[str, Any] = {}
    if scope:
        params["scope"] = scope.json()
    if language_code:
        params["language_code"] = language_code

    resp = make_request(method="deleteMyCommands", params=params)
    return resp is not None and resp.status_code == 200


def get_my_commands(
    scope: BotCommandScope | None = None,
    language_code: str | None = None,
) -> list[BotCommand]:
    params: dict[str, Any] = {}
    if scope:
        params["scope"] = scope.json()
    if language_code:
        params["language_code"] = language_code

    if resp := make_request(method="getMyCommands", params=params):
        result = json.loads(resp.content.decode("utf-8"))["result"]
        expected = TypeAdapter(list[BotCommand])
        return expected.validate_python(result)
    else:
        return []
