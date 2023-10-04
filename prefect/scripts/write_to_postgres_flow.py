# Need to install wget, prefect, psycopg2
"""
Script to ingest ny-taxi data to local postgres db running in docker.
"""
import os
from time import time
import pandas as pd
import sqlalchemy.engine
from sqlalchemy import create_engine
import gzip
from prefect import task, flow
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(retries=3, cache_key_fn=task_input_hash, cache_expiration=timedelta(days=1))
def get_data(url: str, gzip_file: str, csv_name: str) -> pd.DataFrame:
    """
    Download data from DE-Zoompcamp github using wget
    """
    # Download the csv
    try:
        os.system(f"wget {url} -O {gzip_file}")

    except Exception as e:
        print(f"Download failed with exception: {e}")

    print("Unzipping to csv ... ")
    with gzip.open(gzip_file, 'rt', newline='') as csv_file:
        csv_data = csv_file.read()
    with open(csv_name, 'wt') as out_file:
         out_file.write(csv_data)

    print("Unzip finished. File saved as csv ... ")

    df = pd.read_csv(csv_name)
    return df

@task()
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert date fields to datetime and filter rows with no passengers.
    """
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

    print(f"pre: missing passenger count: {df['passenger_count'].isin([0]).sum()}")
    df = df[df['passenger_count'] != 0]
    print(f"post: missing passenger count: {df['passenger_count'].isin([0]).sum()}")
    return df

@task()
def get_conn(user: str, password:str, host:str, port:str, db:str) -> sqlalchemy.engine.Engine:
    """
    Get postgres connector.
    """
    try:
      engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    except Exception as e:
        print(f"Failed to connect to Postgres with exception {e}")
        raise
    return engine

@task()
def create_table(engine, table_name: str, df: pd.DataFrame) -> True:
    """
    Create a new table and replace if exists.
    """
    df.head(0).to_sql(name=table_name, con=engine, if_exists='replace')
    return True

@task()
def write_to_postgres(engine: sqlalchemy.engine.Engine, table_name: str, df: pd.DataFrame, chunksize: int) -> True:
    t_start = time()
    try:
        df = clean_data(df)
        df.to_sql(table_name, con=engine, if_exists='append', index=False, chunksize=chunksize)
    except Exception as e:
        print("Failed with exception {e}")
        raise 
    t_end = time()
    print(f"Write finished, took {t_end-t_start} seconds.")
    return True

@flow(name="Ingest NY-taxi data")
def flow():

    user = "root"
    password = "root"
    host = "localhost"
    port = "5432"
    db = "ny_taxi"
    table_name = "yellow_taxi_data"
    url = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
    gzip_file = 'output.csv.gz'
    csv_name = 'output.csv'

    df = get_data(url, gzip_file, csv_name)
    engine = get_conn(user, password, host, port, db)
    create_table(engine, table_name, df)
    write_to_postgres(engine, table_name, df, chunksize=100000)

if __name__ == '__main__':
    flow()