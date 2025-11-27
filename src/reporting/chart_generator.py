"""
Chart generation utilities for creating visualizations from report data.
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def create_bar_chart(data: pd.DataFrame, x_col: str, y_cols: list, title: str, 
                     output_path: str, labels: list = None):
    """
    Creates a grouped bar chart for comparing multiple metrics.
    
    Args:
        data: DataFrame with data
        x_col: Column name for x-axis categories
        y_cols: List of column names for y-axis values
        title: Chart title
        output_path: Where to save the chart
        labels: Optional custom labels for y_cols
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(data))
    width = 0.8 / len(y_cols)
    
    for i, col in enumerate(y_cols):
        offset = width * i - (width * (len(y_cols) - 1) / 2)
        label = labels[i] if labels else col
        ax.bar(x + offset, data[col], width, label=label)
    
    ax.set_xlabel(x_col.replace('_', ' ').title())
    ax.set_ylabel('Amount ($)')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(data[x_col], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved bar chart to {output_path}")


def create_pareto_chart(data: pd.DataFrame, category_col: str, value_col: str, 
                       title: str, output_path: str, top_n: int = 20):
    """
    Creates a Pareto chart showing cumulative percentage.
    
    Args:
        data: DataFrame with data
        category_col: Column name for categories
        value_col: Column name for values
        title: Chart title
        output_path: Where to save the chart
        top_n: Number of top items to show
    """
    # Sort and calculate cumulative percentage
    df_sorted = data.sort_values(value_col, ascending=False).head(top_n).reset_index(drop=True)
    total = df_sorted[value_col].sum()
    df_sorted['cumulative_pct'] = (df_sorted[value_col].cumsum() / total) * 100
    
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # Bar chart
    x = np.arange(len(df_sorted))
    ax1.bar(x, df_sorted[value_col], color='steelblue', alpha=0.7)
    ax1.set_xlabel(category_col.replace('_', ' ').title())
    ax1.set_ylabel(value_col.replace('_', ' ').title(), color='steelblue')
    ax1.tick_params(axis='y', labelcolor='steelblue')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_sorted[category_col], rotation=45, ha='right')
    
    # Line chart for cumulative percentage
    ax2 = ax1.twinx()
    ax2.plot(x, df_sorted['cumulative_pct'], color='red', marker='o', linewidth=2)
    ax2.set_ylabel('Cumulative Percentage (%)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.set_ylim(0, 105)
    ax2.axhline(y=80, color='gray', linestyle='--', alpha=0.5, label='80% Line')
    
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved Pareto chart to {output_path}")


def create_stacked_bar(data: pd.DataFrame, x_col: str, stack_col: str, 
                      value_col: str, title: str, output_path: str):
    """
    Creates a stacked bar chart.
    
    Args:
        data: DataFrame with data
        x_col: Column for x-axis (e.g., warehouse_id)
        stack_col: Column to stack by (e.g., SKU)
        value_col: Column for values
        title: Chart title
        output_path: Where to save the chart
    """
    # Pivot data for stacking
    pivot_data = data.pivot_table(index=x_col, columns=stack_col, values=value_col, fill_value=0)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    pivot_data.plot(kind='bar', stacked=True, ax=ax, colormap='tab20')
    
    ax.set_xlabel(x_col.replace('_', ' ').title())
    ax.set_ylabel(value_col.replace('_', ' ').title())
    ax.set_title(title)
    ax.legend(title=stack_col.replace('_', ' ').title(), bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved stacked bar chart to {output_path}")


def create_pie_chart(data: pd.DataFrame, category_col: str, value_col: str, 
                    title: str, output_path: str):
    """
    Creates a pie chart for distribution analysis.
    
    Args:
        data: DataFrame with data
        category_col: Column for pie slices
        value_col: Column for values
        title: Chart title
        output_path: Where to save the chart
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(data)))
    wedges, texts, autotexts = ax.pie(
        data[value_col], 
        labels=data[category_col],
        autopct='%1.1f%%',
        colors=colors,
        startangle=90
    )
    
    # Make percentage text more readable
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved pie chart to {output_path}")


def create_line_chart(data: pd.DataFrame, x_col: str, y_col: str, 
                     title: str, output_path: str, xlabel: str = None, ylabel: str = None):
    """
    Creates a line chart for time series or trend analysis.
    
    Args:
        data: DataFrame with data
        x_col: Column for x-axis (e.g., date)
        y_col: Column for y-axis values
        title: Chart title
        output_path: Where to save the chart
        xlabel: Custom x-axis label
        ylabel: Custom y-axis label
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.plot(data[x_col], data[y_col], marker='o', linewidth=2, markersize=6, color='steelblue')
    ax.fill_between(data[x_col], data[y_col], alpha=0.3, color='steelblue')
    
    ax.set_xlabel(xlabel or x_col.replace('_', ' ').title())
    ax.set_ylabel(ylabel or y_col.replace('_', ' ').title())
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved line chart to {output_path}")


def create_horizontal_bar(data: pd.DataFrame, category_col: str, value_col: str,
                         title: str, output_path: str, top_n: int = 15):
    """
    Creates a horizontal bar chart, useful for long category names.
    
    Args:
        data: DataFrame with data
        category_col: Column for categories
        value_col: Column for values
        title: Chart title
        output_path: Where to save the chart
        top_n: Number of top items to show
    """
    df_sorted = data.sort_values(value_col, ascending=True).tail(top_n)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    y_pos = np.arange(len(df_sorted))
    ax.barh(y_pos, df_sorted[value_col], color='steelblue', alpha=0.7)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted[category_col])
    ax.set_xlabel(value_col.replace('_', ' ').title())
    ax.set_title(title)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved horizontal bar chart to {output_path}")
