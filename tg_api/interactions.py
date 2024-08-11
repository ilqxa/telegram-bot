from tg_api.client import HandlerClient


class Interactor:
    def __init__(
        self,
        chat_id: int | str,
        message_thread_id: int | None = None,
        client: HandlerClient | None = None,
    ) -> None:
        self.client = client if client else HandlerClient()
        self.chat_id = chat_id
        self.message_thread_id = message_thread_id

    def send_notification(self): ...

    def send_answer_for_message(self, text: str, reply_to_message_id: int) -> None:
        self.client.send_message(
            chat_id=self.chat_id,
            text=text,
            message_thread_id=self.message_thread_id,
            reply_to_message_id=reply_to_message_id,
        )

    def update_message(self): ...

    def get_first_answer_for_message(self): ...

    def get_inline_button_click(self): ...
