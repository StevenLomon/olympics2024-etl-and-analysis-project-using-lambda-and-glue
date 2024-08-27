import boto3

def lambda_handler(event, context):
    # Set up Glue object
    glue = boto3.client('glue')

    # Start the Glue ETL job
    response = glue.start_job_run(
        JobName='olympics-data-transformation',
    )

    return {
        'statusCode': 200,
        'body': f"Started Glue job with run ID: {response['JobRunId']}"
    }