This is a Data Engineering project that models the Spotify API project mentioned in this video: https://www.youtube.com/watch?v=X8Fin2zMKK4 by Darshil Parmar: https://www.linkedin.com/in/darshil-parmar/
Instead of getting data from the Spotify API, I will be getting data from the Paris Olympics 2024 API: https://data.paris2024.org/api/explore/v2.1/console
The AWS Services that will be used are S3, AWS Glue (with AWS GlueCrawler), Amazon CloudWatch, AWS Lambda, DynamoDB and Amazon Athena. The AWS Data Wrangler library will be used over pandas for the data transformation since we're working with AWS services.
Terraform will be used to automate and manage the provisioning of AWS resources involved in the data pipeline.

To start the project, data from the API was asked for access by atuhorizing on the official website.   
While waiting for the request access, an IAM User was being set up that will be used during the project. This user will only have full access to all of the services that are used in the project and these services only as per the Principle of Least Privilege. The user will both have console access (with MFA) and programmatic access via the CLI and the user will also be disabled by the end of the project to minimuze security risks.  
(When applying policies, I stumbled upon the two types of CloudWatch for the first time: AWS CloudWatchEvidently and AWS CloudWatchRUM (Real User Monitoring). CloudWatchEvidently is moreso used for A/B testing and feature flag management and so for this project CloudWatchRUM will instead be used. This is also more in line with what I learned when studying for the Cloud Practitioner Exam haha)  
Since all of the services that will be used throughout the project are avaialble in the Stockholm (eu-north-1) region and it's the closest one location-wise, this is the one that will be used.  

I then created the provider.tf file. This is my first time working with Terraform so everything is new but exciting and I'm focusing on failing forward! The official Terraform documentation has a super handy button that says "Use this Provider" that allows us to quickly set up our provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs  
With our terraform version block and aws provider block with the region we want to use in provider.tf written, we can run terraform init in our terminal (with Terraform also installed which I did earlier following this: https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) to initalize our Terraform back-end. We are displayed with "Terraform has been successfully initialized!"  
Both the .terraform directory and the .terraform.lock.hcl file are both added to .gitignore since they're both automatically generated and managed by Terraform.  

main.tf and variables.tf were created to handle the provisioning of AWS resources. I starting by creating an S3 Bucket for the Data Lake.   
I'm also making sure to use the variable name in variables.tf rather than writing them in main.tf. Single source of truth.

I decided, since I am pressed for time for job interview deadlines, to finish this project without Terraform and "re-do" it with Terraform in retrospect

So next up is setting up boto3 and creating an S3 object  
Since I still didn't have access to the official API data, I downloaded some Olympics data from Kaggle. All of this data was store in a directory called 'data' in the main directory and was uploaded to S3 via os operations. New for me was os.walk and os.path.relpath  

I decided to switch my approach once again since I remembered that RapidAPI is a thing! So rather than getting official data from the official API, for now I will be getting my data from this unofficial API: https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/olympic-sports-api  
Since RapidAPI uses an API key, I set up dotenv and included it in .gitignore  

At this point I set up the Lambda function to extract the data. This is my first time writing a Lambda function and it will also be my first time using AWS CloudWatch. As I was setting up the Lambda funciton I got this error:  
User: arn:aws:iam::058264546342:user/olympics-user1 is not authorized to perform: iam:CreateRole on resource: arn:aws:iam::058264546342:role/service-role/OlympicsDataExtraction-role-gxqt7ypj because no identity-based policy allows the iam:CreateRole action  
The workaround was to create a custom policy (that I decided to call IAMLambdaPermission) so that no more control than needed was added. Only creating an attaching roles (and others needed to make those work) was needed and so a new policy was created using the following JSON and attached to the IAM User:  
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:PassRole",
                "iam:PutRolePolicy",
                "iam:GetRole"
            ],
            "Resource": "arn:aws:iam::058264546342:role/*"
        }
    ]
}
However, I was quickly faced with another error displaying that the IAM user needs to be able to create policies as well so the JSON was slightly modified to include this as well:  
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:PassRole",
                "iam:PutRolePolicy",
                "iam:GetRole",
                "iam:CreatePolicy"
            ],
            "Resource": "*"
        }
    ]
}
With this, I was able to create the Lambda function!  
It took some getting used to the Lambda function editor and finding where to set environment variables (that are loaded with os.environ) but once the Lambda function was written, I needed to attach two policies to the role that was created when the Lambda function was created: AmazonS3FullAccess for S3 access and CloudWatchLogsFullAccess for CloudWatch logs access. And this brought attention to the fact that the current IAM user can't list policies and therefore the following line was added to the IAMLambdaPermission policy: "iam:ListPolicies"  
With our Lambda function having full access to S3 and CloudWatch, I then proceeded to test the funciton. This was done by creating a test event to invoke the function. When testing, I ran into the problem of Lambda not recognizing the 'requests' module. This was resolved by creating a deployment package: a directory with the newly written lambda code and the 'requests' library. A file named lambda_function.py was created and requests was pip installed. When pip installing, it was important to use the following flag in the bash command (this was completely new to me):
pip install requests -t . (this is important to include all files associated with the module in the directory)
Everything was then zipped using the following bash command (this was also completely new to me):
zip -r ../my_lambda_function.zip .  
The zip file was uploaded and overwrote the current code. Another thing that prevented me from testing was the handle. Since the Python file was named my_lambda_function.py, I had to change the handle in Runtime settings from lambda_function.lambda_handler to my_lambda_function.lambda_handler. In the future, I will have my file names simply be called lambda_function.py  
Another problem was timeout. The task timed out after 3 seconds and so the timeout setting was increased to 10 seconds instead. And with that, I was able to run my first succesful Lambda function (test)! To confirm, the json data is indeed in the S3 bucket for raw data  

The next step is to write the Lambda function that will transform the data. After previewing the JSON data in S3 I decided to start with just creating the athletes table with the following columns:  
id, name, country, sport  
Gender is not available in the data which is pretty sad. These are the only four keys and sport is missing for quite a few. This is not a very extensive dataset given from the API but it's all about the experience working with the services so let's move forward  

For the data transformation, my first instinct is to use pandas but since we're working in an AWS environment, I decided to try AWS Data Wrangler for the first time. A new Lambda function called OlympicsDataTransformation was created as well as a new S3 Bucket called olympics-data-transformed  
The Lambda file was written and for the testing of the function to go through, we once again had to increase the timeout from 3 seconds to 10 seconds just to find out that Lambda doesn't know what 'pandas' is haha. So once again, we also had to create a deployment package with pandas pip installed, zip it and import it into Lambda, just like we did with the 'requests' module deployment package for the lambda_function_extract. The difference here is that the directory is a lot bigger with slightly more complex structure that confused the Lambda interpreter the first time I tried so we use a different bash command when zipping:
zip -r9 ../lambda_function_transform.zip .
The -r flag means that we're zipping everything recursively and the 9 sets the compression level to the highest level (9), which means the zip file will be as small as possible, though it may take a bit longer to create. We then add the python file to the zip file using:  
zip -g lambda_function_transform.zip lambda_function_transform.py  
This is what I tried to do. But it simply did not want to work. So I found a way to use AWS Data Wrangler without using a pandas DataFrame! It made everything so much incredibly easier haha, and the code became SO MUCH SIMPLER. But... there was still an error saying that Lambda doesn't recognize the AWS Data Wrangler module. So I switched over to Glue!  

In order to get started with Glue I first had to swithc to my root user in order to give the IAM user created for the project access to Glue. I started by creating a database for the olympics data. I then created the crawler that will index our S3 data to infer the schema. After that I created the ETL job.  
Writing the ETL job script (which uses Spark) was by far the most annoying part of the project so far. I got error after error after error and I kept having ChatGPT re-writing the script over and over and wasn't really learning anything. One thing from my side was realizing after a few re-writes that I only had attached S3 read permission to the current IAM user and not write access which definitely interfered from my side.  
After the job finally succeeded, I had GPT summarize the most important key changes:  
1. Error: INVALID_ARGUMENT_ERROR; AttributeError: 'DynamicFrame' object has no attribute 'explode'
Issue: The initial approach tried to use the explode function directly on a DynamicFrame, which doesn’t support this method.
Solution: Converted the DynamicFrame to a Spark DataFrame using .toDF() before applying the explode function. This allowed us to work with the nested JSON structure effectively.
2. Error: UNCLASSIFIED_ERROR; com.amazonaws.services.glue.types.ArrayNode cannot be cast to com.amazonaws.services.glue.types.ObjectNode
Issue: This error occurred when attempting to relationalize or transform a nested array incorrectly in the DynamicFrame.
Solution: Rather than trying to relationalize complex structures directly, we focused on manipulating the DataFrame (which is more flexible) by selecting and transforming only the required fields (id, name, country, sport) after exploding the athletes array.  

To automatically trigger the ETL process whenever a new object is uploaded to the raw data S3 bucket, I now had to set up an S3 Object Created Event in combination with an AWS Lambda function that invokes the Glue ETL job. So I had to use a Data Transformation Lambda function anyway haha  
This proccess started by creating an event notification for the raw data S3 bucket. This was my first time creating an event notification for any S3 bucket. I named the notification trigger-glue-etl and limited the notification only to .json files. s3:ObjectCreated:* was selected for the Event type and Lambda function as Destination. I opened a new tab, created the Lambda function calling it trigger-glue-etl-job (I had to log in to my root user to attach a policy to the IAM role that allows the Lambda function to invoke Glue jobs), and selected it in the previous tab to finish setting up the event notification. The Lambda function was the simplest yet.  
The workflow was confirmed to be working by manually starting the Lambda function that extracts data, confirming that a new JSON file was uploaded in the raw data S3 bucket, a new job run was initiated in Glue, and the transformed data indeed appeared in the transformed data S3 bucket neatly partitioned by sport as Parquet files!  

What caught my attention now is that I manually update the page variable in the Lambda function for data extraction every time I run the Lambda function. I decided to automate this as well using a DynamoDB table to store the current page number!  
A new DynamoDB table was created called OlympicsAPIState and 'id' was set as primary key with a String type. As the initial record, an item was added with id = "currentPage" and page = 4 (since I had done 3 API calls with pages 1, 2 and 3). And with the DynamoDB table created, the data extraction Lambda funciton was modified to fetch the page number from DynamoDB. With all this I also had to add a policy for full access to DynamoDB to the IAM user from my root user, as well as the role associated with the Lambda function  

The only thing left now is running some Athena SQL queries to examine the dataset. I will connect it to QuickSight as well just to get some hands-on experience with the service  
Athena was not as simple as point it to the transformed data S3 bucket and run some queries haha. I had to first create a Glue crawler to infer the schema from the transformed data bucket. Getting the crawler to create a table became a bit of a hassle but allowing the IAM user to see CloudWatch logs pointed out the error that the crawler doesn't have permission to upload S3 objects and after a little bit more digging I found the real source of the problem: The IAM Role I created for the previous crawler (that I also assigned to this crawler) only gave permission to Get and Put objects in the raw data bucket haha. So the transformed data bucket was added as a resource as well. Running the crawler *now* automatically created the desired table.  

Running this simple query in Athena:  
SELECT * 
FROM "AwsDataCatalog"."olympics_data"."olympics2024_bucket_transformed" 
WHERE sport = 'Skateboarding'
LIMIT 10;
gave this result:
#	id	name	country	sport
1	71458	Augusto Akio	BRA	Skateboarding
2	71458	Augusto Akio	BRA	Skateboarding
3	71458	Augusto Akio	BRA	Skateboarding

Number one, this pointed out how rather lackluster the dataset is at the time of querying, and 2. there are evidently duplicates in the data. So the dataset is not something to brag about at all but hands-on experience on how to take data from an API all the way to Athena, fully automated, has been gained!  

In QuickSight, 

We were not able to extract high quality data from the official API and not able to do any interesting visualizations in Amazon QuickSight but this project has given valuable hands-on experience and insight nevertheless! The pipeline can be fully automated with CloudWatch to trigger daily  