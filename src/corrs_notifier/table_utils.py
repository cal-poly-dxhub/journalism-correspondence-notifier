import boto3
from botocore.exceptions import ClientError
import os

# Initialize a DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.getenv("PROCESSED_DATES_TABLE"))


def add_date_item(date, item):
    """
    Add a date and item to the table. If the date exists, it adds the item to the existing set.
    If the date doesn't exist, it creates a new entry with the item.

    :param date: String in format 'MM-DD-YYYY'
    :param item: String representing the item (e.g., 'Item 7a')
    """
    try:
        response = table.update_item(
            Key={"date": date},
            UpdateExpression="ADD agenda_items :i",  # Changed from Items to agenda_items
            ExpressionAttributeValues={":i": set([item])},
            ReturnValues="UPDATED_NEW",
        )
        print(f"Successfully added {item} to {date}")
        return True
    except ClientError as e:
        print(f"Error adding item: {e.response['Error']['Message']}")
        return False


def date_item_exists(date, item):
    """
    Check if a specific date and item pair exists in the table.

    :param date: String in format 'MM-DD-YYYY'
    :param item: String representing the item (e.g., 'Item 7a')
    :return: Boolean indicating if the pair exists
    """
    try:
        response = table.get_item(Key={"date": date})

        if "Item" not in response:
            print(f"date {date} does not exist in the table.")
            return False

        if item in response["Item"]["agenda_items"]:
            return True
        else:
            print(f"{item} does not exist for date {date}")
            return False

    except ClientError as e:
        print(f"Error checking item: {e.response['Error']['Message']}")
        return False
