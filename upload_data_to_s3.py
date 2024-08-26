import os
import boto3
from botocore.exceptions import NoCredentialsError

# Initialize the S3 client
s3 = boto3.client('s3')

# Set the directory and S3 bucket name
local_directory = 'data'
bucket_name = "olympics2024-terraform-bucket-steven"

# Loop through all files in the data directory. os.walk yields a 3-tuple; (dirpath, dirnames, filenames)
for root, dirs, files in os.walk(local_directory):
    for file in files:
        if file.endswith('.csv'):
            # Construct the full local file path
            local_file_path = os.path.join(root, file)

            # Construct the S3 object key (keeping the same directory structure). relpath returns a relative path
            s3_file_path = os.path.relpath(local_file_path, local_directory)

            try:
                # Upload to S3
                s3.upload_file(local_file_path, bucket_name, s3_file_path)
                print(f'Successfully uploaded {local_file_path} to s3://{bucket_name}/{s3_file_path}')
            except NoCredentialsError:
                print('Credentials not available')

