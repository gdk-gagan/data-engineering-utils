import pyspark
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input_green', required=True)
parser.add_argument('--input_yellow', required=True)
parser.add_argument('--output', required=True)

args = parser.parse_args()

input_green = args.input_green
input_yellow = args.input_yellow
output = args.output

# creating the job by running the python script directly
# spark = SparkSession.builder\
#         .master("spark://Gagans-MacBook-Pro.local:7077")\
#         .appName('test') \
#         .getOrCreate()

# creating the job using spark-submit and passing master conf as arg
spark = SparkSession.builder\
        .appName('test') \
        .getOrCreate()

# Use the Cloud Storage bucket for temporary BigQuery export data used
# by the connector.
bucket = "dataproc-staging-us-central1-419760316501-eqrseixa"
spark.conf.set('temporaryGcsBucket', bucket)

df_yellow = spark.read.parquet(input_yellow)

df_green = spark.read.parquet(input_green)

df_yellow = df_yellow.withColumnRenamed("tpep_pickup_datetime", "pickup_datetime")                 .withColumnRenamed("tpep_dropoff_datetime", "dropoff_datetime")
df_yellow = df_yellow.withColumnRenamed("tpep_dropoff_datetime", "dropoff_datetime")                 .withColumnRenamed("tpep_dropoff_datetime", "dropoff_datetime")

df_green = df_green.withColumnRenamed("lpep_pickup_datetime", "pickup_datetime")                 .withColumnRenamed("lpep_dropoff_datetime", "dropoff_datetime")
df_green = df_green.withColumnRenamed("lpep_dropoff_datetime", "dropoff_datetime")                 .withColumnRenamed("lpep_dropoff_datetime", "dropoff_datetime")

# select common columns
common_cols = [
    'VendorID',
    'pickup_datetime',
    'dropoff_datetime',
    'store_and_fwd_flag',
    'RatecodeID',
    'PULocationID',
    'DOLocationID',
    'passenger_count',
    'trip_distance',
    'fare_amount',
    'extra',
    'mta_tax',
    'tip_amount',
    'tolls_amount',
    'improvement_surcharge',
    'total_amount',
    'payment_type',
    'congestion_surcharge'
]

df_yellow_com = df_yellow.select(common_cols).withColumn('service_type', F.lit('yellow'))
df_green_com = df_green.select(common_cols).withColumn('service_type', F.lit('green'))

df_trips_data = df_yellow_com.unionAll(df_green_com)


df_trips_data.createOrReplaceTempView('trips_data')
spark.sql("SELECT service_type, count(*) AS count FROM trips_data GROUP BY service_type").show()

# calculate revenue per month per service
df_result = spark.sql("""
SELECT 
    -- Reveneue grouping 
    PULocationID AS revenue_zone,
    date_trunc('month', pickup_datetime) AS revenue_month, 
    service_type, 

    -- Revenue calculation 
    SUM(fare_amount) AS revenue_monthly_fare,
    SUM(extra) AS revenue_monthly_extra,
    SUM(mta_tax) AS revenue_monthly_mta_tax,
    SUM(tip_amount) AS revenue_monthly_tip_amount,
    SUM(tolls_amount) AS revenue_monthly_tolls_amount,
    SUM(improvement_surcharge) AS revenue_monthly_improvement_surcharge,
    SUM(total_amount) AS revenue_monthly_total_amount,
    SUM(congestion_surcharge) AS revenue_monthly_congestion_surcharge,

    -- Additional calculations
    AVG(passenger_count) AS avg_montly_passenger_count,
    AVG(trip_distance) AS avg_montly_trip_distance
FROM
    trips_data
GROUP BY
    1, 2, 3
""")

# save the result as parquet but in a SINGLE FILE
df_result.write \
     .format('bigquery') \
     .option('table', 'output') \
     .save()