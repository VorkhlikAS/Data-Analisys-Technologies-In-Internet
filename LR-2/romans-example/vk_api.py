import requests
from requests import Response


class VKApi:
    def __init__(self, token: str, v: str = "5.131"):
        self.TOKEN = token
        self.VERSION = v

    def get(self, url: str, **params) -> Response:
        default_params = {
            "access_token": self.TOKEN,
            "v": self.VERSION,
        }
        return requests.get(
            f"https://api.vk.com/method/{url}", params=default_params | params
        )
