# NexCart Digital: Monthly Inventory & Revenue Analytics
![E-commerce business struggling with manual reporting and data silos](E-commerce_business_struggling_with_manual_reporting_and_data_silos.png)

## 🚀 About the Project
This project delivers a centralized data analytics platform for **NexCart Digital**, a Series A e-commerce retailer. The solution addresses critical visibility gaps in inventory management and revenue tracking by unifying data from internal systems into a single source of truth.

The pipeline processes data from Orders, Inventory, Customers, and Transactions to provide automated, real-time dashboards and predictive insights, replacing manual spreadsheet reporting.

---

## 🏢 Client Profile
*   **Company**: NexCart Digital
*   **Industry**: E-commerce Retail (Fashion & Lifestyle)
*   **Key Stakeholders**:
    *   **Jennifer Wu (VP of Ops)**: Needs actionable data to manage P&L and inventory.
    *   **David Chen (CFO)**: Requires real-time financial accuracy.
    *   **Marcus Rodriguez (Head of Marketing)**: Needs channel performance visibility.

---

## 📉 Business Context
NexCart operates across multiple sales channels with regional warehouses. The project aims to solve:

*   **Revenue Visibility**: Automating monthly profitability reporting.
*   **Inventory Management**: Preventing stockouts through better demand signals.
*   **Channel Performance**: Tracking revenue across different sales channels.
*   **Data Consolidation**: Merging scattered data into a unified analytics layer.

---

## 📊 Data Landscape
The solution integrates the following data sources via an ETL pipeline:

| Source Table | Content |
| :--- | :--- |
| **orders_raw** | Order details, dates, and total amounts. |
| **inventory_snapshots_raw** | Daily inventory levels by SKU and warehouse. |
| **customers** | Customer demographics and location data. |
| **transactions** | Payment transaction records and status. |
| **channels_raw** | Sales channel metadata (e.g., Web, Mobile, Social). |

**Key Features**:
*   **Data Cleaning**: Automated handling of outliers, missing values, and duplicates using PySpark.
*   **Validation**: Data quality checks before loading into the analytics layer.
*   **Storage**: Cleaned data is stored in structured tables (`orders_clean`, `inventory_clean`, etc.) for reporting.

---

## 🎯 Key Deliverables
1.  **Operational Dashboard**: Interactive Dash application displaying:
    *   Monthly Revenue Trends
    *   Sales Channel Distribution
    *   Top Products by Revenue
    *   Geographic Sales Performance
    *   Inventory Levels Over Time
    *   Payment Method Analysis
2.  **Automated Monthly Pipeline**: ETL process to ingest, clean, and aggregate data.
3.  **Ad-Hoc Exploration**: Jupyter notebooks for deep-dive analysis.

---

## 🛠️ Tech Stack
*   **Core**: Python 3.11+
*   **Data Processing**: PySpark
*   **Database**: SQLite
*   **Dashboarding**: Plotly Dash
*   **Reporting**: Pandas & Jinja2

---

## ⚙️ Setup & Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/nexcart-analytics.git
    cd nexcart-analytics
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize Database**
    ```bash
    python db/init_db.py
    ```

4.  **Run the ETL Pipeline**
    ```bash
    python spark_jobs/etl_raw_to_cleaned.py
    ```

5.  **Launch the Dashboard**
    ```bash
    python dashboard_app.py
    ```
    Access the dashboard at `http://127.0.0.1:8050`

---

## 📬 Contact

*   **LinkedIn**: [Adejori Eniola](https://www.linkedin.com/in/placeholder)
*   **Website**: [adatamage](https://www.adatamage.com)
*   **Email**: [adejorieniola@adatamage.com](mailto:adejorieniola@adatamage.com)
