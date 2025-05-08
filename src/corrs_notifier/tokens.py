import requests
import os

url = "https://opengov.slocity.org/LFRepositoryAPI/v1/Repositories/CityClerk/Token"


def get_access_token():
    bearer = f"Bearer {os.getenv('API_TOKEN')}"
    headers = {
        "accept": "application/json",
        "Authorization": bearer,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "password",
        "username": os.getenv("LAZERFISCHE_USERNAME"),
        "password": os.getenv("LAZERFISCHE_PASSWORD"),
    }

    response = requests.post(url, headers=headers, data=data)

    response_json = response.json()

    token = list(response_json.values())[1]

    if response.status_code == 200:
        return token
    else:
        print(response.status_code, "Request Failed")
