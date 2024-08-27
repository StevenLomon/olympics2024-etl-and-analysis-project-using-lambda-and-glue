import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Load the raw data from the S3 bucket
raw_data = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://olympics2024-bucket-raw/"]},
    format="json"
)

# Convert the DynamicFrame to a Spark DataFrame for easier manipulation
df = raw_data.toDF()

# Explode the athletes array into individual rows
exploded_df = df.selectExpr("year", "explode(athletes) as athlete")

# Select only the required columns and rename them
selected_df = exploded_df.select(
    "athlete.id",
    "athlete.name",
    "athlete.country",
    "athlete.sport"
)

# Convert the DataFrame back to a DynamicFrame
selected_dynamic_frame = DynamicFrame.fromDF(selected_df, glueContext, "selected_dynamic_frame")

# Write the transformed data to the destination S3 bucket in Parquet format partitioned by 'sport'
output_path = "s3://olympics2024-bucket-transformed/"
glueContext.write_dynamic_frame.from_options(
    frame=selected_dynamic_frame,
    connection_type="s3",
    connection_options={
        "path": output_path,
        "partitionKeys": ["sport"]  # Partition by 'sport'
    },
    format="parquet"  # Write as Parquet
)

# Commit the job
job.commit()
