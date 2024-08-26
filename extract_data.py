import requests
from dotenv import dotenv_values
import boto3
from botocore.exceptions import NoCredentialsError

# Load environment variables
config = dotenv_values(".env")
RAPIDAPI_KEY = config['RAPIDAPI-KEY']

# Initialize the S3 client
s3 = boto3.client('s3')

# Set the directory and S3 bucket name
local_directory = 'data'
bucket_name = "olympics2024-bucket-raw"

# Set up API strings
url = "https://olympic-sports-api.p.rapidapi.com/athletes"
querystring = {"year":"2024","page":"1"}
headers = {
	"x-rapidapi-key": RAPIDAPI_KEY,
	"x-rapidapi-host": "olympic-sports-api.p.rapidapi.com"
}

# # Get the API data
# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())