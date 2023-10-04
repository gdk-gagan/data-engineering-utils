# Needs pandas-gbq for using df.to_gbq function

import pandas as pd
from prefect import task, flow
from prefect.tasks import task_input_hash
from datetime import timedelta
from prefect_gcp.cloud_storage import GcsBucket
from prefect_gcp import GcpCredentials

@task()
def extract_from_gcs(color: str, month: int, year: int) -> str:
    """GCS Block.get_directory - Copies a folder from the configured GCS bucket to a local directory. 
    Defaults to copying the entire contents of the block's bucket_folder to the current working directory."""
    gcs_path = f"data/{color}/{color}_tripdata_{year}-{month:02}"
    local_path = f"../data/"
    gcs_block = GcsBucket.load("de-gcs-bucket")
    gcs_block.get_directory(from_path=gcs_path, local_path=local_path)
    return local_path

@task()
def transform(path: str) -> pd.DataFrame:
    """Reads data saved to local path in a dataframe, transforms and returns a df """
    df = pd.read_parquet(path)
    print(f"pre: missing passenger count: {df['passenger_count'].isna().sum()}")
    df["passenger_count"] = df["passenger_count"].fillna(0)
    print(f"post: missing passenger count: {df['passenger_count'].isna().sum()}")
    return df

@task()
def write_to_bq(df: pd.DataFrame) -> None:
    """Write transformed data to big query. Make sure that the table already exists in big query. 
    Create a table using console and truncate it.
    NOTE: project_id is not the same as project_name."""
   
    gcp_credentials_block = GcpCredentials.load("de-gcp-creds")

    df.to_gbq(destination_table='ny_taxi.yellow_taxi',
              project_id='dtc-de-2023-398823',
              credentials=gcp_credentials_block.get_credentials_from_service_account(),
              if_exists='append',
              chunksize='500_000')
    return True

@flow()
def etl_gcs_to_bg():
    """Main ETL flow to load data into Big query"""
    color = "yellow"
    month = 1
    year = 2021

    path = extract_from_gcs(color, month, year)
    df = transform(path)
    write_to_bq(df)


if __name__ == '__main__':
    etl_gcs_to_bg()