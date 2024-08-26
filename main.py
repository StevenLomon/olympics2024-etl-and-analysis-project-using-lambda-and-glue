import boto3

# Create an S3 object for programmatic access to our S3 buckets
s3 = boto3.client('s3')
bucket_naeme = "olympics2024-terraform-bucket-steven"