import json
import requests
from tokens import get_access_token
import os
from collections import Counter


def get_page_count(doc_id):
    url = f"https://opengov.slocity.org/LFRepositoryAPI/v1/Repositories/CityClerk/Entries/{doc_id}"
    params = {"$select": "pageCount"}
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + get_access_token(),
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("pageCount")
    else:
        print("Page request failed", response.status_code)
        return None


def get_text_of_page(doc_id, page_num):
    url = "https://opengov.slocity.org/WebLink/DocumentService.aspx/GetTextHtmlForPage"
    headers = {"Content-Type": "application/json"}

    data = {"documentId": doc_id, "pageNum": page_num, "repoName": "CityClerk"}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        return response_json["data"]["text"]
    except Exception as e:
        print(f"Request Failed for page {page_num}: {str(e)}")
        return ""


def get_document_text(document_id):
    # Get the number of pages in the document
    page_count = get_page_count(document_id)
    if page_count is None:
        return ""

    # Retrieve the text for each page and combine it
    full_text = []
    for page_num in range(1, min(3, page_count + 1)):
        full_text.append(get_text_of_page(document_id, page_num))

    # Combine the text from all pages into a single string
    combined_text = "".join(full_text)

    return combined_text


def get_folder_listing(folder_id, start=0, end=40):
    """Calls lazerfische folder_listing API with end - start results."""
    url = "https://opengov.slocity.org/WebLink/FolderListingService.aspx/GetFolderListing2"
    body = {
        "repoName": os.getenv("REPO_NAME"),
        "folderId": int(folder_id),
        "getNewListing": "true",
        "start": start,
        "end": end,
        "sortColumn": "",
        "sortAscending": "true",
    }
    response = requests.post(url, json=body)
    if response.status_code == 200:
        return response.json().get("data", {}).get("results", [])
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return []


def get_agenda_correspondence_years(folder_listing):
    """Returns a list of (year, entryId) for years with associated correspondence."""
    dates = {
        result["name"]: result["entryId"]
        for result in folder_listing
        if result is not None
    }

    return dates


def get_valid_correspondences(correspondence_shortcut_id):
    raw_correspondences = get_folder_listing(correspondence_shortcut_id)
    cleaned_correspondence_data = [
        c
        for c in (process_correspondence(c) for c in raw_correspondences if c)
        if c[0] and c[0] != "Item Public"
    ]
    return cleaned_correspondence_data


def get_correspondence_counts(correspondences):
    """Returns a list of items and their count. Ex: Counter({'Item 7c': 11})"""
    return Counter(item for item, _, _ in correspondences)


def get_agendas_by_year(meeting_entry_id):
    entries = get_folder_listing(meeting_entry_id)
    return [entry for entry in entries if entry is not None]


def process_correspondence(correspondence):
    if correspondence and "Staff" not in correspondence.get("name", ""):
        try:
            words = correspondence.get("name", "").split()
            item_text = f"{words[1]} {words[2].replace(',', '')}"
            return (
                item_text,
                correspondence.get("entryId"),
                words[int(os.getenv("CITIZEN_NAME_INDEX"))],
            )
        except:
            return None, None, None
    return None, None, None


def get_parent_folder(folder_id):
    url = "https://opengov.slocity.org/WebLink/FolderListingService.aspx/GetBreadCrumbs"
    body = {"vdirName": "WebLink", "repoName": "CityClerk", "folderId": folder_id}

    response = requests.post(url, json=body)
    if response.status_code == 200:
        content_str = response.content.decode("utf-8")

        json_content = json.loads(content_str)

        return json_content.get("data", {})[-2].get("id")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return []


def get_doc_url_from_id(entry_id):
    return f"https://opengov.slocity.org/WebLink/DocView.aspx?id={entry_id}&dbid=0&repo=CityClerk"


def get_folder_url_from_id(entry_id):
    return f"https://opengov.slocity.org/WebLink/browse.aspx?id={entry_id}&dbid=0&repo=CityClerk"
