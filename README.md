# Journalism Notifier

A collaborative project between the DxHub and Cal Poly Journalism Department that monitors city council agendas and generates automated reports based on public correspondence.

## Table of Contents
- [Collaboration](#collaboration)
- [Disclaimers](#disclaimers)
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
- [Configuration](#configuration)
- [Testing](#troubleshooting)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

# Collaboration
Thanks for your interest in our solution.  Having specific examples of replication and cloning allows us to continue to grow and scale our work. If you clone or download this repository, kindly shoot us a quick email to let us know you are interested in this work!

[wwps-cic@amazon.com] 

# Disclaimers

**Customers are responsible for making their own independent assessment of the information in this document.**

**This document:**

(a) is for informational purposes only, 

(b) represents current AWS product offerings and practices, which are subject to change without notice, and 

(c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers. 

(d) is not to be considered a recommendation or viewpoint of AWS

**Additionally, all prototype code and associated assets should be considered:**

(a) as-is and without warranties

(b) not suitable for production environments

(d) to include shortcuts in order to support rapid prototyping such as, but not limitted to, relaxed authentication and authorization and a lack of strict adherence to security best practices

**All work produced is open source. More information can be found in the GitHub repo.**

## Author
- Nick Riley - njriley@calpoly.edu

## Overview
This system automatically scrapes city council agendas from LazerFische and analyzes public correspondence. When correspondence for an agenda item exceeds a set threshold, it generates comprehensive reports on a dashboard with detailed analytics and summaries.

## Features
- **Correspondence Analysis**
  - Support vs Opposition tracking
  - Sentiment analysis for each correspondence
  - Polarity measurements
  - Frequently used words analysis
  
- **Automated Reporting**
  - Item summaries
  - Overall sentiment analysis
  - Direct links to:
    - Agenda
    - Specific items
    - Related correspondence
  - Summary statistics

- **Automated Monitoring**
  - Hourly checks for new issues
  - Email notifications for popular new issues
  - Web page generation for items above threshold

## Prerequisites
- AWS Account and CLI
- Python 3.x
- Docker
- Git
- LazerFische credentials

## Deployment Steps

1. **Configure AWS Credentials**
```bash
aws configure
```

2. **Clone Repository**
```bash
git clone https://github.com/cal-poly-dxhub/journalism-correspondence-notifier
```

3. **Rename example config file**
```bash
mv example_config.yaml config.yaml
```

4. **Configure Settings**

Update the following values in `config.yaml`:

### Required Settings
```yaml
# Authentication
email_collection_password: <your-subscribe-button-password>    # Password for subscription system
sender_email: <your-ses-verified-email>              # Requires AWS SES setup

# LazerFische Credentials
lazerfische_username: <your-lazerfische-username>
lazerfische_password: <your-lazerfische-password>
lazerfische_token: <your-lazerfische-token>
```

See [AWS SES Email Setup Guide](https://docs.aws.amazon.com/ses/latest/dg/setting-up.html) for configuring your email.

### Optional: Custom Domain Setup
```yaml
homepage_url: <your-website-url>      # Optional - for custom domain only
```

**IMPORTANT**: If using a custom domain:
- Set `homepage_url` in `config.yaml` BEFORE running `cdk deploy`
- Follow the [AWS guide for custom domain setup](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-register.html)
- If using default S3 bucket URL, leave `homepage_url` unchanged


5. **Set Up Python Environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

6. **Deploy Infrastructure**


```bash
cd cdk
cdk synth
cdk deploy
```


**From CloudFormation outputs** Update `config.yaml`:
- `email_api_endpoint`: EmailCollectorApiEndpoint from CDK output
- `assets_bucket_name`: WebAssetsBucketName from CDK output
- `homepage_url`: WebsiteURL from CDK output (or use your own custom URL for the bucket see [AWS guide for setting up domain with Route53 and S3](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/getting-started-s3.html))


7. **Initialize Homepage**
```bash
python3 insert_home_page.py
```

8. **Subscribe to Notifications**
Open index.html and subscribe using your email address

**Note**: This system runs automatically every hour to check for new issues and generates web pages for items meeting the correspondence threshold criteria.

## Testing
To immediately test if the system is working:
1. Change the START_DATE environment variable to a date before the agenda dates you want to process.
2. Example: Set START_DATE to 05-01-2025 to create issues for all dates from then until present.


## Troubleshooting
- Verify AWS credentials and permissions
- Check LazerFische authentication
- Confirm Lambda execution role permissions
- Verify email subscription status

## Support
For assistance, contact:
- Darren Kraker, Sr Solutions Architect - dkraker@amazon.com
- Nick Riley, Jr Software Development Engineer - njriley@calpoly.edu
