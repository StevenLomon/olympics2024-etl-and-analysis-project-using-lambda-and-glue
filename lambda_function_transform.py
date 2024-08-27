# import json
# import boto3
# import pandas as pd
# import awswrangler as wr

# def lambda_handler(event, context):
#     # Set up S3 client and declare raw and transformed data bucket name
#     s3 = boto3.client('s3')
#     s3_bucket_raw = "olympics2024-bucket-raw"
#     s3_bucket_transformed = "olympics2024-bucket-transformed"
    
#     # List all objects in the bucket
#     response = s3.list_objects_v2(Bucket=s3_bucket_raw)
    
#     # Extract the list of JSON files (objects) in the bucket using list comprehension and response.get()
#     json_files = [obj["Key"] for obj in response.get('Contents', []) if obj['Key'].endswith(".json")]
    
#     # Initialize an empty list to hold all JSON data
#     all_json_data = []
    
#     # Iterate over each JSON file in the bucket
#     for json_file in json_files:
#         # Get the object using the S3 client and key
#         obj = s3.get_object(Bucket=s3_bucket_raw, Key=json_file)
        
#         # Read the file content and load the JSON data
#         file_content = obj['Body'].read().decode('utf-8')
#         json_data = json.loads(file_content)
        
#         # Extract the 'athletes' data and append to the list
#         if 'athletes' in json_data:
#             all_json_data.extend(json_data['athletes'])
            
#     # Convert the list of athletes' data to a DataFrame
#     df = pd.json_normalize(all_json_data)
    
#     # Reorder columns to ensure the desired order
#     desired_columns = ['id', 'name', 'country', 'sport']
#     df = df[desired_columns]
    
#     # Save the DataFrame as Parquet using AWS DataWrangler to the transformed data S3 bucket
#     wr.s3.to_parquet(
#         df=df,
#         path=f"s3://{s3_bucket_transformed}/athletes_data/",
#         dataset=True,
#         partition_cols=['sport'] # We're partitioning in S3 by sport
#         )
    
#     return {
#         'statusCode': 200,
#         'body': 'Data successfully transformed and saved to S3 as Parquet.'
#     }

import json
import boto3
import awswrangler as wr

def lambda_handler(event, context):
    # Define S3 paths
    s3_path_raw_data = "s3://olympics2024-bucket-raw/"
    s3_path_transformed_data = "s3://olympics2024-bucket-transformed/athletes_data/"
    
    # Read JSON files directly from S3 directly using AWS Data Wrangler
    json_data = wr.s3.read_json(path=s3_path_raw_data)
    
    # Select only the 'athletes' field from the JSON
    athletes_data = json_data['athletes']
    
    # Write the selected data back to S3 in Parquet format
    wr.s3.to_parquet(
        df=athletes_data,
        path=s3_path_transformed_data,
        dataset=True,
        partition_cols=["sport"]
    )
    
    return {
        'statusCode': 200,
        'body': 'Data successfully transformed and saved to S3 as Parquet.'
    }

