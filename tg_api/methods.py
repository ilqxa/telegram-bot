import json
from typing import Any

import requests
from objects import Update, MessageEntity
from pydantic import HttpUrl, parse_obj_as
from config import ApiConf


config = ApiConf()  # type: ignore

def make_request(
    method: str,
    params: dict[str, Any],
    config: ApiConf = config,
) -> Any:
    with requests.Session() as session:
        response = session.post(
            url=config.url + method,
            headers=config.headers,
            json=params,
        )
    
    if response is None:
        return
    elif response.status_code != 200:
        return
    else:
        return json.loads(response.content.decode('utf-8'))['result']

def get_updates(
    offset: int | None = None,
    limit: int = 100,
    timeout: int = 0,
    allowed_updates: list | str = 'chat_member',
) -> list[Update] | None:
    params = {
        'offset': offset,
        'limit': limit,
        'timeout': timeout,
        'allowed_updates': allowed_updates,
    }
    result = make_request(method='getUpdates', params=params)
    if result:
        return parse_obj_as(list[Update], result)
    
def send_message(
    chat_id: int | str,
    text: str,
    parse_mode: str = 'MarkdownV2',
    entities: list[MessageEntity] | None = None,
    reply_to_message_id: int | None = None,
) -> None:
    params = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
        'entites': entities,
        'reply_to_message_id': reply_to_message_id,
    }
    result = make_request(method='sendMessage', params=params)