import json
import boto3
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.getenv("EMAIL_SUBSCRIBERS_TABLE"))
the_password = os.getenv("EMAIL_PASSWORD")


def insert_email(email):
    response = table.put_item(Item={"email": email})
    return response


def lambda_handler(event, context):
    body = json.loads(event.get("body"))
    email_address = body.get("email")
    entred_password = body.get("password")

    if entred_password != the_password:
        return {"statusCode": 401, "body": json.dumps("Incorrect Password")}

    if not email_address:
        return {"statusCode": 400, "body": json.dumps("Email address is required")}

    insert_email(email_address)

    ses_client = boto3.client("ses")

    response = ses_client.verify_email_identity(EmailAddress=email_address)

    return {
        "statusCode": 200,
        "body": json.dumps(f"Email {email_address} uploaded to database successfully"),
    }
