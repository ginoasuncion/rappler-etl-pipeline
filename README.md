
# ETL Pipeline for Extracting and Loading News Data

This project is an **ETL (Extract, Transform, Load)** pipeline for extracting the latest news articles from [Rappler](https://www.rappler.com/latest/) and loading the data into **Google Cloud Storage (GCS)** and **BigQuery**. The pipeline is composed of two services:

1. **Extract Service** (`extract_to_gcs`): This service scrapes the latest news from Rappler's website and stores the data in Google Cloud Storage.
2. **Load Service** (`load_to_bigquery`): This service reads the data from GCS and loads it into Google BigQuery for analysis.

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Deployment](#deployment)
  - [Deploy to Cloud Run](#deploy-to-cloud-run)
  - [Deploy Cloud Scheduler Jobs](#deploy-cloud-scheduler-jobs)
- [Usage](#usage)
- [License](#license)

---

## Overview

This **ETL pipeline** performs the following tasks:

1. **Extract**: Scrapes the latest news articles from [Rappler's Latest News](https://www.rappler.com/latest/), extracts the content, and saves it as a JSON file in Google Cloud Storage.
2. **Load**: Reads the data from GCS, transforms it if necessary, and loads it into Google BigQuery for further analysis and querying.

### Architecture

- **Cloud Run**: Used for both the **Extract** and **Load** services. Each service is deployed as a Cloud Run function.
- **Cloud Scheduler**: Automates the execution of the Extract and Load jobs on a scheduled basis (e.g., every 4 hours for extraction and 4.5 hours for loading).
- **BigQuery**: Stores the extracted and transformed data for easy querying and analysis.

---

## Requirements

To run this ETL pipeline, you need the following:

- **Google Cloud account** with the necessary permissions to deploy and use Cloud Run, Cloud Storage, and BigQuery.
- **Google Cloud SDK** installed on your machine.
- **Python 3.8+** for the local environment.
- **Docker** (for containerization of the Cloud Run services).
- **GitHub account** (for repository management and version control).

---

## Project Structure

Here is the directory structure of the project:

```
etl-pipeline/
├── README.md              # Documentation for the ETL pipeline
├── extract_to_gcs/        # Extract service - scrapes news and stores in GCS
├── load_to_bigquery/      # Load service - loads data into BigQuery
├── Dockerfile             # Docker configuration for containerizing the services
├── requirements.txt       # Python dependencies for the ETL services
├── .gitignore             # Files and directories to ignore in Git
```

---

## Setup and Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/etl-pipeline.git
   cd etl-pipeline
   ```

2. **Install dependencies**:

   Make sure you have the required dependencies for the project:

   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Google Cloud SDK**:

   If you haven’t already, install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) and authenticate with your Google Cloud account:

   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

4. **Configure Google Cloud Services**:

   Enable the following Google Cloud APIs for your project:
   - Cloud Run
   - Cloud Scheduler
   - Cloud Storage
   - BigQuery

---

## Deployment

### Deploy to Cloud Run

1. **Deploy the Extract Service**:

   Navigate to the `extract_to_gcs` folder and deploy it to Cloud Run:

   ```bash
   gcloud run deploy extract-to-gcs      --source extract_to_gcs      --region us-central1      --allow-unauthenticated      --service-account your-service-account@your-project.iam.gserviceaccount.com
   ```

2. **Deploy the Load Service**:

   Navigate to the `load_to_bigquery` folder and deploy it to Cloud Run:

   ```bash
   gcloud run deploy load-to-bigquery      --source load_to_bigquery      --region us-central1      --allow-unauthenticated      --service-account your-service-account@your-project.iam.gserviceaccount.com
   ```

### Deploy Cloud Scheduler Jobs

Cloud Scheduler will automatically trigger the **Extract** and **Load** functions at the specified intervals.

1. **Create the Extract Job (every 4 hours)**:

   ```bash
   gcloud scheduler jobs create http extract-job      --schedule="0 */4 * * *"      --uri="https://extract-to-gcs-137287523276.us-central1.run.app"      --http-method=GET      --time-zone="Asia/Kolkata"      --location="us-central1"
   ```

2. **Create the Load Job (every 4.5 hours)**:

   ```bash
   gcloud scheduler jobs create http load-job      --schedule="30 */4 * * *"      --uri="https://load-to-bigquery-137287523276.us-central1.run.app"      --http-method=POST      --headers="Content-Type=application/json"      --message-body="{}"      --time-zone="Asia/Kolkata"      --location="us-central1"
   ```

---

## Usage

Once deployed, the **Extract** function will run automatically every 4 hours, pulling the latest news from [Rappler](https://www.rappler.com/latest/) and storing the data in Google Cloud Storage. The **Load** function will run every 4.5 hours, loading the data from Cloud Storage into BigQuery for further analysis.

To manually trigger the functions:

- **Extract Function** (GET request):
  ```bash
  curl https://extract-to-gcs-137287523276.us-central1.run.app
  ```

- **Load Function** (POST request with empty JSON body):
  ```bash
  curl -X POST https://load-to-bigquery-137287523276.us-central1.run.app/     -H "Content-Type: application/json"     -d '{}'
  ```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Conclusion

This ETL pipeline extracts the latest news articles from Rappler and loads them into BigQuery for analysis. It uses **Google Cloud Run** for deployment, **Cloud Scheduler** for automation, and **Cloud Storage** and **BigQuery** for data storage and processing.

By following the instructions in this README, you can set up, deploy, and schedule the ETL pipeline in your Google Cloud environment.

---

