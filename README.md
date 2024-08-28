This is a Data Engineering project that models the Spotify API project mentioned in this video: https://www.youtube.com/watch?v=X8Fin2zMKK4 by Darshil Parmar: https://www.linkedin.com/in/darshil-parmar/
Instead of getting data from the Spotify API, the data will be from the Paris Olympics 2024 API: https://data.paris2024.org/api/explore/v2.1/console
(however, since there's been 5 days with no access to the API Data, RapidAPI was used instead: https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/olympic-sports-api)
The AWS Services that will be used are S3, Lambda, AWS Glue, DynamoDB and Athena. The AWS Data Wrangler library will be used over pandas for the data transformation since we're working with AWS services. The pipeline can be fully automated to trigger daily with Amazon CloudWatch EventBridge and the provisioning of the resources can be automated with Terraform (not implemented in this first version of the project)

To start the project, data from the API was asked for access by atuhorizing on the official website.   
While waiting for the request access, an IAM User was being set up that will be used during the project. This user will only have full access to all of the services that are used in the project and these services only as per the Principle of Least Privilege. The user will both have console access (with MFA) and programmatic access via the CLI and the user will also be disabled by the end of the project to minimuze security risks.  
(When applying policies, I stumbled upon the two types of CloudWatch for the first time: AWS CloudWatchEvidently and AWS CloudWatchRUM (Real User Monitoring). CloudWatchEvidently is moreso used for A/B testing and feature flag management and so for this project CloudWatchRUM will instead be used. This is also more in line with what I learned when studying for the Cloud Practitioner Exam haha)  
Since all of the services that will be used throughout the project are avaialble in the Stockholm (eu-north-1) region and it's the closest one location-wise, this is the one that will be used.  

(I decided to switch my approach once again since I remembered that RapidAPI is a thing! So rather than getting official data from the official API, for now I will be getting my data from this unofficial API: https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/olympic-sports-api)   

At this point I set up the Lambda function to extract the data. (This is my first time writing a Lambda function and as with doing anything for the first time; everything is new but exciting and I'm focusing on failing forward!) When setting up the Lambda fucntion, the following error was encountered:
User: arn:aws:iam::058264546342:user/olympics-user1 is not authorized to perform: iam:CreateRole on resource: arn:aws:iam::058264546342:role/service-role/OlympicsDataExtraction-role-gxqt7ypj because no identity-based policy allows the iam:CreateRole action  
The workaround was to create a custom policy so that no more control than needed was added. Only creating an attaching roles (and others needed to make those work) was needed and so a new policy was created using the following JSON and attached to the IAM User:  
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
However, with another error quickly surfaced displaying that the IAM user needs to be able to create policies as well so the JSON was slightly modified to include this as well:  
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
With this, the Lambda function was able to be created!  
It took some getting used to the Lambda function editor and finding where to set environment variables (that are loaded with os.environ) but once the Lambda function was written, two policies needed to be attached to the role that was created when the Lambda function was created: AmazonS3FullAccess for S3 access and CloudWatchLogsFullAccess for CloudWatch logs access. And this brought attention to the fact that the current IAM user can't list policies and therefore the following line was added to the IAMLambdaPermission policy: "iam:ListPolicies"  

With the  Lambda function having full access to S3 and CloudWatch, funciton was tested. This was done by creating a test event to invoke the function. When testing, another problem surfaced: Lambda not recognizing the 'requests' module. This was resolved by creating a deployment package: a directory with the newly written lambda code and the 'requests' library. A file named lambda_function.py was created and requests was pip installed. When pip installing, it was important to use the following flag in the bash command (this was completely new to me):
pip install requests -t . (this is important to include all files associated with the module in the directory)
Everything was then zipped using the following bash command (this was also completely new to me):
zip -r ../my_lambda_function.zip .  

The zip file was uploaded and overwrote the current code. Another thing that prevented the code from testing was the handle. Since the Python file was named my_lambda_function.py, the handle in Runtime settings had to be changed from lambda_function.lambda_handler to my_lambda_function.lambda_handler. (In the future, I will have my file names simply be called lambda_function.py)    
Another problem was timeout. The task timed out after 3 seconds and so the timeout setting was increased to 10 seconds instead. And with that, the first successful Lambda test was able to run! To confirm, the json data was indeed in the S3 bucket for raw data  

The next step was to write the Lambda function that will transform the data. The JSON data was previewed in S3 which infered the athletes table to be created with the following columns:  
id, name, country, sport  
Gender is not available in the data which is pretty sad. These are the only four keys and sport is missing for quite a few. This is not a very extensive dataset given from the API but it's all about the experience working with the services so let's move forward  

** The following ended up not being used **
(For the data transformation, my first instinct is to use pandas but since we're working in an AWS environment, I decided to try AWS Data Wrangler for the first time.)  
A new Lambda function called OlympicsDataTransformation was created as well as a new S3 Bucket called olympics-data-transformed. The Lambda file was written and for the testing of the function to go through, the timeout once again had to be incresed from 3 seconds to 10 seconds just to find out that Lambda doesn't know what 'pandas' is haha. So once again, a deployment package also had to be created with pandas pip installed. It was zipped and imported into Lambda, just like the 'requests' module deployment package for the lambda_function_extract.  

The difference here is that the directory is a lot bigger with slightly more complex structure that confused the Lambda interpreter the first time. Therefore, a different bash command when zipping:
zip -r9 ../lambda_function_transform.zip .
The -r flag means that everything is zipped recursively and the 9 sets the compression level to the highest level (9), which means the zip file will be as small as possible, though it may take a bit longer to create. The python file was then added to the zip file using:  
zip -g lambda_function_transform.zip lambda_function_transform.py  
(This is what I tried to do. But it simply did not want to work. So I found a way to use AWS Data Wrangler without using a pandas DataFrame! It made everything so much incredibly easier haha, and the code became SO MUCH SIMPLER. But... there was still an error saying that Lambda doesn't recognize the AWS Data Wrangler module. So I switched over to Glue!)  
** The following ended up not being used **   

In order to get started with Glue, the IAM user created for the project had to given access to Glue which was done using the root user. First, a database was created for the olympics data. Then the crawler that will index our S3 data to infer the schema was created. Next was creating the ETL job:    
(Writing the ETL job script (which uses Spark) was by far the most annoying part of the project. I got error after error after error and I kept having ChatGPT re-writing the script over and over and wasn't really learning anything. One thing from my side was realizing after a few re-writes that I only had attached S3 read permission to the current IAM user and not write access which definitely interfered from my side.)  
After the job finally succeeded, GPT kindly summarized the most important key changes:  
1. Error: INVALID_ARGUMENT_ERROR; AttributeError: 'DynamicFrame' object has no attribute 'explode'
Issue: The initial approach tried to use the explode function directly on a DynamicFrame, which doesn’t support this method.
Solution: Converted the DynamicFrame to a Spark DataFrame using .toDF() before applying the explode function. This allowed us to work with the nested JSON structure effectively.
2. Error: UNCLASSIFIED_ERROR; com.amazonaws.services.glue.types.ArrayNode cannot be cast to com.amazonaws.services.glue.types.ObjectNode
Issue: This error occurred when attempting to relationalize or transform a nested array incorrectly in the DynamicFrame.
Solution: Rather than trying to relationalize complex structures directly, we focused on manipulating the DataFrame (which is more flexible) by selecting and transforming only the required fields (id, name, country, sport) after exploding the athletes array.  

To automatically trigger the ETL process whenever a new object is uploaded to the raw data S3 bucket, an S3 Object Created Event in combination with an AWS Lambda function that invokes the Glue ETL job had to be set up. (So I had to use a Data Transformation Lambda function anyway haha)  
This proccess started by creating an event notification for the raw data S3 bucket. (This was my first time creating an event notification for any S3 bucket. The notification was named trigger-glue-etl and limited the notification only to .json files. s3:ObjectCreated:* was selected for the Event type and Lambda function as Destination. I opened a new tab, created the Lambda function calling it trigger-glue-etl-job (I had to log in to my root user to attach a policy to the IAM role that allows the Lambda function to invoke Glue jobs haha), and selected it in the previous tab to finish setting up the event notification. And the Lambda function was the simplest yet!)    
The workflow was confirmed to be working by manually starting the Lambda function that extracts data, confirming that a new JSON file was uploaded in the raw data S3 bucket, a new job run was initiated in Glue, and the transformed data indeed appeared in the transformed data S3 bucket neatly partitioned by sport as Parquet files!  

(What caught my attention now is that I manually update the page variable in the Lambda function for data extraction every time I run the Lambda function. I decided to automate this as well using a DynamoDB table to store the current page number!  
A new DynamoDB table was created called OlympicsAPIState and 'id' was set as primary key with a String type. As the initial record, an item was added with id = "currentPage" and page = 4 (since I had done 3 API calls with pages 1, 2 and 3). And with the DynamoDB table created, the data extraction Lambda funciton was modified to fetch the page number from DynamoDB. With all this I also had to add a policy for full access to DynamoDB to the IAM user from my root user, as well as the role associated with the Lambda function)  

The only thing left at this point was running some Athena SQL queries to examine the dataset. (and Athena was not as simple as point it to the transformed data S3 bucket and run some queries haha.)  
First, a Glue crawler to infer the schema from the transformed data bucket had to be created. Getting the crawler to create a table became a bit of a hassle but allowing the IAM user to see CloudWatch logs pointed out the error that the crawler doesn't have permission to upload S3 objects and after a little bit more digging, the real source of the problem was found: The IAM Role previously created for the previous crawler (that I also assigned to this crawler) only gave permission to Get and Put objects in the raw data bucket haha. So the transformed data bucket was added as a resource as well. Running the crawler *now* automatically created the desired table.    

Running this simple query in Athena:  
SELECT * 
FROM "AwsDataCatalog"."olympics_data"."olympics2024_bucket_transformed" 
WHERE sport = 'Skateboarding'
LIMIT 10;
gave this result:
	id	name	country	sport
1	71458	Augusto Akio	BRA	Skateboarding
2	71458	Augusto Akio	BRA	Skateboarding
3	71458	Augusto Akio	BRA	Skateboarding

Number one, this pointed out how rather lackluster the dataset is at the time of querying, and 2. there are evidently duplicates in the data. So the dataset is not something to brag about at all but hands-on experience on how to take data from an API all the way to Athena, fully automated, has been gained!  

(I decided not to use QuickSight since I didn't have an interesting dataset and as to not start the free trial. I will most likely use it in a project in the future!)   

The pipeline can be fully automated with CloudWatch EventBridge to trigger daily by creating a rule with a name like 'olympic-data-pipeline-daily-trigger', setting the rule type to Schedule. Either the rate would be set to rate(1 day) or the Cron expression would be set to cron(0 0 * * ? *). A flexibel time window of say 15 minutes could be set as well. The target API would be AWS Lambda Invoke pointing to the OlympicsDataExtraction Lambda function.  

We were not able to extract high quality data from the official API and not able to do any interesting visualizations in Amazon QuickSight but this project has given valuable hands-on experience and insight with a lot of AWS Services for Data Engineering nevertheless! 