from typing import Optional, Union
from starlette.requests import Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from typing import List, Optional
import pydantic
from enum import Enum
import os
import pymongo
from datetime import datetime
import logging


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


app = FastAPI(
    debug=False,
    title="place.geoxor.moe — Alternative API",
    description="Alternative API for place.geoxor.moe with statistics and more!",
    version="0.2.0",
    contact=pydantic.BaseModel(email="contact+geplapi@vapronva.pw")
)


__DB = pymongo.MongoClient(os.environ["MONGODB_URI"])

__DB_PIXINFO = __DB["plcgxrm"]["pixels-info"]
__DB_TLS = __DB["plcgxrm"]["timelapses"]
# __DB_CANVASIMAGES = __DB["plcgxrm"]["pixels-info"]


class ErrorTypes(Enum):
    """
    List (enum) of possible errors.
    """
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    ROUTE_NOT_FOUND = "ROUTE_NOT_FOUND"
    DATABASE_RESPONSE_ERROR = "DATABASE_RESPONSE_ERROR"
    MISSING_API_KEY = "MISSING_API_KEY"
    WRONG_API_KEY = "WRONG_API_KEY"
    REQUEST_VALIDATION_ERROR = "REQUEST_VALIDATION_ERROR"
    UNACCEPTABLE_INTERVAL_TIME = "UNACCEPTABLE_INTERVAL_TIME"

class ActionTypes(Enum):
    """
    List (enum) of possible actions.
    """
    ROOT_PATH_REQUEST = "ROOT_PATH_REQUEST"
    CHECK_STATUS = "CHECK_STATUS"
    GET_PIXELS_ALL = "GET_PIXELS_ALL"
    GET_CERTAIN_PIXEL = "GET_CERTAIN_PIXEL"
    GET_TIMELAPSE_ALL = "GET_TIMELAPSE_ALL"
    GET_LATEST_TIMELAPSE = "GET_LATEST_TIMELAPSE"
    GET_REDIRECT_LATEST_TIMELAPSE = "GET_REDIRECT_LATEST_TIMELAPSE"
    GET_ALL_USERS = "GET_ALL_USERS"
    GET_ALL_PIXELS_BY_USERNAME = "GET_ALL_PIXELS_BY_USERNAME"
    GET_ALL_PIXELS_BY_USERID = "GET_ALL_PIXELS_BY_USERID"

class ErrorBaseModel(pydantic.BaseModel):
    """
    Error base model for all errors.
    """
    name: ErrorTypes
    description: str
    class Config:
        use_enum_values = True

class BaseResponseModel(pydantic.BaseModel):
    """
    Base response model for all responses.
    """
    action: Optional[ActionTypes] = None
    result: Optional[dict] = None
    error: Optional[ErrorBaseModel]
    class Config:
        use_enum_values = True

class ErrorCustomBruhher(Exception):
    """
    Custom error exception for FastAPI HTTP-endpoints.
    """
    def __init__(self, response: BaseResponseModel, statusCode: int) -> None:
        """
        Initialize the exception.
        Response is a BaseResponseModel object, which contains the response; statusCode is an integer of the HTTP-status code.
        """
        self.response = response
        self.statusCode = statusCode


class PositionPixelModel(pydantic.BaseModel):
    """
    Pixel position model.
    """
    x: int
    y: int

class StatisticsPixelModel(pydantic.BaseModel):
    """
    Pixel statistics model.
    """
    totalPlaces: int
    lastPlace: datetime
    placesThisWeek: Optional[int]
    leaderboardRank: Optional[int]

class UserBadgeModel(pydantic.BaseModel):
    """
    User badge model.
    """
    text: str
    style: str
    isRanking: Optional[bool]
    lowPriority: Optional[bool]
    isLowRanking: Optional[bool]

class PixelLatestInfoUserModel(pydantic.BaseModel):
    """
    Latest info for a pixel by a user.
    """
    point: PositionPixelModel
    modified: datetime
    colour: str
    editorID: str
    isLatest: bool

class PixelInfoUserModel(pydantic.BaseModel):
    """
    User information model.
    """
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
    """
    One pixel information model.
    """
    point: PositionPixelModel
    modified: datetime
    colour: str
    editorID: str
    user: Optional[PixelInfoUserModel]


class VideoDownloadFormatsModel(pydantic.BaseModel):
    """
    Video download formats model.
    """
    h264: str
    h265: str
    prores: Optional[str] = None

class ArchiveImagesDownloadModel(pydantic.BaseModel):
    """
    Model for the download of the timelapse images.
    """
    zip_png: str

class CanvasTimelapseObjectModel(pydantic.BaseModel):
    """
    Model for single timelapse object.
    """
    name: str
    date: datetime
    interval_time: int
    downloadURLs: VideoDownloadFormatsModel
    snapshotURL: ArchiveImagesDownloadModel


def get_all_pixels() -> List[PixelInformationModel]:
    """
    Function to get all pixels from the database.
    """
    pixels = __DB_PIXINFO.find({})
    return [PixelInformationModel(**pixel) for pixel in pixels]

def get_pixel_by_coordinates(x: int, y: int) -> Optional[List[PixelInformationModel]]:
    """
    Funciton to get a pixel info by its coordinates.
    """
    pixel = __DB_PIXINFO.find({"point.x": x, "point.y": y})
    pixel = list(pixel)
    if pixel == 0:
        return None
    return [PixelInformationModel(**pixel) for pixel in pixel]


def add_timelapse_to_db(timelapse: CanvasTimelapseObjectModel) -> None:
    """
    Function to add a timelapse to the database.
    """
    __DB_TLS.insert_one(timelapse.dict())

def get_db_all_timelapses() -> List[CanvasTimelapseObjectModel]:
    """
    Function to get all timelapses from the database.
    """
    timelapses = __DB_TLS.find({})
    return [CanvasTimelapseObjectModel(**timelapse) for timelapse in timelapses]

def get_db_all_timelapses_by_itervaltime(interval_time: int) -> List[CanvasTimelapseObjectModel]:
    """
    Function to get all timelapses from the database by interval time.
    """
    timelapses = __DB_TLS.find({"interval_time": interval_time})
    return [CanvasTimelapseObjectModel(**timelapse) for timelapse in timelapses]

def get_db_latest_timelapse(interval_time: int) -> CanvasTimelapseObjectModel:
    """
    Function to get the latest timelapse from the database by interval time.
    """
    timelapse = __DB_TLS.find({"interval_time": interval_time}).sort("date", -1).limit(1)[0]
    return CanvasTimelapseObjectModel(**timelapse)


def get_db_all_users_by_latest_pixel() -> List[PixelInfoUserModel]:
    """
    Function to get all users from the database, sorted by the latest pixel.
    """
    users = [user["user"] for user in __DB_PIXINFO.find({}).sort("modified", -1)]
    usedUserIDs = set()
    for user in users:
        if user is not None and user["id"] not in usedUserIDs:
            usedUserIDs.add(user["id"])
            yield PixelInfoUserModel(**user)

def get_db_all_pixels_by_username(username: str) -> List[PixelInformationModel]:
    """
    Function to get all pixels from the database, sorted by the latest pixel.
    """
    pixels = __DB_PIXINFO.find({"user.username": username})
    return [PixelInformationModel(**pixel) for pixel in pixels]

def get_db_all_pixels_by_userid(userid: str) -> List[PixelInformationModel]:
    """
    Function to get all pixels from the database, sorted by the latest pixel.
    """
    pixels = __DB_PIXINFO.find({"editorID": userid})
    return [PixelInformationModel(**pixel) for pixel in pixels]


def check_for_proper_authentication_header(request: Request) -> bool:
    """
    Function to check if the request has a proper authentication header.
    """
    if "Authorization" not in request.headers:
        return False
    if request.headers["Authorization"] != os.environ["MASTER_KEY"]:
        return False
    return True


@app.exception_handler(ErrorCustomBruhher)
def custom_error_bruhher(request: Request, exc: ErrorCustomBruhher) -> JSONResponse:
    """
    Handles the response for the custom error.
    Returns JSONResponse with the error message.
    """
    return JSONResponse(status_code=exc.statusCode, content=exc.response.dict())

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(*_) -> JSONResponse:
    """
    Handles the response for the RequestValidationError.
    Returns JSONResponse with the error message.
    """
    return JSONResponse(
        status_code=400,
        content=BaseResponseModel(
            error=ErrorBaseModel(
                name=ErrorTypes.REQUEST_VALIDATION_ERROR,
                description="Ooops, your requset received a validation error. The error is either on our end or on your end. Please try again later.",
            )).dict())


@app.get("/", status_code=200, response_model=BaseResponseModel)
def main_root(request: Request):
    """
    Main endpoint for the root path.
    """
    return BaseResponseModel(
        action=ActionTypes.ROOT_PATH_REQUEST,
        result={"message": "This is the root of the API. I mean, you're already here, right? Well... Hi! Hope you're having a lovely day. If you have any questions, feel free to contact me at contact@vapronva.pw. Thank you for using the API! :)"},
        error=None)

@app.get("/status", status_code=200, response_model=BaseResponseModel)
def check_internal_status(request: Request):
    """
    Endpoint for checking the status of the API.
    """
    return BaseResponseModel(
        action=ActionTypes.CHECK_STATUS,
        result={"status": {"connections": {"database": "OK", "api": "OK"}}},
        error=None)


@app.get("/pixels/all", status_code=200, response_model=BaseResponseModel)
def get_all_pixels_historic_information(request: Request):
    """
    Endpoint for getting all pixels historic information.
    """
    if not check_for_proper_authentication_header(request):
        raise ErrorCustomBruhher(
            BaseResponseModel(
                action=ActionTypes.GET_PIXELS_ALL,
                result=None,
                error=ErrorBaseModel(
                    name=ErrorTypes.WRONG_API_KEY,
                    description="The provided API key is not correct.",
                )), 401)
    return BaseResponseModel(
        action=ActionTypes.GET_PIXELS_ALL,
        result={"pixels": get_all_pixels()},
        error=None)

@app.get("/pixels/{x}/{y}", status_code=200, response_model=BaseResponseModel)
def get_pixel_historic_information(request: Request, x: int, y: int):
    """
    Endpoint for getting historic information of a given pixel.
    """
    return BaseResponseModel(
        action=ActionTypes.GET_CERTAIN_PIXEL,
        result={"pixels": get_pixel_by_coordinates(x, y)},
        error=None)


@app.get("/timelapses/all", status_code=200, response_model=BaseResponseModel)
def get_all_timelapses(request: Request, interval_time: Optional[int] = None):
    """
    Endpoint for getting all timelapses.
    """
    match interval_time:
        case None:
            return BaseResponseModel(
                action=ActionTypes.GET_TIMELAPSE_ALL,
                result={"timelapses": get_db_all_timelapses()},
                error=None)
        case 15:
            return BaseResponseModel(
                action=ActionTypes.GET_TIMELAPSE_ALL,
                result={"timelapses": get_db_all_timelapses_by_itervaltime(15)},
                error=None)
        case 60:
            return BaseResponseModel(
                action=ActionTypes.GET_TIMELAPSE_ALL,
                result={"timelapses": get_db_all_timelapses_by_itervaltime(60)},
                error=None)
    raise ErrorCustomBruhher(
        BaseResponseModel(
            action=ActionTypes.GET_TIMELAPSE_ALL,
            result=None,
            error=ErrorBaseModel(
                name=ErrorTypes.UNACCEPTABLE_INTERVAL_TIME,
                description="The provided interval time is not acceptable. Only 60 and 15 are accepted.",
            )), 400)

@app.get("/timelapses/latest", status_code=200, response_model=BaseResponseModel)
def get_latest_timelapses(request: Request, interval_time: int = 60, redirectToH264: bool = False):
    """
    Endpoint for getting latest timelapse.
    """
    if not interval_time in [60, 15]:
        raise ErrorCustomBruhher(
            BaseResponseModel(
                action=ActionTypes.GET_LATEST_TIMELAPSE,
                result=None,
                error=ErrorBaseModel(
                    name=ErrorTypes.UNACCEPTABLE_INTERVAL_TIME,
                    description="The provided interval time is not acceptable. Only 60 and 15 are accepted.",
                )), 400)
    if redirectToH264:
        timelapse = get_db_latest_timelapse(interval_time)
        return RedirectResponse(url=timelapse.downloadURLs.h264, status_code=303)
    return BaseResponseModel(
        action=ActionTypes.GET_LATEST_TIMELAPSE,
        result={"timelapse": get_db_latest_timelapse(interval_time)},
        error=None)

@app.get("/users/all", status_code=200, response_model=BaseResponseModel)
def get_all_users(request: Request):
    """
    Endpoint to get all users with their latest information.
    """
    return BaseResponseModel(
        action=ActionTypes.GET_ALL_USERS,
        result={"users": list(get_db_all_users_by_latest_pixel())},
        error=None)

@app.get("/users/name/{username}", status_code=200, response_model=BaseResponseModel)
def get_all_pixels_by_username(request: Request, username: str):
    """
    Endpoint to get all pixels of a user by their username.
    """
    return BaseResponseModel(
        action=ActionTypes.GET_ALL_PIXELS_BY_USERNAME,
        result={"pixels": get_db_all_pixels_by_username(username)},
        error=None)

@app.get("/users/id/{userID}", status_code=200, response_model=BaseResponseModel)
def get_all_pixels_by_userid(request: Request, userID: str):
    """
    Endpoint to get all pixels of a user by their userID.
    """
    return BaseResponseModel(
        action=ActionTypes.GET_ALL_PIXELS_BY_USERID,
        result={"pixels": get_db_all_pixels_by_userid(userID)},
        error=None)
