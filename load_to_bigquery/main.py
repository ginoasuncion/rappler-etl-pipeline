import os
import json
import logging
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound
from flask import Flask, request

# Set up logging for visibility in Cloud Run logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use default service account provided by Cloud Run
bq_client = bigquery.Client()
storage_client = storage.Client()

def load_json_to_bq(request):
    """
    Triggered by an HTTP request when a new file is uploaded to Cloud Storage.
    Loads data into BigQuery using a temporary staging table and MERGE logic.
    """
    try:
        request_json = request.get_json()

        # Extract bucket and filename from request
        bucket_name = request_json['bucket']
        file_name = request_json['name']
        logger.info(f"Received file: {file_name} from bucket: {bucket_name}")

        # Get environment configs
        project_id = os.environ.get("GCP_PROJECT")
        dataset_id = os.environ.get("BQ_DATASET")
        table_id = os.environ.get("BQ_TABLE")
        full_table = f"{project_id}.{dataset_id}.{table_id}"
        temp_table = f"{table_id}_temp"

        # Read file from GCS
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        content = blob.download_as_string()
        records = json.loads(content)

        # Flatten fields
        for article in records:
            article['categories'] = ', '.join(article['categories'])
            article['tags'] = ', '.join(article['tags'])

        # Define table schema
        schema = [
            bigquery.SchemaField("article_id", "STRING"),
            bigquery.SchemaField("datetime", "TIMESTAMP"),
            bigquery.SchemaField("title", "STRING"),
            bigquery.SchemaField("link", "STRING"),
            bigquery.SchemaField("categories", "STRING"),
            bigquery.SchemaField("tags", "STRING")
        ]

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_TRUNCATE",
            autodetect=False
        )

        # Load to temp table
        logger.info(f"Loading data into temp table: {temp_table}")
        load_job = bq_client.load_table_from_json(
            records,
            f"{project_id}.{dataset_id}.{temp_table}",
            job_config=job_config
        )
        load_job.result()

        # Merge temp into main table
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

        logger.info("Running MERGE into main table")
        query_job = bq_client.query(merge_query)
        query_job.result()
        logger.info(f"Successfully merged into {full_table}")

        # Delete temp table
        try:
            bq_client.delete_table(f"{project_id}.{dataset_id}.{temp_table}")
            logger.info(f"Deleted temporary table {temp_table}")
        except NotFound:
            logger.warning(f"Temporary table {temp_table} not found during cleanup.")

        return f"Processed and merged file: {file_name}", 200

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return f"Error: {str(e)}", 500

# Set up Flask app
app = Flask(__name__)

@app.route('/', methods=['POST'])
def index():
    return load_json_to_bq(request)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
