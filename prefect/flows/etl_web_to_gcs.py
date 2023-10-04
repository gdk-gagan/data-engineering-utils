# Download data from the web, do transformations (data type cleaning), 
# convert into parquet, write locally and then send to Google cloud storage.
# pip install prefect_gcp, pyarrow (for parquet gzip compression)
# Create a bucket in Google cloud storage from the console.
# To use prefect blocks, run the command 'prefect block register -m prefect_gcp'
# before running the script
# Create Blocks in prefect console for GCS Bucket and GCS credentials
# Prefect doc for blocks code usage for uploading/downloading data - https://prefecthq.github.io/prefect-gcp/examples_catalog/

#from pathlib import Path
import pandas as pd
from prefect import task, flow
from prefect.tasks import task_input_hash
from datetime import timedelta
from prefect_gcp.cloud_storage import GcsBucket

@task(retries=3, cache_key_fn=task_input_hash, cache_expiration=timedelta(days=1))
def fetch(dataset_url: str) -> pd.DataFrame:
    """Read taxi data from URL"""

    df = pd.read_csv(dataset_url)
    return df

@task(log_prints=True)
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Fix dtypes"""
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    print(f"Columns: {df.dtypes}")
    print(f"Rows: {len(df)}")
    return df

@task()
def write_to_local(df: pd.DataFrame, color: str, dataset_file: str) -> None:
    """Write the dataframe out as a parquet file"""
    # path = Path(f"data/{color}/{dataset_file}.parquet")
    path = f"data/{color}/{dataset_file}.parquet"
    df.to_parquet(path, compression="gzip")
    print(f"Path : {path}")
    return path

@task()
def write_to_gcs(path: str):
    """Uploading local file to GCS"""
    gcs_block = GcsBucket.load("de-gcs-bucket")
    gcs_block.upload_from_path(
        from_path=path,
        to_path=path
    )

@flow()
def etl_web_to_gcs() -> None:
    """The main ETL function"""
    color = "yellow"
    month = 1
    year = 2021
    dataset_file = f"{color}_tripdata_{year}-{month:02}"
    dataset_url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz"

    df = fetch(dataset_url)
    df_clean = clean(df)
    path = write_to_local(df_clean, color, dataset_file)
    write_to_gcs(path)


if __name__ == '__main__':
    etl_web_to_gcs()