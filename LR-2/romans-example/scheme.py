from pydantic import BaseModel, BaseSettings, Field


class Settings(BaseSettings):
    token: str = Field(env="VK_TOKEN")
    folder: str = Field(env="FOLDER")
    domain: str = Field(env="DOMAIN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Album(BaseModel):
    id: int
    title: str
    owner_id: int
    size: int
