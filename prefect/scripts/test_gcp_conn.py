# pip install google-cloud-storage

from google.cloud import storage

# Set your credentials file path and bucket name
credentials_path = '~/google-cloud-sdk/dtc-de-2023.json'
project_id = 'dtc-de-2023'
bucket_name = 'ny-taxi-trips'

def create_bucket(project_id, bucket_name):
    """Creates a new bucket."""
    storage_client = storage.Client.from_service_account_json(credentials_path, project=project_id)
    bucket = storage_client.create_bucket(bucket_name)

    print(f'Bucket {bucket_name} created.')

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client.from_service_account_json(credentials_path)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f'File {source_file_name} uploaded to {destination_blob_name}.')

# Example usage
create_bucket(project_id, bucket_name)
# upload_blob(bucket_name, 'local_file.txt', 'remote_file.txt')