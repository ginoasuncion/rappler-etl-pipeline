import os
import json
from google.cloud import storage
import requests
from datetime import datetime
from flask import Flask, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def index():
    """
    Scrapes the latest articles from Rappler, uploads them to GCS, and triggers
    the BigQuery load function in Cloud Run.
    """
    # Scrape articles from Rappler
    articles = scrape_rappler_latest()
    
    # Generate filename using timestamp
    now = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"rappler_articles_{now}.json"
    
    # Upload to GCS
    upload_to_gcs(os.environ["GCS_BUCKET"], articles, filename)
    
    # Return response
    return jsonify({"message": f"Uploaded {filename} to {os.environ['GCS_BUCKET']} and triggered load-to-bigquery."})

def scrape_rappler_latest(page=1):
    """
    Scrapes the latest articles from Rappler's website.
    """
    url = f"https://www.rappler.com/latest/page/{page}/" if page > 1 else "https://www.rappler.com/latest/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    for article in soup.find_all("article"):
        article_id = article.get("id", "")
        time_tag = article.find("time")
        datetime_str = time_tag.get("datetime") if time_tag else ""
        if not datetime_str:
            continue
        title_tag = article.find("h3") or article.find("h2")
        link_tag = title_tag.find("a") if title_tag else None
        title = title_tag.get_text(strip=True) if title_tag else ""
        link = link_tag["href"] if link_tag else ""
        classes = article.get("class", [])
        categories = [cls.replace("category-", "") for cls in classes if cls.startswith("category-")]
        tags = [cls.replace("tag-", "") for cls in classes if cls.startswith("tag-")]

        articles.append({
            "article_id": article_id,
            "datetime": datetime_str,
            "title": title,
            "link": link,
            "categories": categories,
            "tags": tags
        })

    return articles

def upload_to_gcs(bucket_name, data, filename):
    """
    Uploads the scraped article data to Google Cloud Storage (GCS).
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(json.dumps(data), content_type="application/json")

if __name__ == "__main__":
    # Use Cloud Run's port (8080) and disable Flask's debug mode for production
    app.run(debug=False, host='0.0.0.0', port=8080)
