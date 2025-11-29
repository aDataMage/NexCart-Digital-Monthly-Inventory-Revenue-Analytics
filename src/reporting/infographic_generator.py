"""
Infographic generator using Google Gemini for business report visuals.
Creates professional infographics for executive summary presentations.
"""
import logging
import time
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from config.settings import settings

logger = logging.getLogger(__name__)


class InfographicGenerator:
    """Generate infographics using Google's Gemini 3 Pro Image API."""

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3-pro-image-preview"

    def generate_infographic(
        self,
        topic: str,
        data_summary: str,
        style: str = "modern business infographic",
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate an infographic image for a specific topic.

        Args:
            topic: The main topic (e.g., "Sales Performance")
            data_summary: Key data points to visualize
            style: Visual style description
            output_path: Optional path to save the image

        Returns:
            Image bytes if successful, None otherwise
        """
        prompt = self._build_infographic_prompt(topic, data_summary, style)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio="16:9",
                        image_size="4K"
                    )
                )
            )

            # Extract image from response
            image_parts = [part for part in response.parts if part.inline_data]

            if image_parts:
                image = image_parts[0].as_image()

                if output_path:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    image.save(output_path)
                    logger.info(f"Infographic saved to {output_path}")

                # Return image bytes - read from saved file
                if output_path:
                    with open(output_path, 'rb') as f:
                        return f.read()
                return b'image_generated'

            logger.warning("No image returned from Gemini API")
            return None

        except Exception as e:
            logger.error(f"Error generating infographic for {topic}: {e}")
            return None

    def _build_infographic_prompt(self, topic: str, data_summary: str, visual_style: str = "Flat Vector", brand_hex_primary: str = "#0055FF", brand_hex_secondary: str = "#FFFFFF", font_style: str = "Sans-Serif") -> str:
        """
        Build a strictly formatted prompt for infographic generation that matches slide decks.

        Args:
            topic: The subject matter.
            data_summary: The data points to visualize.
            visual_style: The artistic style (e.g., 'Flat Vector', '3D Isometric', 'Line Art').
            brand_hex_primary: The main brand color code to ensure matching hues.
            brand_hex_secondary: The background or accent color.
            font_style: The specific font family used in the slides (e.g., 'Arial', 'Roboto').
        """
        return f"""Generate a high-fidelity presentation graphic. 

            Context:
            This image will be embedded in a corporate slide deck. It must match the surrounding slide formatting exactly.

            Subject: {topic}

            Visual Identity & Constraints (STRICT):
            - Style: {visual_style} (Must appear consistent with a professional slide deck)
            - Primary Color Palette: Use strictly {brand_hex_primary} for main elements.
            - Background: {brand_hex_secondary} (Must match slide background exactly).
            - Typography: Mimic {font_style} weighting and spacing.
            - Layout: 16:9 Aspect Ratio. Composition should be balanced to allow for slide headers.

            Data to Visualize:
            {data_summary}

            Negative Constraints (Do Not Include):
            - Do not use photographic or hyper-realistic styles (unless specified).
            - Do not use cluttered backgrounds.
            - Do not generate gibberish text; prefer symbolic representation of data where text isn't legible.

            Output Quality:
            - 4k resolution
            - Sharp edges
            - Vector-like clarity
            """

    def generate_all_infographics(self, insights: dict, report_data: dict, output_dir: str, delay: int = 15) -> dict:
        """
        Generate all infographics for a complete executive summary.

        Args:
            insights: LLM-generated insights dictionary
            report_data: Aggregated report data
            output_dir: Directory to save infographic images

        Returns:
            Dictionary mapping slide names to image paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        infographics = {}
        report_month = report_data.get('report_month', 'Monthly Report')

        # 1. Title/Cover infographic
        title_data = f"Report Period: {report_month}"
        title_path = output_path / "01_title_infographic.png"
        if self.generate_infographic(
            "Executive Summary Report Cover",
            title_data,
            "elegant corporate cover design with abstract data visualization elements",
            str(title_path)
        ):
            infographics['title'] = str(title_path)

        time.sleep(delay)

        # 2. Executive Summary infographic
        exec_summary = insights.get('executive_summary', '')
        sales_summary = report_data.get('sales_summary', {})
        exec_data = f"""
                Executive Overview:
                {exec_summary}

                Key Metrics:
                - Total Revenue: ${sales_summary.get('total_gross', 0):,.2f}
                - Total Orders: {sales_summary.get('total_orders', 0):,}
                - Average Order Value: ${sales_summary.get('avg_order_value', 0):.2f}
                """
        exec_path = output_path / "02_executive_summary.png"
        if self.generate_infographic(
            "Executive Summary Overview",
            exec_data,
            "dashboard-style infographic with KPI cards and trend indicators",
            str(exec_path)
        ):
            infographics['executive_summary'] = str(exec_path)

        time.sleep(delay)

        # 3. Sales & Channel Performance infographic
        sales_data = report_data.get('sales_summary', {})
        channels = sales_data.get('channels', [])
        channel_text = "\n".join([
            f"- {ch.get('channel_name', 'Unknown')}: ${ch.get('gross_revenue', 0):,.2f}"
            for ch in channels[:5]
        ])
        sales_info = f"""
Sales Performance:
{insights.get('sales_insights', '')}

Channel Revenue Breakdown:
{channel_text}

Total Gross: ${sales_data.get('total_gross', 0):,.2f}
Total Net: ${sales_data.get('total_net', 0):,.2f}
"""
        sales_path = output_path / "03_sales_performance.png"
        if self.generate_infographic(
            "Sales & Channel Performance",
            sales_info,
            "bar chart and pie chart infographic showing revenue distribution",
            str(sales_path)
        ):
            infographics['sales'] = str(sales_path)

        time.sleep(delay)

        # 4. Product Performance infographic
        product_data = report_data.get('product_summary', {})
        top_skus = product_data.get('top_skus', [])
        sku_text = "\n".join([
            f"- {sku.get('sku', 'Unknown')}: {sku.get('total_quantity_sold', 0)} units"
            for sku in top_skus[:5]
        ])
        product_info = f"""
Product Insights:
{insights.get('product_insights', '')}

Top Products:
{sku_text}

Average Order Value: ${product_data.get('aov', 0):.2f}
"""
        product_path = output_path / "04_product_performance.png"
        if self.generate_infographic(
            "Product & Inventory Performance",
            product_info,
            "product ranking infographic with icons and performance bars",
            str(product_path)
        ):
            infographics['products'] = str(product_path)

        time.sleep(delay)

        # 5. Customer Demographics infographic
        customer_data = report_data.get('customer_summary', {})
        top_states = customer_data.get('top_states', [])
        state_text = "\n".join([
            f"- {st.get('state', 'Unknown')}: ${st.get('total_sales', 0):,.2f}"
            for st in top_states[:5]
        ])
        customer_info = f"""
Customer Insights:
{insights.get('customer_insights', '')}

Top Markets:
{state_text}

New Customers: {customer_data.get('new_customers', 0)}
Avg Purchase Latency: {customer_data.get('avg_latency', 0):.1f} days
"""
        customer_path = output_path / "05_customer_demographics.png"
        if self.generate_infographic(
            "Customer Demographics & Behavior",
            customer_info,
            "geographic map infographic with customer distribution",
            str(customer_path)
        ):
            infographics['customers'] = str(customer_path)

        time.sleep(delay)

        # 6. Financial Analysis infographic
        payment_data = report_data.get('payment_summary', {})
        payment_methods = payment_data.get('payment_methods', [])
        payment_text = "\n".join([
            f"- {pm.get('payment_method', 'Unknown')}: ${pm.get('total_amount', 0):,.2f}"
            for pm in payment_methods[:5]
        ])
        financial_info = f"""
Financial Insights:
{insights.get('financial_insights', '')}

Payment Methods:
{payment_text}

Total Transactions: ${payment_data.get('total_amount', 0):,.2f}
Unsettled Orders: {payment_data.get('unsettled_count', 0)}
"""
        financial_path = output_path / "06_financial_analysis.png"
        if self.generate_infographic(
            "Financial & Payment Analysis",
            financial_info,
            "financial dashboard infographic with payment method breakdown",
            str(financial_path)
        ):
            infographics['financial'] = str(financial_path)

        time.sleep(delay)

        # 7. Recommendations infographic
        recommendations = insights.get('recommendations', [])
        rec_text = "\n".join(
            [f"{i+1}. {rec}" for i, rec in enumerate(recommendations[:5])])
        rec_info = f"""
Strategic Recommendations:
{rec_text}
"""
        rec_path = output_path / "07_recommendations.png"
        if self.generate_infographic(
            "Strategic Recommendations",
            rec_info,
            "action-oriented infographic with numbered steps and icons",
            str(rec_path)
        ):
            infographics['recommendations'] = str(rec_path)

        time.sleep(delay)

        # 8. Risk Alerts infographic
        risks = insights.get('risk_alerts', [])
        risk_text = "\n".join([f"⚠ {risk}" for risk in risks[:5]])
        risk_info = f"""
Risk Alerts & Action Items:
{risk_text}
"""
        risk_path = output_path / "08_risk_alerts.png"
        if self.generate_infographic(
            "Risk Alerts & Action Items",
            risk_info,
            "warning-style infographic with alert icons and priority indicators",
            str(risk_path)
        ):
            infographics['risks'] = str(risk_path)

        logger.info(
            f"Generated {len(infographics)} infographics in {output_dir}")
        return infographics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    generator = InfographicGenerator()

    print("Testing single infographic generation...")
    result = generator.generate_infographic(
        "Sales Performance Test",
        "Total Revenue: $224,674\nTop Channel: Amazon\nOrders: 350",
        output_path="reports/test_infographic.png"
    )

    if result:
        print("✓ Infographic generated successfully!")
    else:
        print("✗ Failed to generate infographic")
