import os
import requests
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ecommerce-sentiment-platform")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def fetch_negative_anomalies() -> list[dict]:
    """Queries BigQuery gold layer for products flagged as negative sentiment anomalies."""
    client = bigquery.Client(project=GCP_PROJECT_ID)
    
    query = f"""
        SELECT 
            parent_asin,
            baseline_review_count,
            recent_review_count,
            baseline_positive_ratio,
            recent_positive_ratio,
            sentiment_shift_index
        FROM `{GCP_PROJECT_ID}.analytics.gold_sentiment_shifts`
        WHERE is_negative_anomaly = TRUE
        ORDER BY sentiment_shift_index ASC
        LIMIT 10
    """
    
    print("Querying BigQuery for gold sentiment anomalies...")
    query_job = client.query(query)
    results = [dict(row) for row in query_job.result()]
    return results


def send_discord_alert(anomalies: list[dict]):
    """Formats and posts anomaly alerts to Discord via Webhook."""
    if not DISCORD_WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL not set in environment variables.")
        return

    if not anomalies:
        print("No negative sentiment anomalies detected. Skipping Discord alert.")
        return

    embeds = []
    # Discord permits up to 10 embeds per webhook payload; we limit to top 5 for readability
    for item in anomalies[:5]:
        drop_pct = abs(round(item["sentiment_shift_index"] * 100, 1))
        
        embed = {
            "title": f"🚨 Sentiment Anomaly Detected: ASIN {item['parent_asin']}",
            "color": 15158332,  # Crimson Red
            "fields": [
                {
                    "name": "Sentiment Shift Drop",
                    "value": f"**-{drop_pct}%**",
                    "inline": True
                },
                {
                    "name": "Baseline Positivity Ratio",
                    "value": f"{round(item['baseline_positive_ratio'] * 100, 1)}% ({item['baseline_review_count']} reviews)",
                    "inline": True
                },
                {
                    "name": "Recent Positivity Ratio",
                    "value": f"{round(item['recent_positive_ratio'] * 100, 1)}% ({item['recent_review_count']} reviews)",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Ecommerce Sentiment Platform • Automated Alert"
            }
        }
        embeds.append(embed)

    payload = {
        "content": f"⚠️ **Attention Required:** Found `{len(anomalies)}` product(s) with severe negative review spikes in the recent delta.",
        "embeds": embeds
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    
    if response.status_code in (200, 204):
        print(f"Successfully posted {len(embeds)} anomaly alerts to Discord!")
    else:
        print(f"Failed to post to Discord. Status: {response.status_code}, Response: {response.text}")


def main():
    anomalies = fetch_negative_anomalies()
    print(f"Retrieved {len(anomalies)} anomaly records.")
    send_discord_alert(anomalies)


if __name__ == "__main__":
    main()
    