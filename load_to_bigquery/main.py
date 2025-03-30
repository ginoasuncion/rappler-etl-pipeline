from flask import Flask, jsonify
import os
import json
import uuid
import logging
from google.oauth2 import service_account
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound
import re

# Set up logging for better visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authenticate using the service account specified by the GOOGLE_APPLICATION_CREDENTIALS environment variable
credentials = service_account.Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

# Create clients with the credentials
bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)
storage_client = storage.Client(credentials=credentials, project=credentials.project_id)

app = Flask(__name__)

@app.route('/', methods=['POST'])
def run_data_processing():
    """
    This endpoint automatically processes the latest file from the bucket.
    The bucket name is fetched from environment variables.
    """
    try:
        # Fetch the bucket name from the environment variable
        bucket_name = os.environ.get('BUCKET_NAME')

        if not bucket_name:
            return jsonify({"error": "Bucket name is not set in the environment variables."}), 500

        # Trigger the data processing function
        load_json_to_bq(bucket_name)  # Passing the bucket name directly

        return jsonify({"message": f"Data from the latest file in bucket {bucket_name} has been loaded to BigQuery."})

    except Exception as e:
        logger.error(f"Error occurred while processing data: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def load_json_to_bq(bucket_name):
    try:
        # Debugging the structure of event
        logger.info(f"Processing data from bucket: {bucket_name}")

        # Config
        project_id = os.environ.get("GCP_PROJECT", "your-gcp-project-id")
        dataset_id = os.environ.get("BQ_DATASET", "your-bigquery-dataset")
        table_id = os.environ.get("BQ_TABLE", "your-bigquery-table")
        full_table = f"{project_id}.{dataset_id}.{table_id}"

        temp_table = f"{table_id}_temp_{uuid.uuid4().hex[:8]}"  # random temp table name

        # Step 1: Find the latest file based on timestamp in filename
        latest_file = get_latest_file_from_bucket(bucket_name)

        if not latest_file:
            raise ValueError("No valid files found in the bucket.")

        logger.info(f"Selected latest file: {latest_file}")

        # Load file from GCS
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(latest_file)
        content = blob.download_as_string()
        records = json.loads(content)

        # Flatten 'categories' and 'tags' to comma-separated strings
        for article in records:
            article['categories'] = ', '.join(article['categories'])
            article['tags'] = ', '.join(article['tags'])

        # Define schema for the temp table
        schema = [
            bigquery.SchemaField("article_id", "STRING"),
            bigquery.SchemaField("datetime", "TIMESTAMP"),
            bigquery.SchemaField("title", "STRING"),
            bigquery.SchemaField("link", "STRING"),
            bigquery.SchemaField("categories", "STRING"),  # Flattened to string
            bigquery.SchemaField("tags", "STRING")  # Flattened to string
        ]

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_TRUNCATE",  # Replaces any existing data in the temporary table
            autodetect=False
        )

        # Step 2: Upload data to temporary table
        try:
            # Create temporary table in BigQuery (fully qualified table name)
            bq_client.create_table(bigquery.Table(f"{project_id}.{dataset_id}.{temp_table}", schema=schema))
            logger.info(f"Created temporary table {project_id}.{dataset_id}.{temp_table}")

            # Load data from GCS into the temporary table (fully qualified table name)
            load_job = bq_client.load_table_from_json(records, f"{project_id}.{dataset_id}.{temp_table}", job_config=job_config)
            load_job.result()  # Wait for the load job to complete
            logger.info(f"Loaded data into temporary table {project_id}.{dataset_id}.{temp_table}")

        except Exception as e:
            logger.error(f"Error occurred while uploading data to temp table: {e}")
            raise

        # Step 3: MERGE data from the temp table into the main table (fully qualified table names)
        merge_query = f"""
            MERGE `{full_table}` T
            USING `{project_id}.{dataset_id}.{temp_table}` S
            ON T.article_id = S.article_id
            WHEN MATCHED THEN
              UPDATE SET
                datetime = S.datetime,
                title = S.title,
                link = S.link,
                categories = S.categories,
                tags = S.tags
            WHEN NOT MATCHED THEN
              INSERT (article_id, datetime, title, link, categories, tags)
              VALUES (S.article_id, S.datetime, S.title, S.link, S.categories, S.tags)
        """
        try:
            # Execute the merge query to upsert data from temp table into the main table
            query_job = bq_client.query(merge_query)
            query_job.result()  # Wait for the query to finish
            logger.info(f"Successfully merged data into {full_table}")
        except Exception as e:
            logger.error(f"Error during MERGE operation: {e}")
            raise

        # Step 4: Cleanup - Delete the temporary table
        try:
            bq_client.delete_table(f"{project_id}.{dataset_id}.{temp_table}")
            logger.info(f"Deleted temporary table {project_id}.{dataset_id}.{temp_table}")
        except NotFound:
            logger.warning(f"Temporary table {project_id}.{dataset_id}.{temp_table} not found for deletion.")
        except Exception as e:
            logger.error(f"Error during cleanup (deleting temp table): {e}")
            raise

        # Log the successful operation
        logger.info(f"Upserted {len(records)} rows into {full_table}.")

    except Exception as e:
        logger.error(f"Failed to process data from GCS: {e}")
        raise


def get_latest_file_from_bucket(bucket_name):
    """
    Get the latest file in the given GCS bucket based on the timestamp in the filename.
    Assumes filenames contain a timestamp in the format 'YYYY-MM-DD_HH-MM-SS'.
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blobs = storage_client.list_blobs(bucket_name)

        # Regular expression to match filenames with timestamps (adjust the pattern as needed)
        timestamp_pattern = re.compile(r'rappler_articles_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.json')

        latest_file = None
        latest_timestamp = None

        for blob in blobs:
            match = timestamp_pattern.search(blob.name)
            if match:
                timestamp = match.group(1)
                if not latest_timestamp or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_file = blob.name

        return latest_file

    except Exception as e:
        logger.error(f"Error getting the latest file: {e}")
        return None


if __name__ == "__main__":
    # Use Cloud Run's port (8080) and disable Flask's debug mode for production
    app.run(debug=False, host='0.0.0.0', port=8080)
