# Dockerize the data ingestion script (raw_data_csv.ipynb)
# Use argparse to pass named arguments from command-line to this script

import os
from time import time
import argparse
import pandas as pd
from sqlalchemy import create_engine
import gzip

def main(params):

    # Tip - Shortcut to select all arguments - Cmd+Shift+L and Cmd+Shift+Right arrow
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    url = params.url
    gzip_file = '../data/output.csv.gz'
    csv_name = '../data/output.csv'

    # Download the csv
    os.system(f"wget {url} -O {gzip_file}")

    print("Unzipping to csv ... ")
    with gzip.open(gzip_file, 'rt', newline='') as csv_file:
        csv_data = csv_file.read()
    with open(csv_name, 'wt') as out_file:
         out_file.write(csv_data)
    print("Unzip finished. File saved as csv ... ")
    
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    df_iter = pd.read_csv(csv_name, iterator=True, chunksize=100000)
    df = next(df_iter)

    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

    # Create a new table and replace if exists
    df.head(0).to_sql(name=table_name, con=engine, if_exists='replace')

    # write data using append
    df.to_sql(name=table_name, con=engine, if_exists='append')

    while True:
        t_start = time()
        df = next(df_iter)
        df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
        df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
        df.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')
        t_end = time()
        print(f"Inserted another chunk, took {t_end-t_start} seconds.")


if __name__ == '__main__':
    # args for user, password, host, port, table_name, file-url
    parser = argparse.ArgumentParser(description='Ingest data into Postgres')
    parser.add_argument('--user', help='Postgres user')
    parser.add_argument('--password', help='Postgres password')
    parser.add_argument('--host', help='Postgres hostname')
    parser.add_argument('--port', help='Postgres port')
    parser.add_argument('--db', help='Postgres database name')
    parser.add_argument('--table_name', help='Postgres table name')
    parser.add_argument('--url', help='url of the csv file')

    args = parser.parse_args()
    
    main(args)