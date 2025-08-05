from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    BundlingOptions,
    Duration,
    RemovalPolicy,
    aws_apigateway as apigw,
    CfnOutput,
)
from constructs import Construct
import yaml
from datetime import datetime

config = yaml.safe_load(open("../config.yaml", "r"))


class CorrespondenceNotifierStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for web assets
        web_assets_bucket = s3.Bucket(
            self,
            "calpoly-journalism-notifier-dashboard",
            removal_policy=RemovalPolicy.DESTROY,
            # Enable static website hosting
            website_index_document="index.html",
            # Allow public access
            public_read_access=True,
            # Configure public access blocking settings
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
        )

        # Add the specified bucket policy
        web_assets_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="PublicReadGetObject",
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()],
                actions=["s3:GetObject"],
                resources=[web_assets_bucket.arn_for_objects("*")],
            )
        )

        # Output the website URL
        CfnOutput(
            self,
            "WebsiteURL",
            value=web_assets_bucket.bucket_website_url,
            description="URL for the S3 bucket website",
        )

        # Create DynamoDB tables
        processed_dates_table = dynamodb.Table(
            self,
            "processed-agendas-table",
            partition_key=dynamodb.Attribute(
                name="date", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            table_class=dynamodb.TableClass.STANDARD,
        )

        email_subscribers_table = dynamodb.Table(
            self,
            "email-subscribers-table",
            partition_key=dynamodb.Attribute(
                name="email", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        email_collector_lambda = _lambda.Function(
            self,
            "email-collector-function",
            code=_lambda.Code.from_asset(
                "../src/email_collector",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_13.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip3.13 install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            environment={
                "EMAIL_SUBSCRIBERS_TABLE": email_subscribers_table.table_name,
                "EMAIL_PASSWORD": config["email_collection_password"],
                "START_DATE": datetime.now().strftime("%m-%d-%Y"),
            },
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="collect_email.lambda_handler",
            memory_size=128,
            timeout=Duration.minutes(1),
        )

        # Add permissions to call SES from Email Collector
        email_collector_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ses:VerifyEmailIdentity",
                    "ses:ListVerifiedEmailAddresses",
                    "ses:GetIdentityVerificationAttributes",
                ],
                resources=["*"],
            )
        )

        email_subscribers_table.grant_read_write_data(email_collector_lambda)

        # Create api to hit with emails
        api = apigw.RestApi(
            self,
            "EmailCollectorApi",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
            ),
            deploy_options=apigw.StageOptions(
                throttling_burst_limit=20,  # maximum number of concurrent requests
                throttling_rate_limit=10,  # requests per second
            ),
        )

        # Create the /collectJournalismEmail resource
        collect_email_resource = api.root.add_resource("collectJournalismEmail")

        # Add POST method to the resource
        collect_email_resource.add_method(
            "POST",
            apigw.LambdaIntegration(
                email_collector_lambda,
                proxy=True,
            ),
            authorization_type=apigw.AuthorizationType.NONE,
        )

        # If no custom url exists in config, simply use bucket url
        homepage_url = config.get("homepage_url")
        if not homepage_url or homepage_url == "<your-website-url>":
            homepage_url = web_assets_bucket.bucket_website_url

        scheduled_lambda = _lambda.Function(
            self,
            "scheduled-notifier-function",
            code=_lambda.Code.from_asset(
                "../src/corrs_notifier",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_13.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip3.13 install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            environment={
                "PROCESSED_DATES_TABLE": processed_dates_table.table_name,
                "EMAIL_SUBSCRIBERS_TABLE": email_subscribers_table.table_name,
                "ASSETS_BUCKET_NAME": web_assets_bucket.bucket_name,
                "START_DATE": datetime.now().strftime("%m-%d-%Y"),
                "SENDER_EMAIL": config["sender_email"],
                "CORRS_FOLDER_ID": str(config["correspondence_folder_id"]),
                "CORRS_THRESHOLD": str(config["correspondence_threshold"]),
                "DATE_INDEX": str(config["date_index"]),
                "SHORTCUT_ENTRY_INDEX": str(config["shortcut_entry_index"]),
                "SUMMARIZE_PROMPT": config["item_summarization_prompt"],
                "MODEL_ID": config["model_id"],
                "CITIZEN_SENTIMENT_PROMPT": config["citizen_sentiment_prompt"],
                "OVERALL_SENTIMENT_PROMPT": config["overall_sentiment_prompt"],
                "REPO_NAME": config["repo_name"],
                "CITIZEN_NAME_INDEX": str(config["citizen_name_index"]),
                "LAZERFISCHE_USERNAME": config["lazerfische_username"],
                "LAZERFISCHE_PASSWORD": config["lazerfische_password"],
                "LAZERFISCHE_TOKEN": config["lazerfische_token"],
                "EMAIL_ENDPOINT": config["email_api_endpoint"],
                "HOMEPAGE_URL": homepage_url,
                "MAX_SUMMARIZATION_TOKEN": config[
                    "correspondence_summarization_token_threshold"
                ],
            },
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="app.lambda_handler",
            memory_size=1024,
            timeout=Duration.minutes(15),
        )

        scheduled_lambda.add_to_role_policy(
            iam.PolicyStatement(actions=["bedrock:*"], resources=["*"])
        )

        # Grant permissions
        web_assets_bucket.grant_read_write(scheduled_lambda)
        processed_dates_table.grant_read_write_data(scheduled_lambda)
        email_subscribers_table.grant_read_data(scheduled_lambda)

        # Add permissions to call SES from Scheduled Notifier
        scheduled_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ses:VerifyEmailIdentity",
                    "ses:ListVerifiedEmailAddresses",
                    "ses:GetIdentityVerificationAttributes",
                    "ses:SendEmail",
                ],
                resources=["*"],
            )
        )

        # Create CloudWatch Event rule to trigger lambda hourly
        rule = events.Rule(
            self, "HourlyScheduleRule", schedule=events.Schedule.rate(Duration.hours(1))
        )

        rule.add_target(targets.LambdaFunction(scheduled_lambda))

        # Output bucket name
        CfnOutput(
            self,
            "WebAssetsBucketName",
            value=web_assets_bucket.bucket_name,
            description="Name of the S3 bucket for web assets",
        )
