import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.db_client import DBClient
from src.llm_client import LLMClient
from src.reporting import sql_reports, chart_generator
from src.reporting.executive_summary_generator import ExecutiveSummaryGenerator
import logging

logger = logging.getLogger(__name__)


class ReportBuilder:
    def __init__(self, report_month: str = None):
        """
        Initialize report builder.
        
        Args:
            report_month: Month to report on in YYYY-MM format. 
                         Defaults to previous month if not specified.
        """
        self.db_client = DBClient()
        self.template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        
        # Determine reporting period
        if report_month:
            self.report_month = datetime.strptime(report_month, '%Y-%m')
        else:
            # Default to previous month
            today = datetime.now()
            self.report_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        
        # Calculate date range
        self.start_date = self.report_month.strftime('%Y-%m-%d')
        next_month = self.report_month + relativedelta(months=1)
        self.end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Setup output directory
        month_folder = self.report_month.strftime('%Y-%m')
        self.output_dir = Path('reports') / month_folder
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Report builder initialized for {month_folder}")
        logger.info(f"Report period: {self.start_date} to {self.end_date}")
        logger.info(f"Output directory: {self.output_dir}")

    def build_report(self):
        """Generate all reports for the specified month."""
        logger.info("Building monthly reports...")
        
        # Store report data for LLM analysis
        self.aggregated_data = {
            'report_month': self.report_month.strftime('%B %Y'),
            'sales_summary': {},
            'product_summary': {},
            'inventory_summary': {},
            'customer_summary': {},
            'payment_summary': {}
        }
        
        try:
            # Generate all 5 reports
            self._build_sales_channel_report()
            self._build_product_performance_report()
            self._build_inventory_health_report()
            self._build_customer_demographics_report()
            self._build_payment_analysis_report()
            
            # Create index page
            self._build_index_page()
            
            # Generate LLM-based executive summary
            self._build_executive_summary()
            
            logger.info("Report generation complete.")
            logger.info(f"Reports saved to {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error building reports: {e}")
            raise

    def _build_sales_channel_report(self):
        """Generate Sales & Channel Performance Report."""
        logger.info("Generating Sales & Channel Performance Report...")
        
        # Get data
        data = sql_reports.get_sales_channel_performance(
            self.db_client, self.start_date, self.end_date
        )
        
        if data.empty:
            logger.warning("No sales channel data found for this period")
            return
        
        # Generate chart
        chart_path = self.output_dir / 'sales_channel_chart.png'
        chart_generator.create_bar_chart(
            data=data,
            x_col='channel_name',
            y_cols=['gross_revenue', 'net_revenue'],
            title=f'Gross vs Net Revenue by Channel ({self.report_month.strftime("%B %Y")})',
            output_path=str(chart_path),
            labels=['Gross Revenue', 'Net Revenue']
        )
        
        # Collect data for LLM
        self.aggregated_data['sales_summary'] = {
            'total_gross': data['gross_revenue'].sum(),
            'total_net': data['net_revenue'].sum(),
            'total_orders': data['order_count'].sum(),
            'avg_order_value': data['gross_revenue'].sum() / data['order_count'].sum(),
            'channels': data.head(5).to_dict(orient='records')
        }
        
        # Render report
        context = {
            'title': 'Sales & Channel Performance Report',
            'report_month': self.report_month.strftime('%B %Y'),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'data': data.to_dict(orient='records'),
            'chart_filename': chart_path.name,
            'total_gross': data['gross_revenue'].sum(),
            'total_net': data['net_revenue'].sum(),
            'total_orders': data['order_count'].sum()
        }
        
        self._render_template('sales_channel_report.j2', context, 'sales_channel_report.html')

    def _build_product_performance_report(self):
        """Generate Product Performance & Merchandising Report."""
        logger.info("Generating Product Performance Report...")
        
        # Get data
        data = sql_reports.get_product_performance(
            self.db_client, self.start_date, self.end_date
        )
        
        if data['top_skus'].empty:
            logger.warning("No product data found for this period")
            return
        
        # Generate Pareto chart for revenue drivers
        chart_path = self.output_dir / 'product_pareto_chart.png'
        chart_generator.create_pareto_chart(
            data=data['revenue_drivers'],
            category_col='sku',
            value_col='total_revenue',
            title=f'Top Revenue-Generating Products ({self.report_month.strftime("%B %Y")})',
            output_path=str(chart_path),
            top_n=20
        )
        
        # Render report
        context = {
            'title': 'Product Performance & Merchandising Report',
            'report_month': self.report_month.strftime('%B %Y'),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'top_skus': data['top_skus'].head(15).to_dict(orient='records'),
            'revenue_drivers': data['revenue_drivers'].head(15).to_dict(orient='records'),
            'aov_data': data['aov'].to_dict(orient='records')[0],
            'chart_filename': chart_path.name
        }
        
        # Collect data for LLM
        self.aggregated_data['product_summary'] = {
            'aov': data['aov'].to_dict(orient='records')[0]['avg_order_value'],
            'total_revenue': data['aov'].to_dict(orient='records')[0]['total_revenue'],
            'top_skus': data['top_skus'].head(5).to_dict(orient='records')
        }
        
        self._render_template('product_performance_report.j2', context, 'product_performance_report.html')

    def _build_inventory_health_report(self):
        """Generate Inventory Distribution & Health Report."""
        logger.info("Generating Inventory Health Report...")
        
        # Get data
        data = sql_reports.get_inventory_health(self.db_client)
        
        if data['warehouse_distribution'].empty:
            logger.warning("No inventory data found")
            return
        
        # Generate horizontal bar chart for warehouse distribution
        chart_path = self.output_dir / 'inventory_warehouse_chart.png'
        chart_generator.create_horizontal_bar(
            data=data['warehouse_distribution'],
            category_col='warehouse_id',
            value_col='total_units',
            title=f'Inventory Distribution by Warehouse (as of {data["snapshot_date"]})',
            output_path=str(chart_path)
        )
        
        # Render report
        context = {
            'title': 'Inventory Distribution & Health Report',
            'report_month': self.report_month.strftime('%B %Y'),
            'snapshot_date': data['snapshot_date'],
            'warehouse_data': data['warehouse_distribution'].to_dict(orient='records'),
            'low_stock_items': data['low_stock_alerts'].head(20).to_dict(orient='records'),
            'inventory_value': data['inventory_value'].to_dict(orient='records'),
            'chart_filename': chart_path.name,
            'total_low_stock': len(data['low_stock_alerts'])
        }
        
        self._render_template('inventory_health_report.j2', context, 'inventory_health_report.html')

    def _build_customer_demographics_report(self):
        """Generate Customer Demographics & Behavior Report."""
        logger.info("Generating Customer Demographics Report...")
        
        # Get data
        data = sql_reports.get_customer_demographics(
            self.db_client, self.start_date, self.end_date
        )
        
        if data['geographic_distribution'].empty:
            logger.warning("No customer data found for this period")
            return
        
        # Generate chart for top states
        chart_path = self.output_dir / 'customer_geo_chart.png'
        chart_generator.create_horizontal_bar(
            data=data['geographic_distribution'].head(15),
            category_col='state',
            value_col='total_sales',
            title=f'Top States by Sales Volume ({self.report_month.strftime("%B %Y")})',
            output_path=str(chart_path),
            top_n=15
        )
        
        # Acquisition trend chart
        if not data['new_customers'].empty:
            acquisition_chart = self.output_dir / 'customer_acquisition_chart.png'
            chart_generator.create_line_chart(
                data=data['new_customers'],
                x_col='signup_month',
                y_col='new_customers',
                title='New Customer Acquisition Trend',
                output_path=str(acquisition_chart),
                xlabel='Month',
                ylabel='New Customers'
            )
        else:
            acquisition_chart = None
        
        # Calculate average purchase latency
        avg_latency = data['purchase_latency']['days_to_first_purchase'].mean() if not data['purchase_latency'].empty else 0
        
        # Render report
        context = {
            'title': 'Customer Demographics & Behavior Report',
            'report_month': self.report_month.strftime('%B %Y'),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'geo_data': data['geographic_distribution'].head(20).to_dict(orient='records'),
            'new_customers': data['new_customers'].to_dict(orient='records'),
            'avg_purchase_latency': round(avg_latency, 1),
            'chart_filename': chart_path.name,
            'acquisition_chart': acquisition_chart.name if acquisition_chart else None
        }
        
        self._render_template('customer_demographics_report.j2', context, 'customer_demographics_report.html')

    def _build_payment_analysis_report(self):
        """Generate Financial Reconciliation & Payment Analysis Report."""
        logger.info("Generating Payment Analysis Report...")
        
        # Get data
        data = sql_reports.get_payment_analysis(
            self.db_client, self.start_date, self.end_date
        )
        
        if data['payment_methods'].empty:
            logger.warning("No payment data found for this period")
            return
        
        # Generate pie chart for payment methods
        chart_path = self.output_dir / 'payment_methods_chart.png'
        chart_generator.create_pie_chart(
            data=data['payment_methods'],
            category_col='payment_method',
            value_col='total_amount',
            title=f'Payment Method Distribution ({self.report_month.strftime("%B %Y")})',
            output_path=str(chart_path)
        )
        
        # Daily cashflow chart
        if not data['daily_cashflow'].empty:
            cashflow_chart = self.output_dir / 'daily_cashflow_chart.png'
            chart_generator.create_line_chart(
                data=data['daily_cashflow'],
                x_col='transaction_date',
                y_col='daily_total',
                title=f'Daily Cash Flow ({self.report_month.strftime("%B %Y")})',
                output_path=str(cashflow_chart),
                xlabel='Date',
                ylabel='Amount ($)'
            )
        else:
            cashflow_chart = None
        
        # Render report
        context = {
            'title': 'Financial Reconciliation & Payment Analysis',
            'report_month': self.report_month.strftime('%B %Y'),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'payment_methods': data['payment_methods'].to_dict(orient='records'),
            'unsettled_orders': data['unsettled_orders'].head(50).to_dict(orient='records'),
            'chart_filename': chart_path.name,
            'cashflow_chart': cashflow_chart.name if cashflow_chart else None,
            'total_unsettled': len(data['unsettled_orders'])
        }
        
        self._render_template('payment_analysis_report.j2', context, 'payment_analysis_report.html')

    def _build_index_page(self):
        """Generate index page linking all reports."""
        logger.info("Generating index page...")
        
        context = {
            'title': 'Monthly Analytics Dashboard',
            'report_month': self.report_month.strftime('%B %Y'),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'reports': [
                {'filename': 'sales_channel_report.html', 'title': 'Sales & Channel Performance', 
                 'description': 'Revenue analysis across sales channels with gross vs net comparisons'},
                {'filename': 'product_performance_report.html', 'title': 'Product Performance', 
                 'description': 'Top-selling products, revenue drivers, and merchandising insights'},
                {'filename': 'inventory_health_report.html', 'title': 'Inventory Health', 
                 'description': 'Warehouse distribution, low stock alerts, and inventory valuation'},
                {'filename': 'customer_demographics_report.html', 'title': 'Customer Demographics', 
                 'description': 'Geographic distribution, acquisition trends, and behavior analysis'},
                {'filename': 'payment_analysis_report.html', 'title': 'Payment Analysis', 
                 'description': 'Payment method distribution, unsettled orders, and cash flow'}
            ]
        }
        
        self._render_template('index_report.j2', context, 'index.html')

    def _render_template(self, template_name: str, context: dict, output_filename: str):
        """Render a Jinja template and save to output directory."""
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(context)
            
            output_path = self.output_dir / output_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered)
            
            logger.info(f"Saved {output_filename}")
        except Exception as e:
            logger.error(f"Error rendering {template_name}: {e}")
            raise

    def _build_executive_summary(self):
        """Generate LLM-based executive summary PowerPoint."""
        logger.info("Generating Executive Summary with LLM...")
        
        try:
            # Generate insights with LLM
            llm_client = LLMClient()
            insights = llm_client.generate_insights(self.aggregated_data)
            
            # Generate PowerPoint
            pptx_generator = ExecutiveSummaryGenerator()
            pptx_path = self.output_dir / 'executive_summary.pptx'
            
            pptx_generator.generate_presentation(
                insights=insights,
                report_data=self.aggregated_data,
                output_path=str(pptx_path)
            )
            
            logger.info(f"Executive summary PowerPoint created: {pptx_path}")
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            logger.warning("Continuing without executive summary...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    builder = ReportBuilder()
    builder.build_report()
