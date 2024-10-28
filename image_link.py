from datetime import timedelta, date
import aiohttp
import asyncio

# Don't overwhelm the slow server
REQUEST_LIMIT = 25
EXPIRY_DATE = (date.today() + timedelta(days=90)).strftime("%m/%d/%Y")

async def _make_image_link(session, unique_id) -> str:
    params = {"url": "https://github.com/Chandan8186/cs3103-grp-30/releases/download/1x1-transparent-image/1x1.png",
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


async def _get_image_count(session, unique_id) -> int:
    params = {"type": "json",
              # Ensures the input is a string, as there is no type checking for unique_id
              "id": str(unique_id)}

<<<<<<< Updated upstream
    async with session.get("https://ulvis.net/API/read/get", params=params) as redirect:
        if not redirect.ok:
            print("Ulvis server is down... Returning counter stat as 0.")
            return 0
=======
    def __del__(self):
        self.session.detach()
        self.event_loop.close()
>>>>>>> Stashed changes

        parsed_redirect = await redirect.json()

        if "data" not in parsed_redirect or "hits" not in parsed_redirect["data"]:
            print(f"Error getting image count for {unique_id}:", end=" ")
            # Check if error message can be found
            if "error" in parsed_redirect and "msg" in parsed_redirect["error"]:
                print(f"{parsed_redirect['error']['msg']}.", end=" ")

            print("Returning counter stat as 0.")
            return 0

        return int(parsed_redirect["data"]["hits"])


"""
Asynchronously gets image download count for each unique id.
Usage: asyncio.run(get_image_counts(unique_id_list))

Parameters:
unique_id_list (list[str]): List of unique ids.

Returns:
list[int]: List of image download counts.
"""
async def get_image_counts(unique_id_list) -> list[int]:
    conn = aiohttp.TCPConnector(limit=REQUEST_LIMIT)
    async with aiohttp.ClientSession(connector = conn) as session:
        coroutines = [_get_image_count(session, unique_id) for unique_id in unique_id_list]
        return await asyncio.gather(*coroutines)
