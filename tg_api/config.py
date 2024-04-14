from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiConf(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    api_key: str = Field(alias="tg_api_key")
    api_url: str = "https://api.telegram.org/bot"
    headers: dict[str, str] = {"Content-Type": "application/json"}

    @property
    def url(self) -> str:
        return self.api_url + self.api_key
