from datetime import datetime
from functools import partial
from typing import Any, Callable

import requests
from loguru import logger
from pydantic import TypeAdapter

from tg_api import errors, objects
from tg_api.config import ApiConf


class BaseClient:
    def __init__(
        self,
        config: ApiConf | None = None,
        verbose: bool = False,
    ) -> None:
        self.config = config if config else ApiConf()
        self.verbose = verbose
        self._session = requests.Session()

    @property
    def session(self) -> requests.Session:
        return self._session

    def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 0,
        allowed_updates: list | str = "chat_member",
    ) -> list[objects.Update]:
        params = {
            "offset": offset,
            "limit": limit,
            "timeout": timeout,
            "allowed_updates": allowed_updates,
        }
        response = self.session.post(
            url=self.config.url + "/getUpdates",
            params=params,
        )
        if response is None:
            logger.warning("Request hasn't returned any response")
        elif response.status_code != 200:
            logger.error(f"Bad request: {response.status_code, response.text}")
        elif self.verbose:
            logger.info("Succesfull request")
        return response

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        message_thread_id: int | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> requests.Response:
        params = {
            "chat_id": chat_id,
            "text": text,
            "message_thread_id": message_thread_id,
            "reply_to_message_id": reply_to_message_id,
        }
        if reply_markup:
            params["reply_markup"] = reply_markup
        response = self.session.post(
            url=self.config.url + "/sendMessage",
            params=params,
        )
        if response is None:
            logger.warning("Request hasn't returned any response")
        elif response.status_code != 200:
            logger.error(f"Bad request: {response.status_code, response.text}")
        elif self.verbose:
            logger.info("Succesfull request")
        return response

    def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        reply_markup: dict[str, Any] = {},
    ) -> requests.Response:
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": reply_markup,
        }
        response = self.session.post(
            url=self.config.url + "/editMessageText",
            params=params,
        )
        if response is None:
            logger.warning("Request hasn't returned any response")
        elif response.status_code != 200:
            logger.error(f"Bad request: {response.status_code, response.text}")
        elif self.verbose:
            logger.info("Succesfull request")
        return response

    def edit_message_reply_markup(
        self,
        chat_id: int | str,
        message_id: int,
        reply_markup: dict[str, Any] = {},
    ) -> requests.Response:
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": reply_markup,
        }
        response = self.session.post(
            url=self.config.url + "/editMessageReplyMarkup",
            params=params,
        )
        if response is None:
            logger.warning("Request hasn't returned any response")
        elif response.status_code != 200:
            logger.error(f"Bad request: {response.status_code, response.text}")
        elif self.verbose:
            logger.info("Succesfull request")
        return response


class ValidatorClient(BaseClient):
    def __init__(
        self,
        config: ApiConf | None = None,
        verbose: bool = False,
        offset_autoupdate: bool = True,
    ) -> None:
        super().__init__(config, verbose)
        self.offset_autoupdate = offset_autoupdate
        self._offset = 0

    def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 0,
        allowed_updates: list | str = "chat_member",
    ) -> list[objects.Update]:
        resp = super().get_updates(
            offset or self._offset, limit, timeout, allowed_updates
        )
        if resp is not None and resp.status_code == 200:
            expected = TypeAdapter(list[objects.Update])
            updates = expected.validate_python(resp.json()["result"])
            if self.offset_autoupdate and updates:
                self._offset = max(u.update_id for u in updates) + 1
            return updates

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        message_thread_id: int | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: objects.InlineKeyboardMarkup | None = None,
    ) -> objects.Message | None:
        resp = super().send_message(
            chat_id,
            text,
            message_thread_id,
            reply_to_message_id,
            reply_markup.model_dump_json(exclude_none=True) if reply_markup else None,
        )
        if resp is not None and resp.status_code == 200:
            return objects.Message.model_validate(resp.json()["result"])

    def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        reply_markup: objects.InlineKeyboardMarkup | None = None,
    ) -> objects.Message | None:
        resp = super().edit_message_text(
            chat_id,
            message_id,
            text,
            reply_markup.model_dump_json(exclude_none=True) if reply_markup else {},
        )
        if resp is not None and resp.status_code == 200:
            return objects.Message.model_validate(resp.json()["result"])

    def edit_message_reply_markup(
        self,
        chat_id: int | str,
        message_id: int,
        reply_markup: objects.InlineKeyboardMarkup | None = None,
    ) -> objects.Message | None:
        resp = super().edit_message_reply_markup(
            chat_id,
            message_id,
            reply_markup.model_dump_json(exclude_none=True) if reply_markup else {},
        )
        if resp is not None and resp.status_code == 200:
            return objects.Message.model_validate(resp.json()["result"])


class HandlerClient(ValidatorClient):
    def __init__(
        self,
        config: ApiConf | None = None,
        verbose: bool = False,
        offset_autoupdate: bool = True,
        min_query_delay: int = 50000,
        update_handlers: set[Callable[[objects.Update], None]] = set(),
    ):
        super().__init__(config, verbose, offset_autoupdate)
        self.min_query_delay = min_query_delay
        self.update_handlers = update_handlers
        self._queue: list[tuple[Callable[[], Any], Callable[[Any], None]]] = []
        self._last_query: datetime = datetime.now()

    def general_handler(self, updates: list[objects.Update]) -> None:
        for u in updates:
            for h in self.update_handlers:
                h(u)

    def tick(self) -> None:
        if (datetime.now() - self._last_query).microseconds < self.min_query_delay:
            return
        if self._queue:
            task, callback = self._queue.pop(0)
        else:
            task = super().get_updates
            callback = self.general_handler
        callback(task())
        self._last_query = datetime.now()

    def send_message(
        self,
        callback: Callable[[objects.Message], None] = lambda _: None,
        *,
        chat_id: int | str,
        text: str,
        message_thread_id: int | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: objects.InlineKeyboardMarkup | None = None,
    ) -> None:
        self._queue.append(
            (
                partial(
                    super().send_message,
                    chat_id,
                    text,
                    message_thread_id,
                    reply_to_message_id,
                    reply_markup,
                ),
                callback,
            )
        )

    def edit_message_text(
        self,
        callback: Callable[[objects.Message], None] = lambda _: None,
        *,
        chat_id: int | str,
        message_id: int,
        text: str,
        reply_markup: objects.InlineKeyboardMarkup | None = None,
    ) -> None:
        self._queue.append(
            (
                partial(
                    super().edit_message_text,
                    chat_id,
                    message_id,
                    text,
                    reply_markup,
                ),
                callback,
            )
        )

    def edit_message_reply_markup(
        self,
        callback: Callable[[objects.Message], None] = lambda _: None,
        *,
        chat_id: int | str,
        message_id: int,
        reply_markup: objects.InlineKeyboardMarkup | None = None,
    ) -> None:
        self._queue.append(
            (
                partial(
                    super().edit_message_reply_markup,
                    chat_id,
                    message_id,
                    reply_markup,
                ),
                callback,
            )
        )
