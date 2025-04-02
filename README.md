# 📰 Rappler ETL Pipeline

This project automates the extraction, storage, and loading of news articles from [Rappler](https://www.rappler.com/latest/) into Google BigQuery using a fully serverless architecture.

---

## 📦 Project Structure

```
rappler-etl-pipeline/
├── extract_to_gcs/           # Scraper: extracts articles and uploads to GCS
├── load_to_bigquery/         # Cloud Run service: loads data from GCS to BigQuery
└── README.md                 # You're here
```

---

## ⚙️ Technologies Used

- **Python + Flask** for REST APIs
- **Google Cloud Run** (serverless backend)
- **Google Cloud Storage** (for storing article JSON files)
- **Google BigQuery** (analytics database)
- **Eventarc** (auto-triggers Cloud Run on file upload)
- **gsutil / bq / gcloud** for deployment and testing

---

## 🚀 Architecture

This ETL pipeline is fully serverless and event-driven, designed to run automatically every 4 hours.

1. **Cloud Scheduler**  
   A time-based job that triggers the `extract-to-gcs` Cloud Run service every 4 hours via an HTTP request.  
   This ensures fresh data is regularly scraped from Rappler without manual intervention.

2. **extract-to-gcs** (Cloud Run)  
   Scrapes the latest news articles from Rappler and uploads them as JSON files to a Google Cloud Storage bucket (`rappler-hs-bkk`).

3. **File upload Trigger (Eventarc)**  
   Listens for new file uploads in the GCS bucket and automatically invokes the `load-to-bigquery` service.

4. **load-to-bigquery** (Cloud Run)  
   Parses the uploaded JSON file and appends only new article entries to BigQuery.  
   Articles already present (based on `article_id`) are skipped to prevent duplicates.

5. **BigQuery Table**  
   All cleaned and deduplicated article data is stored in the table: `rappler.rappler_articles`

---

### 🗺️ Workflow

        +-----------------------------+
        |       Cloud Scheduler       |
        |       (Every 4 Hours)       |
        +-------------+---------------+
                      |
                      v
        +-----------------------------+
        |        extract-to-gcs       |
        |          (Cloud Run)        |
        |       Scrapes Rappler       |
        +-------------+---------------+
                      |
                      v
        +-----------------------------+
        |    Google Cloud Storage     |
        |   Bucket: rappler-hs-bkk    |
        +-------------+---------------+
                      |
      Auto-trigger via File Upload (Eventarc)
                      v
        +-----------------------------+
        |       load-to-bigquery      |
        |          (Cloud Run)        |
        |     Parses & Loads to BQ    |
        +-------------+---------------+
                      |
                      v
        +-----------------------------+
        |           BigQuery          |
        |   rappler.rappler_articles  |
        +-----------------------------+





## 🛠️ Setup

### ✅ Environment Variables (used by Cloud Run)

| Variable              | Description                    |
|-----------------------|--------------------------------|
| `GCP_PROJECT`         | Your GCP project ID            |
| `BQ_DATASET`          | BigQuery dataset (e.g. `rappler`)  |
| `BQ_TABLE`            | BigQuery table (e.g. `rappler_articles`) |


---

### ✅ Create GCS Bucket
```bash
gsutil mb -l US gs://rappler-hs-bkk/
```

### ✅ Create BigQuery Dataset and Table

```bash
bq mk --dataset --location=US data-engineering-hs-bkk:rappler

bq mk --table data-engineering-hs-bkk:rappler.rappler_articles \
  article_id:STRING,datetime:TIMESTAMP,title:STRING,link:STRING,categories:STRING,tags:STRING
```
---

### ✅ Deploy `extract-to-gcs` to Cloud Run

```bash
gcloud run deploy extract-to-gcs \
  --source ./extract_to_gcs \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=data-engineering-hs-bkk@data-engineering-hs-bkk.iam.gserviceaccount.com \
  --set-env-vars "GCS_BUCKET=rappler-hs-bkk"
```

### ✅ Deploy `load-to-bigquery` to Cloud Run

```bash
gcloud run deploy load-to-bigquery \
  --source ./load_to_bigquery \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=data-engineering-hs-bkk@data-engineering-hs-bkk.iam.gserviceaccount.com \
  --set-env-vars "GCP_PROJECT=data-engineering-hs-bkk,BQ_DATASET=rappler,BQ_TABLE=rappler_articles"
```


### ✅ Create Cloud Scheduler Job (Run Every 4 Hours)
```bash
gcloud scheduler jobs create http trigger-extract-to-gcs \
  --schedule "0 */4 * * *" \
  --http-method GET \
  --uri https://extract-to-gcs-137287523276.us-central1.run.app \
  --oidc-service-account-email=data-engineering-hs-bkk@data-engineering-hs-bkk.iam.gs
```
---

### ✅ Create Eventarc Trigger for Auto-Loading

```bash
gcloud eventarc triggers create load-from-gcs \
  --location=us \
  --destination-run-service=load-to-bigquery \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=rappler-hs-bkk" \
  --service-account=data-engineering-hs-bkk@data-engineering-hs-bkk.iam.gserviceaccount.com
```

---

## 🙌 Author

**Gino Asuncion**  
ETL • Cloud • Automation  
[github.com/ginoasuncion](https://github.com/ginoasuncion)
