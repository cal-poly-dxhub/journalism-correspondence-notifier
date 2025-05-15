import boto3
from botocore.exceptions import NoCredentialsError, ClientError, PartialCredentialsError
from botocore.config import Config
import json
import os


def send_email(sender, recipients, subject, body_text="Default Text", body_html=None):
    if not recipients:
        print("No verified recipients in email list.")
        return

    # Create a new SES client
    ses_client = boto3.client("ses")

    # The email body for recipients with non-HTML email clients.
    body = {
        "Text": {
            "Charset": "UTF-8",
            "Data": body_text,
        },
    }

    # If HTML content is provided, add it to the email body
    if body_html:
        body["Html"] = {
            "Charset": "UTF-8",
            "Data": body_html,
        }

    try:
        # Send the email
        response = ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": recipients},
            Message={
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": subject,
                },
                "Body": body,
            },
        )
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("Error: AWS credentials not found or incomplete.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

    return response


def invoke_llm(user_input, system="", max_tokens=1000):
    max_input_tokens = int(os.getenv("MAX_SUMMARIZATION_TOKEN"))
    if len(user_input) > max_input_tokens:
        user_input = user_input[0:max_input_tokens]

    bedrock_config = Config(
        retries={
            "max_attempts": 10,  # Increase the number of retries
            "mode": "standard",  # You can also use 'adaptive' for adaptive retry behavior
        }
    )

    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime", config=bedrock_config
    )
    model_id = os.getenv("MODEL_ID")
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user_input}],
        }
    )
    try:
        response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
        return json.loads(response.get("body").read())["content"][0]["text"]
    except Exception as err:
        print(f"An error occurred: {str(err)}")
        return None


def get_verified_emails():
    ses_client = boto3.client("ses")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.getenv("EMAIL_SUBSCRIBERS_TABLE"))

    # Scan the DynamoDB table to get all emails
    response = table.scan()
    emails = [item["email"] for item in response.get("Items", [])]

    verified_emails = []

    # Check the verification status of each email using SES
    for email in emails:
        ses_response = ses_client.get_identity_verification_attributes(
            Identities=[email]
        )
        verification_status = (
            ses_response["VerificationAttributes"]
            .get(email, {})
            .get("VerificationStatus", "")
        )
        if verification_status == "Success":
            verified_emails.append(email)

    return verified_emails


def get_html_content_from_s3(bucket, file_name):
    s3 = boto3.client("s3")

    # Read the index.html file from S3
    response = s3.get_object(Bucket=bucket, Key=file_name)
    html_content = response["Body"].read().decode("utf-8")

    return html_content


def upload_file_to_s3(file_name, bucket, object_name=None):
    """
    Uploads a file to an S3 bucket. If the file already exists, it will be overwritten.

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified, file_name is used
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Create an S3 client
    s3_client = boto3.client("s3")

    try:
        # Upload the file
        s3_client.upload_file(
            file_name, bucket, object_name, ExtraArgs={"ContentType": "text/html"}
        )
        print(f"File {file_name} uploaded to {bucket}/{object_name}")
        return True
    except FileNotFoundError:
        print(f"The file {file_name} was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except ClientError as e:
        print(f"Error occurred: {e}")
        return False
