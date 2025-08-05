import json
from datetime import datetime
import re
from lazerfiche_utils import (
    get_folder_listing,
    get_agenda_correspondence_years,
    get_agendas_by_year,
    get_valid_correspondences,
    get_correspondence_counts,
    get_folder_url_from_id,
    get_parent_folder,
    get_document_text,
    get_doc_url_from_id,
)
from aws_utils import (
    invoke_llm,
    get_verified_emails,
    send_email,
)
from table_utils import date_item_exists, add_date_item
from write_content import write_new_homepage, write_issue_webpage
from corrs_analysis import get_issue_summary_and_polarity, generate_word_cloud
import os


def generate_report(
    agenda_name,
    agenda_item,
    correspondence_data,
    item_title,
    item_summary,
    item_url,
    agenda_url,
):
    analysis = get_issue_summary_and_polarity(correspondence_data, agenda_item)

    word_cloud_html = generate_word_cloud(analysis)

    with open("issue_template.txt", "r", encoding="utf-8") as file:
        html_template = file.read()

    # Replace placeholders in the HTML
    html_content = html_template.format(
        agenda_name=agenda_name,
        agenda_item=agenda_item,
        individual_summaries=analysis["individual_summaries"],
        positive_count=analysis["support_count"],
        neutral_count=analysis["neutral_count"],
        negative_count=analysis["against_count"],
        correspondence_summary=analysis["overall_summary"],
        word_cloud_html=word_cloud_html,
        item_title=item_title,
        item_summary=item_summary,
        agenda_url=agenda_url,
        item_url=item_url,
        homepage_url=os.getenv("HOMEPAGE_URL"),
    )

    issue_id = agenda_name.lower() + "-" + agenda_item.lower()

    write_issue_webpage(html_content, issue_id)

    with open("email_template.txt", "r", encoding="utf-8") as file:
        html_template = file.read()

    html_content = html_template.format(
        agenda_name=agenda_name,
        agenda_item=agenda_item,
        issue_id=issue_id,
        positive_count=analysis["support_count"],
        neutral_count=analysis["neutral_count"],
        negative_count=analysis["against_count"],
        correspondence_summary=analysis["overall_summary"],
        agenda_url=agenda_url,
        item_url=item_url,
        homepage_url=os.getenv("HOMEPAGE_URL").rstrip("/"),
    )

    email_list = get_verified_emails()

    send_email(
        sender=os.getenv("SENDER_EMAIL"),
        recipients=email_list,
        subject="Citizen Correspondence Alert",
        body_html=html_content,
    )

    print(f"Successfully sent email to {email_list}")

    write_new_homepage(agenda_name, agenda_item, issue_id)


def find_item_doc_id(entries, item_pattern):
    """Iterate through files and match to item regex. Returns entryId and the Title."""
    # Create a regex pattern based on the provided item pattern
    pattern = re.compile(rf"^{item_pattern}\b\.\s*(.*)")

    for entry in entries:
        if entry and "name" in entry:
            name = entry["name"]
            # Check if the name matches the provided item pattern
            match = pattern.match(name)
            if match:
                # Extract the rest of the string after the item pattern
                rest_of_title = match.group(1).strip()
                return entry["entryId"], rest_of_title

    return None, None


def lambda_handler(event, context):
    print("Scheduled task triggered")

    current_year = str(datetime.now().year)
    new_issues = []

    year_listing = get_folder_listing(int(os.getenv("CORRS_FOLDER_ID")))

    years = get_agenda_correspondence_years(year_listing)
    start_date_str = os.getenv("START_DATE")
    start_date = datetime.strptime(start_date_str, "%m-%d-%Y")

    # If there exists any correspondence in Lazerfische for the current year
    if current_year in years:
        agendas = get_agendas_by_year(years[current_year])
    else:
        return {
            "statusCode": 200,
            "body": json.dumps(f"No correspondence found for year {current_year}"),
        }

    # Iterate through agendas
    for agenda in agendas:
        agenda_date = agenda.get("name").split()[int(os.getenv("DATE_INDEX"))]
        date_object = datetime.strptime(agenda_date, "%m-%d-%Y")
        # If agenda is in the past (before deployment) do not process
        if date_object < start_date:
            continue

        correspondence_shortcut_id = agenda.get("data")[
            int(os.getenv("SHORTCUT_ENTRY_INDEX"))
        ]

        correspondence_data = get_valid_correspondences(correspondence_shortcut_id)
        item_counts = get_correspondence_counts(correspondence_data)

        # Iterate through items in an agenda
        for agenda_item, count in item_counts.items():
            # If agenda item that has more than threshold write ins
            if count >= int(os.getenv("CORRS_THRESHOLD")) and not date_item_exists(
                agenda_date, agenda_item
            ):
                # Get urls for folders and item
                parent_id = get_parent_folder(correspondence_shortcut_id)
                parent_url = get_folder_url_from_id(parent_id)
                agenda_entries = get_folder_listing(parent_id)
                item_id, item_title = find_item_doc_id(agenda_entries, agenda_item)
                item_text = get_document_text(item_id)
                item_url = get_doc_url_from_id(item_id)

                # Ensure item has text before processing (some files are audio)
                if item_text:
                    item_summary = invoke_llm(item_text, os.getenv("SUMMARIZE_PROMPT"))

                    print(f"New report found: {agenda_date} Agenda {agenda_item}")
                    add_date_item(agenda_date, agenda_item)

                    generate_report(
                        agenda_date,
                        agenda_item,
                        correspondence_data,
                        item_title,
                        item_summary,
                        item_url,
                        parent_url,
                    )

                    print(f"History updated with {agenda_date} Agenda {agenda_item}")
                    new_issues.append(f"{agenda_date} Agenda {agenda_item} added")
                else:
                    print(f"Item text not found for {agenda_item}")

    if new_issues:
        formatted_issues = " ".join(new_issues)
        return {
            "statusCode": 200,
            "body": json.dumps(
                f"Task completed successfully: Added {formatted_issues}"
            ),
        }
    else:
        return {
            "statusCode": 200,
            "body": json.dumps("Task completed successfully: No new issues"),
        }
