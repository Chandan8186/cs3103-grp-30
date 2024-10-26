import aiohttp
import asyncio

# Don't overwhelm the slow server
REQUEST_LIMIT = 25

async def make_image_link(session, unique_id) -> str:
    params = {"url": "https://github.com/Chandan8186/cs3103-grp-30/releases/download/1x1-transparent-image/1x1.png",
              "type": "json",
              "private": "1",
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

# Run using: asyncio.run(make_image_links(unique_id_list))
async def make_image_links(unique_id_list) -> list[str]:
    conn = aiohttp.TCPConnector(limit=REQUEST_LIMIT)
    async with aiohttp.ClientSession(connector = conn) as session:
        coroutines = [make_image_link(session, unique_id) for unique_id in unique_id_list]
        return await asyncio.gather(*coroutines)


async def get_image_count(session, unique_id) -> int:
    params = {"type": "json",
              # Ensures the input is a string, as there is no type checking for unique_id
              "id": str(unique_id)}

    async with session.get("https://ulvis.net/API/read/get", params=params) as redirect:
        if not redirect.ok:
            print("Ulvis server is down... Returning counter stat as 0.")
            return 0

        parsed_redirect = await redirect.json()

        if "data" not in parsed_redirect or "hits" not in parsed_redirect["data"]:
            print(f"Error getting image count for {unique_id}:", end=" ")
            # Check if error message can be found
            if "error" in parsed_redirect and "msg" in parsed_redirect["error"]:
                print(f"{parsed_redirect['error']['msg']}.", end=" ")

            print("Returning counter stat as 0.")
            return 0

        return int(parsed_redirect["data"]["hits"])

# Run using: asyncio.run(get_image_counts(unique_id_list))
async def get_image_counts(unique_id_list) -> list[int]:
    conn = aiohttp.TCPConnector(limit=REQUEST_LIMIT)
    async with aiohttp.ClientSession(connector = conn) as session:
        coroutines = [get_image_count(session, unique_id) for unique_id in unique_id_list]
        return await asyncio.gather(*coroutines)
