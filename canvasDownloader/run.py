from io import BytesIO
from typing import Optional
import requests
import time
import threading
from PIL import Image
from pathlib import Path
import logging

_ENDPOINT_URL = "https://place.geoxor.moe/api/board-image"
_BASE_PATH_OUTPUT_FOLDER_1M = "board-images-60s/"
_BASE_PATH_OUTPUT_FOLDER_15S = "board-images-15s/"

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def createFolders() -> None:
    """
    Creates the folders for the images.
    """
    logging.info("Creating folders...")
    Path(_BASE_PATH_OUTPUT_FOLDER_15S).mkdir(parents=True, exist_ok=True)
    Path(_BASE_PATH_OUTPUT_FOLDER_1M).mkdir(parents=True, exist_ok=True)

def downloadImage() -> Optional[BytesIO]:
    """
    Downloads the image from the API endpoint and returns it as a BytesIO object.
    """
    response = requests.get(_ENDPOINT_URL)
    logging.debug(f"Got repspone from the API with status code {response.status_code} in {round(response.elapsed.total_seconds(), 4)} seconds.")
    if response.status_code != 200:
        return None
    return BytesIO(response.content)

def saveImage(image: BytesIO, path: Path) -> None:
    """
    Saves the image to the given path.
    """
    logging.debug(f"Saving image to {path}...")
    startImageSave = time.time()
    image.seek(0)
    image = Image.open(image)
    image.save(path, format="PNG", quality=100, optimize=True)
    logging.debug(f"Image saved to {path} in {round(time.time() - startImageSave, 4)} seconds.")

def getNewImagePath(basePath: Path) -> Path:
    """
    Returns a new path for the image.
    """
    return Path(basePath) / f"place_geoxor_moe-{int(time.time())}.png"

def executeDownloader(path: Path) -> None:
    """
    Downloads the image and saves it to the given path.
    """
    logging.debug("Executing downloader...")
    image = downloadImage()
    if image is None:
        logging.error("Could not download image.")
        return
    saveImage(image, path)
    logging.info(f"Image saved to {path}.")

def scheduleDownloader(basePath: Path, timeInterval: float = 60) -> None:
    """
    Schedules the downloader to run every minute.
    """
    startTime = time.time()
    while True:
        executeDownloader(getNewImagePath(basePath))
        logging.debug(f"Waiting {round(timeInterval - ((time.time() - startTime) % timeInterval), 4)} seconds before next download...")
        time.sleep(timeInterval - ((time.time() - startTime) % timeInterval))

def main():
    """
    Main function.
    """
    createFolders()
    logging.info("Starting downloader...")
    t1 = threading.Thread(
        target=scheduleDownloader,
        args=(_BASE_PATH_OUTPUT_FOLDER_15S, 15,))
    t1.start()
    t2 = threading.Thread(
        target=scheduleDownloader,
        args=(_BASE_PATH_OUTPUT_FOLDER_1M, 60,))
    t2.start()

if __name__ == "__main__":
    main()
