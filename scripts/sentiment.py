import logging
from typing import List, Dict, Any
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        logger.info(f"Loading sentiment analysis model: {model_name}")
        # Initialize Hugging Face pipeline with truncation enabled for long review texts
        self.pipe = pipeline(
            "sentiment-analysis",
            model=model_name,
            truncation=True,
            max_length=512,
            batch_size=64
        )

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Processes a list of review text strings and returns sentiment labels and confidence scores.
        Handles empty or missing strings gracefully.
        """
        # Clean null/empty values to prevent pipeline errors
        cleaned_texts = [text if text and text.strip() else "No review text provided." for text in texts]
        
        try:
            results = self.pipe(cleaned_texts)
            return [
                {
                    "sentiment_label": res["label"],  # e.g., 'POSITIVE' or 'NEGATIVE'
                    "sentiment_score": round(float(res["score"]), 4)  # Confidence score (e.g., 0.9854)
                }
                for res in results
            ]
        except Exception as e:
            logger.error(f"Error executing sentiment batch inference: {e}")
            # Fallback return on unexpected errors
            return [{"sentiment_label": "NEUTRAL", "sentiment_score": 0.0} for _ in texts]
        