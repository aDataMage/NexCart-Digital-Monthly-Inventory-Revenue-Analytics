"""
Interactive Dash Dashboard - Multi-Month Analytics
Displays comprehensive business metrics across all available months.
"""
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Initialize Dash app
app = dash.Dash(__name__, title="Business Analytics Dashboard")
app._favicon = None

# Database connection
DB_PATH = "inventory_v2.db"

# Enhanced Color scheme with gradients
COLORS = {
    'primary': '#667eea',
    'primary_light': '#764ba2',
    'success': '#10b981',
    'success_light': '#34d399',
    'warning': '#f59e0b',
    'warning_light': '#fbbf24',
    'danger': '#ef4444',
    'info': '#06b6d4',
    'info_light': '#22d3ee',
    'dark': '#1f2937',
    'light': '#f9fafb',
    'card_bg': '#ffffff',
    'text_primary': '#111827',
    'text_secondary': '#6b7280'
}

def get_data():
    """Fetch all data from database."""
    conn = sqlite3.connect(DB_PATH)
    
    data = {
        'orders': pd.read_sql("""
            SELECT 
                o.order_date,
                o.total_amount,
                o.channel_id,
                o.status,
                c.channel_name,
                c.commission_rate
            FROM orders_clean o
            JOIN channels_raw c ON o.channel_id = c.channel_id
        """, conn),
        
        'products': pd.read_sql("""
            SELECT 
                oi.sku,
                oi.quantity,
                oi.unit_price,
                o.order_date
            FROM order_items_raw oi
            JOIN orders_clean o ON oi.order_id = o.order_id
        """, conn),
        
        'customers': pd.read_sql("""
            SELECT 
                c.customer_id,
                c.state,
                c.city,
                o.order_date,
                o.total_amount
            FROM customers_clean c
            JOIN orders_clean o ON c.customer_id = o.customer_id
        """, conn),
        
        'inventory': pd.read_sql("""
            SELECT 
                snapshot_date,
                warehouse_id,
                SUM(quantity_on_hand) as total_stock
            FROM inventory_clean
            GROUP BY snapshot_date, warehouse_id
        """, conn),
        
        'transactions': pd.read_sql("""
            SELECT 
                transaction_date,
                payment_method,
                amount,
                status
            FROM transactions_clean
            WHERE status = 'SUCCESS'
        """, conn)
    }
    
    conn.close()
    
    # Convert dates
    data['orders']['order_date'] = pd.to_datetime(data['orders']['order_date'])
    data['products']['order_date'] = pd.to_datetime(data['products']['order_date'])
    data['customers']['order_date'] = pd.to_datetime(data['customers']['order_date'])
    data['inventory']['snapshot_date'] = pd.to_datetime(data['inventory']['snapshot_date'])
    data['transactions']['transaction_date'] = pd.to_datetime(data['transactions']['transaction_date'])
    
    return data


def create_kpi_card(title, value, subtitle="", trend=None, trend_label="", color=COLORS['primary']):
    """Create an enhanced KPI card with gradient and animations."""
    
    # Trend indicator
    trend_element = None
    if trend is not None:
        trend_color = COLORS['success'] if trend >= 0 else COLORS['danger']
        trend_arrow = "↑" if trend >= 0 else "↓"
        trend_element = html.Div([
            html.Span(trend_arrow, style={
                'fontSize': '16px',
                'fontWeight': 'bold',
                'marginRight': '4px'
            }),
            html.Span(f"{abs(trend):.1f}%", style={
                'fontSize': '14px',
                'fontWeight': '600'
            }),
            html.Span(f" {trend_label}", style={
                'fontSize': '11px',
                'fontWeight': 'normal',
                'opacity': '0.7',
                'marginLeft': '4px'
            })
        ], style={
            'color': trend_color,
            'backgroundColor': f"{trend_color}15",
            'padding': '4px 12px',
            'borderRadius': '20px',
            'display': 'inline-block',
            'marginTop': '8px'
        })

    return html.Div([
        html.Div([
            html.Div(style={
                'position': 'absolute',
                'top': '0',
                'left': '0',
                'right': '0',
                'height': '4px',
                'background': f'linear-gradient(90deg, {color} 0%, {color}AA 100%)',
                'borderRadius': '8px 8px 0 0'
            }),
            html.H4(title, style={
                'color': COLORS['text_secondary'],
                'marginBottom': '12px',
                'fontSize': '13px',
                'fontWeight': '600',
                'textTransform': 'uppercase',
                'letterSpacing': '0.5px'
            }),
            html.H2(value, style={
                'color': COLORS['text_primary'],
                'margin': '8px 0',
                'fontWeight': '700',
                'fontSize': '32px',
                'letterSpacing': '-0.5px'
            }),
            html.P(subtitle, style={
                'color': COLORS['text_secondary'],
                'fontSize': '13px',
                'margin': '0 0 8px 0'
            }),
            trend_element if trend_element else html.Div()
        ], style={'position': 'relative'})
    ], style={
        'backgroundColor': COLORS['card_bg'],
        'padding': '24px',
        'borderRadius': '12px',
        'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)',
        'minHeight': '160px',
        'position': 'relative',
        'transition': 'all 0.3s ease',
        'border': '1px solid #e5e7eb'
    })


# Layout
app.layout = html.Div([
    # Header with gradient
    html.Div([
        html.Div([
            html.H1([
                html.Span("📊 ", style={'fontSize': '40px'}),
                "Business Analytics Dashboard"
            ], style={
                'color': 'white',
                'margin': '0',
                'fontWeight': '700',
                'fontSize': '32px',
                'letterSpacing': '-0.5px'
            }),
            html.P("Real-time insights and performance metrics", style={
                'color': 'rgba(255,255,255,0.9)',
                'margin': '8px 0 0 0',
                'fontSize': '16px',
                'fontWeight': '400'
            })
        ], style={'textAlign': 'center', 'padding': '32px 20px'})
    ], style={
        'background': f'linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["primary_light"]} 100%)',
        'marginBottom': '40px',
        'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'
    }),
    
    # Main Container
    html.Div([
        # Date Range Selector with enhanced styling
        html.Div([
            html.Div([
                html.Label("📅 Date Range", style={
                    'fontWeight': '600',
                    'marginBottom': '12px',
                    'display': 'block',
                    'color': COLORS['text_primary'],
                    'fontSize': '14px'
                }),
                dcc.DatePickerRange(
                    id='date-range',
                    start_date='2025-07-01',
                    end_date='2025-10-31',
                    display_format='YYYY-MM-DD',
                    style={'marginBottom': '20px'}
                ),
            ], style={
                'backgroundColor': COLORS['card_bg'],
                'padding': '24px',
                'borderRadius': '12px',
                'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                'border': '1px solid #e5e7eb'
            }),
            
            # Download Button
            html.Div([
                html.Button("📥 Download CSV", id="btn_csv", style={
                    'backgroundColor': COLORS['primary'],
                    'color': 'white',
                    'border': 'none',
                    'padding': '12px 24px',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontSize': '14px',
                    'fontWeight': '600',
                    'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                    'transition': 'all 0.2s ease',
                    'marginLeft': '20px'
                }),
                dcc.Download(id="download-dataframe-csv"),
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={'marginBottom': '30px', 'display': 'flex', 'alignItems': 'center'}),
        
        # KPI Cards Row
        html.Div(id='kpi-cards', style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(auto-fit, minmax(240px, 1fr))',
            'gap': '24px',
            'marginBottom': '40px'
        }),
        
        # Charts Grid
        html.Div([
            # Revenue Trend
            html.Div([
                html.Div([
                    dcc.Graph(id='revenue-trend', config={'displayModeBar': False})
                ], style={
                    'backgroundColor': COLORS['card_bg'],
                    'padding': '20px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                    'border': '1px solid #e5e7eb'
                })
            ], style={'marginBottom': '30px'}),
            
            # Two column layout
            html.Div([
                html.Div([
                    html.Div([
                        dcc.Graph(id='channel-distribution', config={'displayModeBar': False})
                    ], style={
                        'backgroundColor': COLORS['card_bg'],
                        'padding': '20px',
                        'borderRadius': '12px',
                        'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                        'border': '1px solid #e5e7eb'
                    })
                ], style={'flex': '1', 'marginRight': '15px'}),
                
                html.Div([
                    html.Div([
                        dcc.Graph(id='top-products', config={'displayModeBar': False})
                    ], style={
                        'backgroundColor': COLORS['card_bg'],
                        'padding': '20px',
                        'borderRadius': '12px',
                        'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                        'border': '1px solid #e5e7eb'
                    })
                ], style={'flex': '1', 'marginLeft': '15px'})
            ], style={'display': 'flex', 'marginBottom': '30px', 'gap': '24px'}),
            
            # Another two column layout
            html.Div([
                html.Div([
                    html.Div([
                        dcc.Graph(id='geographic-sales', config={'displayModeBar': False})
                    ], style={
                        'backgroundColor': COLORS['card_bg'],
                        'padding': '20px',
                        'borderRadius': '12px',
                        'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                        'border': '1px solid #e5e7eb'
                    })
                ], style={'flex': '1', 'marginRight': '15px'}),
                
                html.Div([
                    html.Div([
                        dcc.Graph(id='payment-methods', config={'displayModeBar': False})
                    ], style={
                        'backgroundColor': COLORS['card_bg'],
                        'padding': '20px',
                        'borderRadius': '12px',
                        'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                        'border': '1px solid #e5e7eb'
                    })
                ], style={'flex': '1', 'marginLeft': '15px'})
            ], style={'display': 'flex', 'marginBottom': '30px', 'gap': '24px'}),
            
            # Inventory Trend
            html.Div([
                html.Div([
                    dcc.Graph(id='inventory-trend', config={'displayModeBar': False})
                ], style={
                    'backgroundColor': COLORS['card_bg'],
                    'padding': '20px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                    'border': '1px solid #e5e7eb'
                })
            ], style={'marginBottom': '30px'}),
        ])
    ], style={
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '30px',
        'backgroundColor': COLORS['light'],
        'minHeight': '100vh'
    }),
    
    # Footer
    html.Div([
        html.P([
            html.Span("⚡ ", style={'fontSize': '16px'}),
            f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ], style={
            'textAlign': 'center',
            'color': COLORS['text_secondary'],
            'padding': '24px',
            'fontSize': '13px'
        })
    ])
], style={'backgroundColor': COLORS['light'], 'minHeight': '100vh', 'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'})


# Callbacks
@app.callback(
    [Output('kpi-cards', 'children'),
     Output('revenue-trend', 'figure'),
     Output('channel-distribution', 'figure'),
     Output('top-products', 'figure'),
     Output('geographic-sales', 'figure'),
     Output('payment-methods', 'figure'),
     Output('inventory-trend', 'figure')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_dashboard(start_date, end_date):
    """Update all dashboard components based on date range."""
    data = get_data()
    
    # Filter data by date range
    mask_orders = (data['orders']['order_date'] >= start_date) & (data['orders']['order_date'] <= end_date)
    filtered_orders = data['orders'][mask_orders]
    
    mask_products = (data['products']['order_date'] >= start_date) & (data['products']['order_date'] <= end_date)
    filtered_products = data['products'][mask_products]
    
    mask_customers = (data['customers']['order_date'] >= start_date) & (data['customers']['order_date'] <= end_date)
    filtered_customers = data['customers'][mask_customers]
    
    # Calculate KPIs
    total_revenue = filtered_orders['total_amount'].sum()
    total_orders = len(filtered_orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    unique_customers = filtered_customers['customer_id'].nunique()
    
    # Calculate Previous Period KPIs
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    delta = end_dt - start_dt
    
    prev_end = start_dt - timedelta(days=1)
    prev_start = prev_end - delta
    
    mask_prev_orders = (data['orders']['order_date'] >= prev_start) & (data['orders']['order_date'] <= prev_end)
    prev_orders = data['orders'][mask_prev_orders]
    
    mask_prev_customers = (data['customers']['order_date'] >= prev_start) & (data['customers']['order_date'] <= prev_end)
    prev_customers = data['customers'][mask_prev_customers]
    
    # Previous Metrics
    prev_revenue = prev_orders['total_amount'].sum()
    prev_total_orders = len(prev_orders)
    prev_aov = prev_revenue / prev_total_orders if prev_total_orders > 0 else 0
    prev_unique_customers = prev_customers['customer_id'].nunique()
    
    # Calculate Trends
    def calc_trend(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100

    revenue_trend = calc_trend(total_revenue, prev_revenue)
    orders_trend = calc_trend(total_orders, prev_total_orders)
    aov_trend = calc_trend(avg_order_value, prev_aov)
    customers_trend = calc_trend(unique_customers, prev_unique_customers)
    
    trend_label = "vs prev period"

    # KPI Cards
    kpi_cards = [
        create_kpi_card("Total Revenue", f"${total_revenue:,.2f}", f"{total_orders} orders", 
                       trend=revenue_trend, trend_label=trend_label, color=COLORS['success']),
        create_kpi_card("Avg Order Value", f"${avg_order_value:.2f}", "per order", 
                       trend=aov_trend, trend_label=trend_label, color=COLORS['primary']),
        create_kpi_card("Total Orders", f"{total_orders:,}", f"{unique_customers} customers", 
                       trend=orders_trend, trend_label=trend_label, color=COLORS['info']),
        create_kpi_card("Active Customers", f"{unique_customers:,}", "unique customers", 
                       trend=customers_trend, trend_label=trend_label, color=COLORS['warning'])
    ]
    
    # 1. Revenue Trend (Monthly) - Enhanced styling
    monthly_revenue = filtered_orders.groupby(filtered_orders['order_date'].dt.to_period('M'))['total_amount'].sum().reset_index()
    monthly_revenue['order_date'] = monthly_revenue['order_date'].astype(str)
    
    revenue_fig = go.Figure()
    revenue_fig.add_trace(go.Scatter(
        x=monthly_revenue['order_date'],
        y=monthly_revenue['total_amount'],
        mode='lines+markers',
        name='Revenue',
        line=dict(color=COLORS['primary'], width=4),
        marker=dict(size=12, color=COLORS['primary'], line=dict(color='white', width=2)),
        fill='tozeroy',
        fillcolor=f'rgba(102, 126, 234, 0.1)',
        hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>'
    ))
    revenue_fig.update_layout(
        title={
            'text': "📈 Monthly Revenue Trend",
            'font': {'size': 20, 'color': COLORS['text_primary'], 'family': 'Arial, sans-serif'}
        },
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        template="plotly_white",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial, sans-serif', 'color': COLORS['text_secondary']},
        margin=dict(t=60, b=40, l=60, r=40)
    )
    
    # 2. Channel Distribution (Pie) - Enhanced
    channel_revenue = filtered_orders.groupby('channel_name')['total_amount'].sum().reset_index()
    channel_fig = px.pie(
        channel_revenue,
        values='total_amount',
        names='channel_name',
        title="🛒 Revenue by Sales Channel",
        color_discrete_sequence=['#667eea', '#10b981', '#f59e0b', '#06b6d4', '#ef4444'],
        hole=0.4
    )
    channel_fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=12,
        marker=dict(line=dict(color='white', width=2))
    )
    channel_fig.update_layout(
        title={'font': {'size': 20, 'color': COLORS['text_primary']}},
        font={'family': 'Arial, sans-serif', 'color': COLORS['text_secondary']},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=60, b=40, l=40, r=40)
    )
    
    # 3. Top Products (Bar) - Enhanced
    product_sales = filtered_products.groupby('sku').agg({
        'quantity': 'sum',
        'unit_price': 'mean'
    }).reset_index()
    product_sales['revenue'] = product_sales['quantity'] * product_sales['unit_price']
    top_products = product_sales.nlargest(10, 'revenue')
    
    products_fig = px.bar(
        top_products,
        x='sku',
        y='revenue',
        title="📦 Top 10 Products by Revenue",
        color='revenue',
        color_continuous_scale=[[0, '#e0e7ff'], [0.5, '#818cf8'], [1, '#667eea']]
    )
    products_fig.update_traces(
        marker=dict(line=dict(color='white', width=1)),
        hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>'
    )
    products_fig.update_layout(
        xaxis_title="SKU",
        yaxis_title="Revenue ($)",
        showlegend=False,
        title={'font': {'size': 20, 'color': COLORS['text_primary']}},
        font={'family': 'Arial, sans-serif', 'color': COLORS['text_secondary']},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=60, b=60, l=60, r=40)
    )
    
    # 4. Geographic Sales (Horizontal Bar) - Enhanced
    state_sales = filtered_customers.groupby('state')['total_amount'].sum().reset_index()
    top_states = state_sales.nlargest(10, 'total_amount')
    
    geo_fig = px.bar(
        top_states.sort_values('total_amount'),
        x='total_amount',
        y='state',
        orientation='h',
        title="🗺️ Top 10 States by Sales",
        color='total_amount',
        color_continuous_scale=[[0, '#d1fae5'], [0.5, '#34d399'], [1, '#10b981']]
    )
    geo_fig.update_traces(
        marker=dict(line=dict(color='white', width=1)),
        hovertemplate='<b>%{y}</b><br>Sales: $%{x:,.2f}<extra></extra>'
    )
    geo_fig.update_layout(
        xaxis_title="Revenue ($)",
        yaxis_title="State",
        showlegend=False,
        title={'font': {'size': 20, 'color': COLORS['text_primary']}},
        font={'family': 'Arial, sans-serif', 'color': COLORS['text_secondary']},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=60, b=40, l=60, r=40)
    )
    
    # 5. Payment Methods (Donut) - Enhanced
    mask_txn = (data['transactions']['transaction_date'] >= start_date) & (data['transactions']['transaction_date'] <= end_date)
    filtered_txn = data['transactions'][mask_txn]
    
    payment_dist = filtered_txn.groupby('payment_method')['amount'].sum().reset_index()
    payment_fig = px.pie(
        payment_dist,
        values='amount',
        names='payment_method',
        title="💳 Payment Method Distribution",
        hole=0.5,
        color_discrete_sequence=['#06b6d4', '#f59e0b', '#10b981', '#667eea', '#ef4444']
    )
    payment_fig.update_traces(
        textposition='outside',
        textinfo='percent+label',
        textfont_size=12,
        marker=dict(line=dict(color='white', width=2))
    )
    payment_fig.update_layout(
        title={'font': {'size': 20, 'color': COLORS['text_primary']}},
        font={'family': 'Arial, sans-serif', 'color': COLORS['text_secondary']},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=60, b=40, l=40, r=40)
    )
    
    # 6. Inventory Trend - Enhanced
    mask_inv = (data['inventory']['snapshot_date'] >= start_date) & (data['inventory']['snapshot_date'] <= end_date)
    filtered_inv = data['inventory'][mask_inv]
    
    inv_trend = filtered_inv.groupby('snapshot_date')['total_stock'].sum().reset_index()
    
    inv_fig = px.area(
        inv_trend,
        x='snapshot_date',
        y='total_stock',
        title="📊 Total Inventory Over Time"
    )
    inv_fig.update_traces(
        line=dict(color=COLORS['success'], width=4),
        fillcolor=f'rgba(16, 185, 129, 0.1)',
        marker=dict(size=8, color=COLORS['success'], line=dict(color='white', width=2)),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Stock: %{y:,.0f} units<extra></extra>'
    )
    inv_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Total Stock Units",
        template="plotly_white",
        title={'font': {'size': 20, 'color': COLORS['text_primary']}},
        font={'family': 'Arial, sans-serif', 'color': COLORS['text_secondary']},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=60, b=40, l=60, r=40)
    )
    
    return kpi_cards, revenue_fig, channel_fig, products_fig, geo_fig, payment_fig, inv_fig


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    [dash.State('date-range', 'start_date'),
     dash.State('date-range', 'end_date')],
    prevent_initial_call=True,
)
def download_csv(n_clicks, start_date, end_date):
    """Download filtered data as CSV."""
    data = get_data()
    
    # Filter orders by date range
    mask_orders = (data['orders']['order_date'] >= start_date) & (data['orders']['order_date'] <= end_date)
    filtered_orders = data['orders'][mask_orders]
    
    return dcc.send_data_frame(filtered_orders.to_csv, f"sales_data_{start_date}_{end_date}.csv", index=False)


if __name__ == '__main__':
    print("🚀 Starting Dash Dashboard...")
    print("📊 Dashboard available at http://127.0.0.1:8050")
    app.run(debug=True, port=8050)