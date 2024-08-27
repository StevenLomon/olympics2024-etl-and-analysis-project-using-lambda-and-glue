import os
import json
import requests
import boto3
from datetime import datetime

def lambda_handler(event, context):
    # Get API key
    api_key = os.environ['API-KEY']
    
    # Define the S3 bucket and object key (filename)
    s3_bucket = "olympics2024-bucket-raw"
    s3_key = f'olympics_data_{datetime.now().strftime("%Y%m%d%H%M%S")}.json'
    
    # Set up API strings
    api_url = "https://olympic-sports-api.p.rapidapi.com/athletes"
    querystring = {"year":"2024","page":"1"}
    headers = {
    	"x-rapidapi-key": api_key,
    	"x-rapidapi-host": "olympic-sports-api.p.rapidapi.com"
    }
    
    # Get the API data
    response = requests.get(api_url, headers=headers, params=querystring)
    data = response.json()
    
    # Upload data to S3
    s3 = boto3.client('s3')
    s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=json.dumps(data))
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Data successfully uploaded to {s3_bucket}/{s3_key}')
    }
