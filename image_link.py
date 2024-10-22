import requests

def make_image_link(unique_id) -> str:
    params = {"url": "https://github.com/Chandan8186/cs3103-grp-30/releases/download/1x1-transparent-image/1x1.png",
              "type": "json",
              "private": "1",
              # Ensures the input is a string, as there is no type checking for unique_id
              "custom": str(unique_id)}

    redirect = requests.get("https://ulvis.net/API/write/get", params=params)

    if not redirect.ok:
        print("Ulvis server is down... Returning default link with no view stats.")
        return params["url"]

    parsed_redirect = redirect.json()

    if "data" not in parsed_redirect or "url" not in parsed_redirect["data"]:
        print(f"Error making image link for {unique_id}:", end=" ")
        # Check if error message can be found
        if "data" in parsed_redirect and "status" in parsed_redirect["data"]:
            print(f"{parsed_redirect['data']['status']}.", end=" ")

        print("Returning default link with no view stats.")
        return params["url"]

    return parsed_redirect["data"]["url"]

def get_image_count(unique_id) -> int:
    params = {"type": "json",
              # Ensures the input is a string, as there is no type checking for unique_id
              "id": str(unique_id)}

    redirect = requests.get("https://ulvis.net/API/read/get", params=params)

    if not redirect.ok:
        print("Ulvis server is down... Returning counter stat as 0.")
        return 0

    parsed_redirect = redirect.json()

    if "data" not in parsed_redirect or "hits" not in parsed_redirect["data"]:
        print(f"Error getting image count for {unique_id}:", end=" ")
        # Check if error message can be found
        if "error" in parsed_redirect and "msg" in parsed_redirect["error"]:
            print(f"{parsed_redirect['error']['msg']}.", end=" ")

        print("Returning counter stat as 0.")
        return 0

    return int(parsed_redirect["data"]["hits"])
