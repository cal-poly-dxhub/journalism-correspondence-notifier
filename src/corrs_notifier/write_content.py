from aws_utils import upload_file_to_s3, get_html_content_from_s3
import os


def add_article_item(html_content, title, issue_id="#"):
    link = f"https://{os.getenv('ASSETS_BUCKET_NAME')}.s3.amazonaws.com/{issue_id}.html"
    # Define the new article item as a string
    new_article_item = f'''
            <div class="article-item">
                <span class="article-title">{title}</span>
                <a href="{link}" class="link-button">View</a>
            </div>
    '''

    # Check if the article item already exists
    if new_article_item in html_content:
        return html_content  # Return the original content if there's a duplicate

    # Locate the opening tag of the article list div
    start_index = html_content.find('<div class="article-list">')

    if start_index == -1:
        raise ValueError("The article list div was not found in the HTML content.")

    # Insert the new article item immediately after the opening tag
    updated_html = (
        html_content[: start_index + len('<div class="article-list">')]
        + new_article_item
        + html_content[start_index + len('<div class="article-list">') :]
    )

    print(f"Updated list of items with {title}")

    return updated_html


def write_issue_webpage(html_content, issue_id):
    html_content_bytes = html_content.encode("utf-8")

    temp_file_path = f"/tmp/{issue_id}.html"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(html_content_bytes)

    upload_file_to_s3(
        file_name=temp_file_path,
        bucket=os.getenv("ASSETS_BUCKET_NAME"),
        object_name=f"{issue_id}.html",
    )

    print(f"Successfully added new summary page for {issue_id}")

    os.remove(temp_file_path)


def write_new_homepage(agenda_name, agenda_item, issue_id):
    html_content = get_html_content_from_s3(
        os.getenv("ASSETS_BUCKET_NAME"), "index.html"
    )

    new_home_page = add_article_item(
        html_content, f"Correspondence Report - {agenda_name} - {agenda_item}", issue_id
    )

    html_content_bytes = new_home_page.encode("utf-8")
    temp_file_path = f"/tmp/index.html"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(html_content_bytes)

    upload_file_to_s3(
        file_name=temp_file_path,
        bucket=os.getenv("ASSETS_BUCKET_NAME"),
        object_name=f"index.html",
    )
    print("Successfully updated home page")
    os.remove(temp_file_path)
