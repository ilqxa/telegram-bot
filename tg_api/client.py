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
    ) -> requests.Response:
        params = {
            "chat_id": chat_id,
            "text": text,
            "message_thread_id": message_thread_id,
        }
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
        limit: int = 100,
        timeout: int = 0,
        allowed_updates: list | str = "chat_member",
    ) -> list[objects.Update]:
        resp = super().get_updates(self._offset, limit, timeout, allowed_updates)
        if resp is not None and resp.status_code == 200:
            expected = TypeAdapter(list[objects.Update])
            updates = expected.validate_python(resp.json()["result"])
            if updates:
                self._offset = updates[-1].update_id + 1
            return updates

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        message_thread_id: int | None = None,
    ) -> objects.Message:
        resp = super().send_message(chat_id, text, message_thread_id)
        if resp is not None and resp.status_code == 200:
            return objects.Message.model_validate(resp.json()["result"])


class QueueClient(ValidatorClient):
    def __init__(
        self,
        config: ApiConf | None = None,
        verbose: bool = False,
        offset_autoupdate: bool = True,
    ):
        super().__init__(config, verbose, offset_autoupdate)
        self.queue: list[Callable[..., Any]] = []

    def tick(self) -> Any | None:
        if self.queue:
            task = self.queue.pop(0)
            res = task()
            # if isinstance(res, errors.Error):
            #     self.queue.insert(0, task)
            return res

    def get_updates(
        self,
        limit: int = 100,
        timeout: int = 0,
        allowed_updates: list | str = "chat_member",
    ) -> None:
        self.queue.append(
            partial(super().get_updates, limit, timeout, allowed_updates)
        )

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        message_thread_id: int | None = None,
    ) -> None:
        self.queue.append(
            partial(super().send_message, chat_id, text, message_thread_id)
        )


class HandlerClient(QueueClient):
    def __init__(
        self,
        config: ApiConf | None = None,
        verbose: bool = False,
        handlers: set[Callable[[objects.Update], None]] = set(),
    ):
        super().__init__(config, verbose)
        self.handlers = handlers

    def tick(self) -> None:
        res = super().tick()
        if isinstance(res, list) and all([isinstance(i, objects.Update) for i in res]):
            for upd in res:
                for h in self.handlers:
                    h(upd)
