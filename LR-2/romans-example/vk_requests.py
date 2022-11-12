import os
from tqdm.auto import tqdm

from scheme import Album, Settings
from vk_api import VKApi
import requests

settings = Settings()
vk_api = VKApi(settings.token)


def get_users(group_domain: str, fields: list[str] | None = None) -> list[dict[str, str]]:
    fields_req = ",".join(fields) if fields else ""
    response = vk_api.get("groups.getMembers", group_id=group_domain, count=1)
    try:
        count = response.json()["response"]["count"]
    except KeyError:
        print(response.json())
        raise KeyError
    members = []
    for i in tqdm(range(count // 1000 + 1)):
        response = vk_api.get(
            "groups.getMembers",
            group_id=group_domain,
            count=1000,
            offset=i * 1000,
            fields=fields_req,
        )
        members.extend(response.json()["response"]["items"])
    return members


def get_owner_id(domain: str) -> int:
    response = vk_api.get("groups.getById", group_id=domain)
    owner_id = -response.json()["response"][0]["id"]
    return owner_id


def get_albums(owner_id: int) -> list[Album]:
    response = vk_api.get("photos.getAlbums", owner_id=owner_id)
    response_albums = response.json()["response"]["items"]
    albums = []
    for album in response_albums:
        albums.append(
            Album(
                id=album["id"],
                owner_id=album["owner_id"],
                title=album["title"],
                size=album["size"],
            )
        )
    return albums


def get_photos_urls(album: Album) -> list[str]:
    urls = []
    for i in range(album.size // 1000 + 1):
        album_data = vk_api.get(
            "photos.get",
            album_id=album.id,
            owner_id=album.owner_id,
            count=1000,
            offset=i * 1000,
        ).json()["response"]
        for photo in album_data["items"]:
            urls.append(max(photo["sizes"], key=lambda x: x.get("height")))
    return urls


def download_photos(url: list[str], album: Album) -> None:
    path = os.path.join(settings.folder, album.title)
    if not os.path.exists(path):
        os.mkdir(path)
    for photo in tqdm(url, desc=path):
        response = requests.get(photo["url"])
        file_name = photo["url"].split("/")[-1].split("?")[0]
        with open(os.path.join(path, file_name), "wb") as f:
            f.write(response.content)


def main():
    if not os.path.exists(settings.folder):
        os.mkdir(settings.folder)
    owner_id = get_owner_id(settings.domain)
    albums = get_albums(owner_id)
    for album in tqdm(albums, disable=True):
        photos_urls = get_photos_urls(album)
        download_photos(photos_urls, album)


if __name__ == "__main__":
    get_users("hseperm")
    main()
