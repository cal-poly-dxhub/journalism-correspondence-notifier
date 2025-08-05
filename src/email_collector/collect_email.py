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
        return {
            "statusCode": 401,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Requested-With",
                "Access-Control-Allow-Credentials": "true",
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {
                    "message": "Incorrect Password",
                    "success": True,
                }
            ),
        }

    if not email_address:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Requested-With",
                "Access-Control-Allow-Credentials": "true",
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {
                    "message": "Email address is required",
                    "success": True,
                }
            ),
        }

    insert_email(email_address)

    ses_client = boto3.client("ses")

    ses_client.verify_email_identity(EmailAddress=email_address)

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json",
        },
        "body": json.dumps(
            {
                "message": f"Email {email_address} uploaded to database successfully",
                "success": True,
            }
        ),
    }
