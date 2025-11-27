import openai
from config.settings import settings
import logging
import json

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        """Initialize LLM client with API key from settings."""
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL if hasattr(settings, 'LLM_MODEL') else "gpt-4"
        
        # Detect provider based on API key format
        if self.api_key and self.api_key.startswith('AIza'):
            self.provider = 'gemini'
        elif self.api_key and self.api_key.startswith('sk-'):
            self.provider = 'openai'
        else:
            self.provider = None
            logger.warning("No valid LLM API key found, will use fallback insights")

    def generate_insights(self, report_data: dict) -> dict:
        """
        Generate executive insights from aggregated report data.
        
        Args:
            report_data: Dictionary containing:
                - sales_summary: Sales & channel performance metrics
                - product_summary: Product performance metrics
                - inventory_summary: Inventory health metrics
                - customer_summary: Customer demographics metrics
                - payment_summary: Payment & financial metrics
                - report_month: Month being analyzed (e.g., "October 2025")
        
        Returns:
            Dictionary with:
                - executive_summary: High-level overview (2-3 sentences)
                - sales_insights: Sales & channel findings
                - product_insights: Product & inventory findings
                - customer_insights: Customer behavior findings
                - financial_insights: Payment & financial findings
                - recommendations: List of actionable recommendations
                - risk_alerts: List of potential risks/issues
        """
        try:
            # Build comprehensive prompt
            prompt = self._build_analysis_prompt(report_data)
            
            logger.info("Sending data to LLM for insight generation...")
            
            if self.provider == 'gemini':
                insights_text = self._call_gemini(prompt)
            elif self.provider == 'openai':
                insights_text = self._call_openai(prompt)
            else:
                logger.warning("No LLM provider configured, using fallback")
                return self._get_fallback_insights(report_data)
            
            logger.info("Received insights from LLM")
            
            # Parse the structured response
            insights = self._parse_insights(insights_text)
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            # Return fallback insights
            return self._get_fallback_insights(report_data)

    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API."""
        import requests
        import json
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {'Content-Type': 'application/json'}
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API (new version 1.0+)."""
        from openai import OpenAI
        
        client = OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert business analyst specializing in e-commerce and inventory management. Provide actionable, data-driven insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content

    def _build_analysis_prompt(self, report_data: dict) -> str:
        """Build a comprehensive prompt for the LLM."""
        month = report_data.get('report_month', 'this month')
        
        prompt = f"""Analyze the following business performance data for {month} and provide strategic insights.

## SALES & CHANNEL PERFORMANCE
{self._format_sales_data(report_data.get('sales_summary', {}))}

## PRODUCT PERFORMANCE
{self._format_product_data(report_data.get('product_summary', {}))}

## INVENTORY HEALTH
{self._format_inventory_data(report_data.get('inventory_summary', {}))}

## CUSTOMER DEMOGRAPHICS
{self._format_customer_data(report_data.get('customer_summary', {}))}

## FINANCIAL & PAYMENTS
{self._format_financial_data(report_data.get('payment_summary', {}))}

---

Provide your analysis in the following structured format:

**EXECUTIVE SUMMARY:**
[2-3 sentences summarizing overall business health and key takeaways]

**SALES INSIGHTS:**
[Analysis of sales trends, channel performance, commission impact]

**PRODUCT INSIGHTS:**
[Analysis of product performance, inventory turnover signals, merchandising opportunities]

**CUSTOMER INSIGHTS:**
[Analysis of customer behavior, geographic opportunities, acquisition effectiveness]

**FINANCIAL INSIGHTS:**
[Analysis of payment trends, cash flow health, financial risks]

**RECOMMENDATIONS:**
1. [Specific actionable recommendation]
2. [Specific actionable recommendation]
3. [Specific actionable recommendation]
4. [Specific actionable recommendation]
5. [Specific actionable recommendation]

**RISK ALERTS:**
- [Potential risk or issue requiring attention]
- [Potential risk or issue requiring attention]
"""
        return prompt

    def _format_sales_data(self, sales_data: dict) -> str:
        """Format sales data for the prompt."""
        if not sales_data:
            return "No sales data available."
        
        lines = [
            f"- Total Gross Revenue: ${sales_data.get('total_gross', 0):,.2f}",
            f"- Total Net Revenue: ${sales_data.get('total_net', 0):,.2f}",
            f"- Total Orders: {sales_data.get('total_orders', 0):,}",
            f"- Average Order Value: ${sales_data.get('avg_order_value', 0):.2f}",
        ]
        
        if 'channels' in sales_data:
            lines.append("\nChannel Breakdown:")
            for ch in sales_data['channels'][:5]:  # Top 5 channels
                lines.append(f"  - {ch.get('channel_name', 'Unknown')}: ${ch.get('gross_revenue', 0):,.2f} gross, ${ch.get('net_revenue', 0):,.2f} net ({ch.get('order_count', 0)} orders)")
        
        return "\n".join(lines)

    def _format_product_data(self, product_data: dict) -> str:
        """Format product data for the prompt."""
        if not product_data:
            return "No product data available."
        
        lines = [
            f"- Average Order Value: ${product_data.get('aov', 0):.2f}",
            f"- Total Revenue: ${product_data.get('total_revenue', 0):,.2f}",
        ]
        
        if 'top_skus' in product_data:
            lines.append("\nTop 5 Products by Quantity:")
            for prod in product_data['top_skus'][:5]:
                lines.append(f"  - {prod.get('sku', 'Unknown')}: {prod.get('total_quantity_sold', 0)} units, ${prod.get('total_revenue', 0):,.2f} revenue")
        
        return "\n".join(lines)

    def _format_inventory_data(self, inventory_data: dict) -> str:
        """Format inventory data for the prompt."""
        if not inventory_data:
            return "No inventory data available."
        
        lines = [
            f"- Low Stock Items: {inventory_data.get('low_stock_count', 0)} SKUs below threshold",
            f"- Snapshot Date: {inventory_data.get('snapshot_date', 'Unknown')}",
        ]
        
        if 'warehouse_summary' in inventory_data:
            lines.append("\nWarehouse Distribution:")
            for wh in inventory_data['warehouse_summary']:
                lines.append(f"  - {wh.get('warehouse_id', 'Unknown')}: {wh.get('total_units', 0):,} units, ${wh.get('inventory_value', 0):,.2f} value")
        
        return "\n".join(lines)

    def _format_customer_data(self, customer_data: dict) -> str:
        """Format customer data for the prompt."""
        if not customer_data:
            return "No customer data available."
        
        lines = [
            f"- Average Purchase Latency: {customer_data.get('avg_latency', 0):.1f} days",
            f"- New Customers: {customer_data.get('new_customers', 0)}",
        ]
        
        if 'top_states' in customer_data:
            lines.append("\nTop 5 States by Sales:")
            for state in customer_data['top_states'][:5]:
                lines.append(f"  - {state.get('state', 'Unknown')}: ${state.get('total_sales', 0):,.2f}, {state.get('customer_count', 0)} customers")
        
        return "\n".join(lines)

    def _format_financial_data(self, financial_data: dict) -> str:
        """Format financial data for the prompt."""
        if not financial_data:
            return "No financial data available."
        
        lines = [
            f"- Total Transaction Amount: ${financial_data.get('total_amount', 0):,.2f}",
            f"- Unsettled Orders: {financial_data.get('unsettled_count', 0)}",
        ]
        
        if 'payment_methods' in financial_data:
            lines.append("\nPayment Method Distribution:")
            for pm in financial_data['payment_methods']:
                lines.append(f"  - {pm.get('payment_method', 'Unknown')}: ${pm.get('total_amount', 0):,.2f} ({pm.get('transaction_count', 0)} transactions)")
        
        return "\n".join(lines)

    def _parse_insights(self, insights_text: str) -> dict:
        """Parse the LLM response into structured sections."""
        sections = {
            'executive_summary': '',
            'sales_insights': '',
            'product_insights': '',
            'customer_insights': '',
            'financial_insights': '',
            'recommendations': [],
            'risk_alerts': []
        }
        
        # Simple parsing based on section headers
        lines = insights_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if '**EXECUTIVE SUMMARY:**' in line or 'EXECUTIVE SUMMARY:' in line:
                current_section = 'executive_summary'
            elif '**SALES INSIGHTS:**' in line or 'SALES INSIGHTS:' in line:
                current_section = 'sales_insights'
            elif '**PRODUCT INSIGHTS:**' in line or 'PRODUCT INSIGHTS:' in line:
                current_section = 'product_insights'
            elif '**CUSTOMER INSIGHTS:**' in line or 'CUSTOMER INSIGHTS:' in line:
                current_section = 'customer_insights'
            elif '**FINANCIAL INSIGHTS:**' in line or 'FINANCIAL INSIGHTS:' in line:
                current_section = 'financial_insights'
            elif '**RECOMMENDATIONS:**' in line or 'RECOMMENDATIONS:' in line:
                current_section = 'recommendations'
            elif '**RISK ALERTS:**' in line or 'RISK ALERTS:' in line:
                current_section = 'risk_alerts'
            elif line and current_section:
                # Add content to current section
                if current_section in ['recommendations', 'risk_alerts']:
                    # These are lists
                    if line.startswith(('-', '•', '*')) or line[0].isdigit():
                        clean_line = line.lstrip('-•*0123456789. ').strip()
                        if clean_line:
                            sections[current_section].append(clean_line)
                else:
                    # These are text blocks
                    if line and not line.startswith('**'):
                        sections[current_section] += line + ' '
        
        # Clean up text blocks
        for key in ['executive_summary', 'sales_insights', 'product_insights', 'customer_insights', 'financial_insights']:
            sections[key] = sections[key].strip()
        
        return sections

    def _get_fallback_insights(self, report_data: dict) -> dict:
        """Return basic fallback insights if LLM fails."""
        return {
            'executive_summary': f"Business performance data for {report_data.get('report_month', 'this period')} has been compiled. Please review the detailed analytics reports for comprehensive insights.",
            'sales_insights': "Sales data collected across all channels. Review the Sales & Channel Performance report for detailed metrics.",
            'product_insights': "Product performance tracked. See Product Performance report for top sellers and revenue drivers.",
            'customer_insights': "Customer demographic data analyzed. Refer to Customer Demographics report for geographic and behavioral insights.",
            'financial_insights': "Financial transactions processed. Check Payment Analysis report for cash flow and reconciliation details.",
            'recommendations': [
                "Review detailed SQL analytics reports for specific action items",
                "Monitor low-stock inventory items for restocking",
                "Analyze top-performing channels for expansion opportunities"
            ],
            'risk_alerts': [
                "Manual review recommended due to LLM service unavailability"
            ]
        }


if __name__ == "__main__":
    # Test the LLM client
    logging.basicConfig(level=logging.INFO)
    
    test_data = {
        'report_month': 'October 2025',
        'sales_summary': {
            'total_gross': 224674.36,
            'total_net': 205000.00,
            'total_orders': 350,
            'avg_order_value': 641.93,
            'channels': [
                {'channel_name': 'Amazon', 'gross_revenue': 60683.79, 'net_revenue': 54615.41, 'order_count': 90},
                {'channel_name': 'Shopify', 'gross_revenue': 57638.49, 'net_revenue': 55831.42, 'order_count': 92}
            ]
        }
    }
    
    client = LLMClient()
    insights = client.generate_insights(test_data)
    
    print("\n=== INSIGHTS ===")
    print(json.dumps(insights, indent=2))
