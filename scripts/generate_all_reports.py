"""
Generate reports for multiple months.
"""
from src.reporting.report_builder import ReportBuilder
import logging

logging.basicConfig(level=logging.INFO)

# Generate reports for 4 months
months = ["2025-07", "2025-08", "2025-09", "2025-10"]

for month in months:
    print(f"\n{'='*60}")
    print(f"Generating reports for {month}")
    print(f"{'='*60}")
    
    try:
        builder = ReportBuilder(report_month=month)
        builder.build_report()
        print(f"[OK] {month} reports complete!")
    except Exception as e:
        print(f"[ERROR] Error generating {month} reports: {e}")

print(f"\n{'='*60}")
print("[OK] All monthly reports generated!")
print(f"{'='*60}")

