import boto3
import os
import yaml

config = yaml.safe_load(open("../config.yaml"))


def upload_to_s3():
    # S3 bucket name
    bucket_name = config["assets_bucket_name"]

    # Check if file exists
    if not os.path.exists("index.html"):
        print("Error: index.html not found in current directory")
        return False

    try:
        # Create S3 client
        s3_client = boto3.client("s3")

        # Upload file
        s3_client.upload_file("index.html", bucket_name, "index.html")
        print(f"Successfully uploaded index.html to s3://{bucket_name}/")
        return True

    except Exception as e:
        print(f"Error uploading file to S3: {str(e)}")
        return False


if __name__ == "__main__":
    upload_to_s3()
