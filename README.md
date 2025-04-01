# 📰 Rappler ETL Pipeline (Cloud Run + BigQuery)

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

1. `extract_to_gcs`: Extracts the latest Rappler articles and uploads them as JSON to `rappler-hs-bkk` GCS bucket.
2. `load_to_bigquery`: Automatically triggered by file upload (via Eventarc) → parses and merges data into BigQuery.
3. Data is stored in BigQuery table: `rappler.rappler_articles`.

---

## 🛠️ Setup

### ✅ Environment Variables (used by Cloud Run)

| Variable              | Description                    |
|-----------------------|--------------------------------|
| `GCP_PROJECT`         | Your GCP project ID            |
| `BQ_DATASET`          | BigQuery dataset (e.g. `rappler`)  |
| `BQ_TABLE`            | BigQuery table (e.g. `rappler_articles`) |

---

### ✅ Deploy `extract-to-gcs` to Cloud Run
gcloud run deploy extract-to-gcs \
  --source ./extract_to_gcs \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=data-engineering-hs-bkk@data-engineering-hs-bkk.iam.gserviceaccount.com \
  --set-env-vars "GCS_BUCKET=rappler-hs-bkk"

### ✅ Deploy `load-to-bigquery` to Cloud Run

```bash
gcloud run deploy load-to-bigquery \
  --source ./load_to_bigquery \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=data-engineering-hs-bkk@data-engineering-hs-bkk.iam.gserviceaccount.com \
  --set-env-vars "GCP_PROJECT=data-engineering-hs-bkk,BQ_DATASET=rappler,BQ_TABLE=rappler_articles"
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

---

### ✅ Create BigQuery Dataset and Table (if needed)

```bash
bq mk --dataset --location=US data-engineering-hs-bkk:rappler

bq mk --table data-engineering-hs-bkk:rappler.rappler_articles \
  article_id:STRING,datetime:TIMESTAMP,title:STRING,link:STRING,categories:STRING,tags:STRING
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

## 🧪 Test the Full Pipeline

1. Upload a sample file:
```bash
gsutil cp rappler_articles_2025-04-01_15-30-00.json gs://rappler-hs-bkk
```

2. Watch logs:
```bash
gcloud run services logs read load-to-bigquery \
  --region us-central1 \
  --limit 50
```

---

## 📊 Query Data in BigQuery

```sql
SELECT * FROM `data-engineering-hs-bkk.rappler.rappler_articles`
ORDER BY datetime DESC
LIMIT 10;
```

---

## 🧼 Cleanup

```bash
gcloud eventarc triggers delete load-from-gcs --location=us
gcloud run services delete load-to-bigquery --region=us-central1
```

---

## 🙌 Author

**Gino Asuncion**  
ETL • Cloud • Automation  
[github.com/ginoasuncion](https://github.com/ginoasuncion)
