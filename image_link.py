from datetime import timedelta, date
import aiohttp
import asyncio

# Don't overwhelm the slow server
REQUEST_LIMIT = 25
EXPIRY_DATE = (date.today() + timedelta(days=90)).strftime("%m/%d/%Y")

async def _make_image_link(session, unique_id) -> str:
    params = {"url": "https://upload.wikimedia.org/wikipedia/commons/c/ca/1x1.png",
              "type": "json",
              "private": "1",
              "expire": EXPIRY_DATE,
              # Ensures the input is a string, as there is no type checking for unique_id
              "custom": str(unique_id)}

    async with session.get("https://ulvis.net/API/write/get", params=params) as redirect:
        if not redirect.ok:
            print("Ulvis server is down... Returning default link with no view stats.")
            return params["url"]

        parsed_redirect = await redirect.json()

        if "data" not in parsed_redirect or "url" not in parsed_redirect["data"]:
            print(f"Error making image link for {unique_id}:", end=" ")
            # Check if error message can be found
            if "data" in parsed_redirect and "status" in parsed_redirect["data"]:
                print(f"{parsed_redirect['data']['status']}.", end=" ")

            print("Returning default link with no view stats.")
            return params["url"]

        return parsed_redirect["data"]["url"]


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


class Image_Count_Manager:
    def __init__(self):
        self.unique_id_list = []
        self.session = None
        # Manually manage an event loop for this instance, to allow session (aiohttp.ClientSession)
        # to be persistent across each call of get_image_counts().
        self.event_loop = asyncio.new_event_loop()
        self.event_loop.run_until_complete(self._create_session())

    def __del__(self):
        self.session.connector.close()
        self.session.detach()
        self.event_loop.close()

    async def _create_session(self):
        conn = aiohttp.TCPConnector(limit=REQUEST_LIMIT)
        self.session = aiohttp.ClientSession(connector = conn)

    def update_unique_id_list(self, unique_id_list):
        self.unique_id_list = unique_id_list

    async def _get_image_count(self, unique_id) -> int:
        params = {"type": "json",
                # Ensures the input is a string, as there is no type checking for unique_id
                "id": str(unique_id)}

        async with self.session.get("https://ulvis.net/API/read/get", params=params) as redirect:
            if not redirect.ok:
                print("Ulvis server is down... Returning counter stat as empty.")
                return ""

            parsed_redirect = await redirect.json()

            if "data" not in parsed_redirect or "hits" not in parsed_redirect["data"]:
                print(f"Error getting image count for {unique_id}:", end=" ")
                # Check if error message can be found
                if "error" in parsed_redirect and "msg" in parsed_redirect["error"]:
                    print(f"{parsed_redirect['error']['msg']}.", end=" ")

                print("Returning counter stat as empty.")
                return ""

            return parsed_redirect["data"]["hits"]

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
        return self.event_loop.run_until_complete(self._get_image_counts())
