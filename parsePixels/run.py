from PIL import Image
from typing import List, Optional
import pydantic
from datetime import datetime
import requests
import pymongo
import time
import logging
import threading
import random
import urllib3
import os
from io import BytesIO

class PositionPixelModel(pydantic.BaseModel):
    x: int
    y: int

class StatisticsPixelModel(pydantic.BaseModel):
    totalPlaces: int
    lastPlace: datetime
    placesThisWeek: Optional[int]
    leaderboardRank: Optional[int]

class UserBadgeModel(pydantic.BaseModel):
   text: str
   style: str
   isRanking: Optional[bool]
   lowPriority: Optional[bool]
   isLowRanking: Optional[bool]

class PixelLatestInfoUserModel(pydantic.BaseModel):
    point: PositionPixelModel
    modified: datetime
    colour: str
    editorID: str
    isLatest: bool

class PixelInfoUserModel(pydantic.BaseModel):
    id: str
    username: str
    isOauth: bool
    creationDate: datetime
    admin: bool
    moderator: bool
    statistics: StatisticsPixelModel
    banned: bool
    deactivated: bool
    markedForDeletion: bool
    badges: List[UserBadgeModel]
    latestPixel: Optional[PixelLatestInfoUserModel]

class PixelInformationModel(pydantic.BaseModel):
    point: PositionPixelModel
    modified: datetime
    colour: str
    editorID: str
    user: Optional[PixelInfoUserModel]

class PixelInformationResponseModel(pydantic.BaseModel):
    pixel: Optional[PixelInformationModel]

class OnlineCountModel(pydantic.BaseModel):
    count: int

class OnlineCountResponseModel(pydantic.BaseModel):
    online: OnlineCountModel

class ChatMessageModel(pydantic.BaseModel):
    id: int
    date: datetime
    text: str
    position: PositionPixelModel
    user: PixelInfoUserModel

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

__DB = pymongo.MongoClient(os.environ["MONGODB_URI"])
__DB_PIXINFO = __DB["plcgxrm"]["pixels-info"]

_ENDPOINT_URL = "https://place.geoxor.moe"
_WORKERS_COUNT = 2

def addPixelToDatabase(pixel: PixelInformationResponseModel) -> int:
    try:
        if pixel.pixel is None:
            return 3
        _dbr = __DB_PIXINFO.insert_one(pixel.dict()["pixel"])
        return 0 if _dbr.inserted_id else 1
    except pymongo.errors.DuplicateKeyError:
        return 2

def getPixelInformation(x: int, y: int) -> Optional[PixelInformationResponseModel]:
    try:
        response = requests.get(
            url=f"{_ENDPOINT_URL}/api/pos-info",
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "PlaceGeoxorMoeParser/0.6.2 (Macintosh; OS X/12.3.0) URLSession/1858.112",
                "x-vprw-intfs-ver": "1.2",
            },
            params={
                "x": str(x),
                "y": str(y),
            },
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occured while getting info about pixel at ({x}, {y}): {e}")
        time.sleep(5)
        return getPixelInformation(x, y)
    except urllib3.exceptions.ProtocolError as e:
        logging.error(f"An error occured while getting info about pixel at ({x}, {y}): {e}")
        time.sleep(5)
        return getPixelInformation(x, y)
    except requests.exceptions.ConnectionError as e:
        logging.error(f"An error occured while getting info about pixel at ({x}, {y}): {e}")
        time.sleep(5)
        return getPixelInformation(x, y)
    if response.status_code == 200:
        try:
            return PixelInformationResponseModel(**response.json())
        except pydantic.error_wrappers.ValidationError as e:
            logging.error(f"A validation error occured while parsing response from API: {response.text} ;; {e}.")
            return None
    elif response.status_code == 503:
        time.sleep(0.5)
        return getPixelInformation(x, y)
    elif response.status_code == 400:
        time.sleep(1)
        return getPixelInformation(x, y)
    logging.error(f"The API returned an error while getting info about pixel at ({x}, {y}): {response.text}.")
    return None

def splitInChunks(input_list: list, nums: int) -> list[list]:
    for i in range(0, nums):
        yield input_list[i::nums]

def processBatchGetInfo(batch: list[tuple[int, int]], threadNumber: int) -> None:
    for coordinates in batch:
        rspap = getPixelInformation(coordinates[0], coordinates[1])
        if rspap is not None:
            dbabq = addPixelToDatabase(rspap)
            if dbabq == 0:
                logging.debug(f"Added info about pixel at ({coordinates[0]}, {coordinates[1]}) successfully.")
            elif dbabq == 1:
                logging.error(f"An error occured while adding info about pixel at ({coordinates[0]}, {coordinates[1]}).")
            elif dbabq == 2:
                logging.debug(f"Pixel at ({coordinates[0]}, {coordinates[1]}) did not change as it already exists in database.")
            elif dbabq == 3:
                logging.debug(f"Pixel at ({coordinates[0]}, {coordinates[1]}) was not found or is empty.")
        else:
            logging.error(f"An error occured while getting info about pixel at ({coordinates[0]}, {coordinates[1]}).")
        time.sleep(0.1 + random.randint(0, 2) / 10)

# def getUsersToCheckFromLeaderboard() -> Optional[List[str]]:
#     response = requests.get(
#         url=f"{_ENDPOINT_URL}/api/leaderboard",
#     )
#     if response.status_code == 200:
#         data = response.json()
#         if data["success"] and data["leaderboard"]:
#             allU = []
#             for user in data["leaderboard"]:
#                 allU.append(user["username"])
#             return allU
#         else:
#             logging.error(f"The API returned an error while getting leaderboard: {response.text}.")
#             return None
#     elif response.status_code == 503:
#         time.sleep(0.5)
#         return getUsersToCheckFromLeaderboard()
#     elif response.status_code == 400:
#         time.sleep(1)
#         return getUsersToCheckFromLeaderboard()
#     logging.error(f"The API returned an error while getting leaderboard: {response.text}.")
#     return None

# def getUserLastActivePixelCoordinates(username: str) -> Optional[PositionPixelModel]:
#     response = requests.get(
#         url=f"{_ENDPOINT_URL}/api/user/{username}",
#     )
#     if response.status_code == 200:
#         try:
#             return PixelInfoUserModel(**response.json()).latestPixel.point
#         except pydantic.error_wrappers.ValidationError:
#             return None
#         except KeyError:
#             logging.error(f"The API returned an error while getting info about user {username}: {response.text}.")
#     elif response.status_code == 503:
#         time.sleep(0.5)
#         return getUsersToCheckFromLeaderboard()
#     elif response.status_code == 400:
#         time.sleep(1)
#         return getUsersToCheckFromLeaderboard()
#     logging.error(f"The API returned an error while getting {username}'s user information: {response.text}.")
#     return None

# def main():
#     while True:
#         startTime = time.time()
#         users = list(getUsersToCheckFromLeaderboard())
#         logging.info(f"Found {len(users)} users to check from the leaderboard.")
#         if users is not None:
#             allPixelCoordinates = []
#             for user in users:
#                 pixloc = getUserLastActivePixelCoordinates(user)
#                 allPixelCoordinates.append((pixloc.x, pixloc.y)) if pixloc is not None else None
#             logging.info(f"Found {len(allPixelCoordinates)} pixels to check.")
#             if len(allPixelCoordinates) > 0:
#                 processBatchGetInfo(list(allPixelCoordinates), 1)
#             logging.info(f"Finished checking {len(allPixelCoordinates)} pixels from the leaderboard in {time.time() - startTime} seconds.")
#         else:
#             logging.warning(f"No users to check from the leaderboard.")
#         time.sleep(0.2 + random.randint(0, 2) / 10)

def downloadImage() -> Optional[Image.Image]:
    response = requests.get(
        f"{_ENDPOINT_URL}/api/board-image",
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "PlaceGeoxorMoeParser/0.6.5",
            "x-vprw-intfs-ver": "1.2",
            "x-vprw-parslinkplgemopar-ver": "0.4",
        },
    )
    logging.debug(f"Got repspone from the API with status code {response.status_code} in {round(response.elapsed.total_seconds(), 4)} seconds.")
    if response.status_code != 200:
        return downloadImage()
    image = BytesIO(response.content)
    image.seek(0)
    image = Image.open(image)
    return image

_PREVIOUS_IMAGE = downloadImage()

def compareTwoImagesAndDeterminesIfPixelHasChanged(image: Image.Image) -> List[tuple[int, int]]:
    global _PREVIOUS_IMAGE
    if _PREVIOUS_IMAGE is None:
        _PREVIOUS_IMAGE = image
        logging.warning(f"The previous image was not set, so it was set to the current image.")
        return []
    changedPixels = []
    startTimeCompare = time.time()
    for x in range(0, image.width):
        for y in range(0, image.height):
            if image.getpixel((x, y)) != _PREVIOUS_IMAGE.getpixel((x, y)):
                changedPixels.append((x, y))
    logging.debug(f"Compared {image.width * image.height} pixels in {round(time.time() - startTimeCompare, 4)} seconds.")
    _PREVIOUS_IMAGE = image
    return changedPixels

def main():
    while True:
        allPixelsCoordinates = compareTwoImagesAndDeterminesIfPixelHasChanged(downloadImage())
        logging.info(f"Found {len(allPixelsCoordinates)} pixels to check.")
        random.shuffle(allPixelsCoordinates)
        splittedCoordinates = list(splitInChunks(allPixelsCoordinates, _WORKERS_COUNT))
        for value, numThread in zip(splittedCoordinates, range(len(splittedCoordinates))):
            t = threading.Thread(
                target=processBatchGetInfo,
                args=(
                    value,
                    numThread,
                ),
            )
            t.start()
        time.sleep(4 + random.randint(0, 2))

if __name__ == "__main__":
    main()
