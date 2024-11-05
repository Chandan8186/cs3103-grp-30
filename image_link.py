from datetime import timedelta, date
from flask import flash
import aiohttp
import asyncio

# Don't overwhelm the slow server
REQUEST_LIMIT = 25
# Unlikely to check email after 90 days
EXPIRY_DATE = (date.today() + timedelta(days=90)).strftime("%m/%d/%Y")

"""
A coroutine to generate a single image link.
"""
async def _make_image_link(session, unique_id) -> str:
    params = {"url": "https://upload.wikimedia.org/wikipedia/commons/c/ca/1x1.png",
              "type": "json",
              "private": "1",
              "expire": EXPIRY_DATE,
              # Ensures the input is a string, as there is no type checking for unique_id
              "custom": str(unique_id)}
    
    for i in range(3): # Retries
        if i > 0:
            asyncio.sleep(1)
        async with session.get("https://ulvis.net/API/write/get", params=params) as redirect:
            if not redirect.ok:
                print("make_image_links Error:", redirect.status)
                continue
                
            try:
                parsed_redirect = await redirect.json()
            except aiohttp.ContentTypeError:
                print("make_image_links Error:", redirect.status)
                continue

            if "data" not in parsed_redirect or "url" not in parsed_redirect["data"]:
                error_msg = f"make_image_links Error for {unique_id}."
                # Check if error message can be found
                if "data" in parsed_redirect and "status" in parsed_redirect["data"]:
                    error_msg += f" {parsed_redirect['data']['status']}."
                print(error_msg)
                continue

            return parsed_redirect["data"]["url"]

    # flash("Ulvis server is down... View stats may not function properly.")
    return "https://ulvis.net/" + str(unique_id)

"""
Asynchronously generates unique links for each unique id.
Usage: asyncio.run(make_image_links(unique_id_list))

Parameters:
unique_id_list (list[str]): List of unique ids.

Returns:
list[str]: List of unique links.
"""
async def make_image_links(unique_id_list) -> list[str]:
    conn = aiohttp.TCPConnector(limit=REQUEST_LIMIT)
    async with aiohttp.ClientSession(connector = conn) as session:
        coroutines = [_make_image_link(session, unique_id) for unique_id in unique_id_list]
        return await asyncio.gather(*coroutines)


"""
Manages obtaining image counts.
Unique ids are used to identify and retrieve links for getting image counts.
"""
class Image_Count_Manager:
    def __init__(self):
        self.unique_id_list = []
        self.session = None
        # Manually manage an event loop for this instance, to allow session (aiohttp.ClientSession)
        # to be persistent across each call of get_image_counts(), making it much more responsive.
        self.event_loop = asyncio.new_event_loop()
        self.event_loop.run_until_complete(self._create_session())

    def __del__(self):
        # Connector has to be manually closed since session.close() is a coroutine, and it may not be able
        # to run as event loops could be closed when exiting the program. The connector is then
        # manually detached to prevent false error messages of connector not being closed.
        self.session.connector.close()
        self.session.detach()
        self.event_loop.close()

    async def _create_session(self):
        conn = aiohttp.TCPConnector(limit=REQUEST_LIMIT)
        self.session = aiohttp.ClientSession(connector = conn)

    """
    Updates the unique ids which are used to obtain image view counts.
    """
    def update_unique_id_list(self, unique_id_list):
        self.unique_id_list = unique_id_list

    """
    A coroutine to obtain a single image count.
    """
    async def _get_image_count(self, unique_id) -> int:
        if unique_id == None:
            return "error"
        params = {"type": "json",
                # Ensures the input is a string, as there is no type checking for unique_id
                "id": str(unique_id)}

        for i in range(3): # Retries
            if i > 0:
                asyncio.sleep(1)
            async with self.session.get("https://ulvis.net/API/read/get", params=params) as redirect:
                if not redirect.ok:
                    print("Image_Link Error:", redirect.status)
                    continue

                try:
                    parsed_redirect = await redirect.json()
                except aiohttp.ContentTypeError:
                    print("Image_Link Error:", redirect.status)
                    continue

                if "data" not in parsed_redirect or "hits" not in parsed_redirect["data"]:
                    error_msg = f"Image_Link Error for {unique_id}."
                    # Check if error message can be found
                    if "error" in parsed_redirect and "msg" in parsed_redirect["error"]:
                        error_msg += f" {parsed_redirect['error']['msg']}."
                    print(error_msg)
                    continue

                return parsed_redirect["data"]["hits"]

        # flash("View stats failed to load for an email.")
        return "error"

    """
    Asynchronously gets image download count for each unique id.
    Usage: asyncio.run(_get_image_counts(unique_id_list))

    Parameters:
    unique_id_list (list[str]): List of unique ids.

    Returns:
    list[str]: List of image download counts.
    """
    async def _get_image_counts(self) -> list[str]:
        coroutines = [self._get_image_count(unique_id) for unique_id in self.unique_id_list]
        return await asyncio.gather(*coroutines)
    
    """
    Asynchronously gets image download count for each unique id in self.unique_id_list.
    """
    def get_image_counts(self) -> list[str]:
        try:
            coroutine = self._get_image_counts()
            image_counts = self.event_loop.run_until_complete(coroutine)
        except RuntimeError: # Previous loop still running
            coroutine.close()
            return []
        
        # Remove invalid ids to prevent unnecessary server spam
        for i in range(len(image_counts)):
            if image_counts[i] == "error":
                self.unique_id_list[i] = None
        return image_counts
