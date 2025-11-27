import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from src.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llm():
    logger.info("Testing LLM Credentials...")
    client = LLMClient()
    
    kpi_data = {
        "channels": [
            {"channel_id": "TEST_CH", "total_revenue": 12345.67, "order_count": 100, "avg_order_value": 123.45}
        ]
    }
    
    try:
        insights = client.generate_insights(kpi_data)
        logger.info("LLM Response Received:")
        logger.info(insights)
        
        if "TEST_CH" in insights or "12,345.67" in insights or "revenue" in insights.lower():
             logger.info("LLM test PASSED (Content looks relevant).")
        else:
             logger.warning("LLM test completed but content might be generic/mock.")
             
    except Exception as e:
        logger.error(f"LLM test FAILED: {e}")

if __name__ == "__main__":
    test_llm()
