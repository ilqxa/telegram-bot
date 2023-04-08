from pydantic import BaseSettings, Field


class ApiConf(BaseSettings):
    api_key: str = Field(env='TG_API_KEY')
    api_url: str = 'https://api.telegram.org/bot'
    headers: dict[str, str] = {'Content-Type': 'application/json'}

    @property
    def url(self) -> str:
        return self.api_url + self.api_key
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'