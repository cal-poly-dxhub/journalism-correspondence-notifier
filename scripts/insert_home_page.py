import boto3
import yaml

config = yaml.safe_load(open("../config.yaml"))


def create_home_page():
    """Creates index.html in s3 bucket and subsitutes email collection endpoint."""
    # S3 bucket name
    bucket_name = config["assets_bucket_name"]

    try:
        # Create S3 client
        s3_client = boto3.client("s3")

        email_endpoint = config["email_api_endpoint"]
        homepage_url = config["homepage_url"]
        with open("index_template.html", "r") as file:
            content = file.read()
            modified_content = content.replace(
                "https://your-unique-api-endpoint.com/prod/", email_endpoint
            ).replace("https://your-unique-homepage-url/", homepage_url)

        with open("index.html", "w") as file:
            file.write(modified_content)

        # Upload file
        s3_client.upload_file(
            "index.html",
            bucket_name,
            "index.html",
            ExtraArgs={"ContentType": "text/html"},
        )
        print(f"Successfully uploaded index.html to s3://{bucket_name}/")
        return True

    except Exception as e:
        print(f"Error uploading file to S3: {str(e)}")
        return False


if __name__ == "__main__":
    create_home_page()
