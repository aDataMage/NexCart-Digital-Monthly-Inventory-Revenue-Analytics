"""
Interactive Dash Dashboard - Multi-Tab Analytics
Displays comprehensive business metrics with 6 report tabs.
"""
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Initialize Dash app
app = dash.Dash(__name__, title="Business Analytics Dashboard",
                suppress_callback_exceptions=True)
app._favicon = None

# Add custom CSS for range buttons
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .range-btn {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #e5e7eb;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            .range-btn:hover {
                background-color: #e5e7eb;
                border-color: #d1d5db;
            }
            .range-btn:active, .range-btn.active {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
            }
            .reset-btn {
                background-color: #fef3c7;
                border-color: #fcd34d;
                color: #92400e;
            }
            .reset-btn:hover {
                background-color: #fde68a;
                border-color: #fbbf24;
            }
            .DateInput_input {
                font-size: 14px !important;
                padding: 8px 12px !important;
            }
            .DateRangePickerInput {
                border-radius: 8px !important;
                border: 1px solid #e5e7eb !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Database connection
DB_PATH = "inventory_v2.db"

# Enhanced Color scheme
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

TAB_COLORS = {
    'overview': '#667eea',
    'sales': '#3498db',
    'products': '#e74c3c',
    'inventory': '#27ae60',
    'customers': '#9b59b6',
    'payments': '#16a085'
}

# Common hover template style
HOVER_TEMPLATE_STYLE = dict(
    bgcolor="rgba(255, 255, 255, 0.95)",
    bordercolor="#e5e7eb",
    font=dict(family="Arial, sans-serif", size=13, color="#1f2937")
)


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_data():
    """Fetch all data from database."""
    conn = get_connection()

    data = {
        'orders': pd.read_sql("""
            SELECT o.order_date, o.total_amount, o.channel_id, o.status, o.customer_id,
                   c.channel_name, c.commission_rate
            FROM orders_clean o
            JOIN channels_raw c ON o.channel_id = c.channel_id
        """, conn),

        'products': pd.read_sql("""
            SELECT oi.sku, oi.quantity, oi.unit_price, oi.order_id, o.order_date
            FROM order_items_raw oi
            JOIN orders_clean o ON oi.order_id = o.order_id
        """, conn),

        'customers': pd.read_sql("""
            SELECT c.customer_id, c.state, c.city, c.signup_date,
                   o.order_date, o.total_amount
            FROM customers c
            LEFT JOIN orders_clean o ON c.customer_id = o.customer_id
        """, conn),

        'inventory': pd.read_sql("""
            SELECT snapshot_date, warehouse_id, sku, quantity_on_hand
            FROM inventory_clean
        """, conn),

        'transactions': pd.read_sql("""
            SELECT transaction_date, payment_method, amount, status, order_id
            FROM transactions_clean
        """, conn)
    }

    conn.close()

    # Convert dates
    for key in ['orders', 'products', 'customers']:
        if 'order_date' in data[key].columns:
            data[key]['order_date'] = pd.to_datetime(data[key]['order_date'])
    data['customers']['signup_date'] = pd.to_datetime(
        data['customers']['signup_date'])
    data['inventory']['snapshot_date'] = pd.to_datetime(
        data['inventory']['snapshot_date'])
    data['transactions']['transaction_date'] = pd.to_datetime(
        data['transactions']['transaction_date'])

    return data


def create_styled_table(df, columns_config, id_prefix="table"):
    """Create a styled DataTable with consistent formatting."""
    return dash_table.DataTable(
        id=f'{id_prefix}-{datetime.now().timestamp()}',
        columns=columns_config,
        data=df.to_dict('records'),
        style_table={'overflowX': 'auto', 'borderRadius': '8px'},
        style_header={
            'backgroundColor': '#f8fafc',
            'fontWeight': '600',
            'color': '#374151',
            'borderBottom': '2px solid #e5e7eb',
            'padding': '12px 16px',
            'textAlign': 'left',
            'fontSize': '13px',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px'
        },
        style_cell={
            'padding': '12px 16px',
            'textAlign': 'left',
            'fontSize': '14px',
            'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif',
            'border': 'none',
            'borderBottom': '1px solid #f3f4f6',
            'color': '#374151',
            'maxWidth': '200px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#fafafa'},
            {'if': {'state': 'active'}, 'backgroundColor': '#e0e7ff', 'border': 'none'},
            {'if': {'state': 'selected'},
                'backgroundColor': '#e0e7ff', 'border': 'none'}
        ],
        style_as_list_view=True,
        page_size=10,
        page_action='native',
        sort_action='native',
        filter_action='native'
    )


def create_kpi_card(title, value, subtitle="", trend=None, trend_label="", color=COLORS['primary'], icon="📊"):
    """Create an enhanced KPI card."""
    trend_element = None
    if trend is not None:
        trend_color = COLORS['success'] if trend >= 0 else COLORS['danger']
        trend_arrow = "↑" if trend >= 0 else "↓"
        trend_element = html.Div([
            html.Span(trend_arrow, style={
                      'fontSize': '16px', 'fontWeight': 'bold', 'marginRight': '4px'}),
            html.Span(f"{abs(trend):.1f}%", style={
                      'fontSize': '14px', 'fontWeight': '600'}),
            html.Span(f" {trend_label}", style={
                      'fontSize': '11px', 'opacity': '0.7', 'marginLeft': '4px'})
        ], style={
            'color': trend_color, 'backgroundColor': f"{trend_color}15",
            'padding': '4px 12px', 'borderRadius': '20px', 'display': 'inline-block', 'marginTop': '8px'
        })

    return html.Div([
        html.Div([
            html.Div(style={
                'position': 'absolute', 'top': '0', 'left': '0', 'right': '0', 'height': '5%',
                'background': f'linear-gradient(90deg, {color} 0%, {color}AA 100%)',
                'borderRadius': '12px 12px 0 0'
            }),
            html.Div([
                html.Div(icon, style={'fontSize': '16px',
                                      }),
                html.H4(title, style={
                    'color': COLORS['text_secondary'], 'fontSize': '13px',
                    'fontWeight': '600', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'
                })
            ], style={
                "display": "flex",
                "justify-content": "flex-start",
                "align-items": "center",
                "gap": "2px", 'marginBottom': '12px'

            }),
            html.H2(value, style={
                'color': COLORS['text_primary'], 'margin': '8px 0', 'fontWeight': '700',
                'fontSize': '32px', 'letterSpacing': '-0.5px'
            }),
            html.P(subtitle, style={
                   'color': COLORS['text_secondary'], 'fontSize': '13px', 'margin': '0 0 8px 0'}),
            trend_element if trend_element else html.Div()
        ])
    ], style={
        'backgroundColor': COLORS['card_bg'], 'padding': '24px', 'borderRadius': '12px',
        'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)', 'minHeight': '160px',
        'position': 'relative', 'border': '1px solid #e5e7eb'
    })


def create_metric_card(title, value, icon="📊", color=COLORS['primary']):
    """Create a simple metric card for report tabs."""
    return html.Div([
        html.Div(icon, style={'fontSize': '28px', 'marginBottom': '8px'}),
        html.H4(title, style={'color': COLORS['text_secondary'],
                'fontSize': '12px', 'margin': '0', 'textTransform': 'uppercase'}),
        html.H3(value, style={'color': color, 'fontSize': '24px',
                'fontWeight': '700', 'margin': '8px 0 0 0'})
    ], style={
        'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'border': '1px solid #e5e7eb'
    })


def apply_hover_style(fig):
    """Apply consistent hover styling to a figure."""
    fig.update_layout(hoverlabel=HOVER_TEMPLATE_STYLE)
    return fig


# ============== LAYOUT ==============
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1([html.Span("📊 ", style={'fontSize': '40px'}), "Business Analytics Dashboard"],
                    style={'color': 'white', 'margin': '0 0 12px 0', 'fontWeight': '700', 'fontSize': '32px'}),
            html.P("Real-time insights and performance metrics",
                   style={'color': 'rgba(255,255,255,0.9)', 'margin': '0', 'fontSize': '16px'})
        ], style={'textAlign': 'center', 'padding': '32px 20px'})
    ], style={
        'background': f'linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["primary_light"]} 100%)',
        'marginBottom': '12px', 'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'
    }),

    # Tabs Navigation
    html.Div([
        dcc.Tabs(id='report-tabs', value='overview', children=[
            dcc.Tab(label='📈 Overview', value='overview',
                    style={'padding': '12px 20px', 'fontWeight': '600'},
                    selected_style={'padding': '12px 20px', 'fontWeight': '600', 'borderTop': f'3px solid {TAB_COLORS["overview"]}'}),
            dcc.Tab(label='💰 Sales & Channels', value='sales',
                    style={'padding': '12px 20px', 'fontWeight': '600'},
                    selected_style={'padding': '12px 20px', 'fontWeight': '600', 'borderTop': f'3px solid {TAB_COLORS["sales"]}'}),
            dcc.Tab(label='📦 Products', value='products',
                    style={'padding': '12px 20px', 'fontWeight': '600'},
                    selected_style={'padding': '12px 20px', 'fontWeight': '600', 'borderTop': f'3px solid {TAB_COLORS["products"]}'}),
            dcc.Tab(label='🏭 Inventory', value='inventory',
                    style={'padding': '12px 20px', 'fontWeight': '600'},
                    selected_style={'padding': '12px 20px', 'fontWeight': '600', 'borderTop': f'3px solid {TAB_COLORS["inventory"]}'}),
            dcc.Tab(label='👥 Customers', value='customers',
                    style={'padding': '12px 20px', 'fontWeight': '600'},
                    selected_style={'padding': '12px 20px', 'fontWeight': '600', 'borderTop': f'3px solid {TAB_COLORS["customers"]}'}),
            dcc.Tab(label='💳 Payments', value='payments',
                    style={'padding': '12px 20px', 'fontWeight': '600'},
                    selected_style={'padding': '12px 20px', 'fontWeight': '600', 'borderTop': f'3px solid {TAB_COLORS["payments"]}'}),
        ], style={'backgroundColor': 'white'})
    ], style={'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),

    # Main Content
    html.Div([
        # Date Range Selector - Enhanced with preset buttons
        html.Div([
            html.Div([
                html.Label("📅 Date Range", style={
                    'fontWeight': '600', 'marginBottom': '12px', 'display': 'block', 'fontSize': '14px', 'color': COLORS['text_primary']
                }),
                # Preset Range Buttons
                html.Div([
                    html.Button("Last Month", id="btn-last-month",
                                n_clicks=0, className="range-btn"),
                    html.Button("MTD", id="btn-mtd", n_clicks=0,
                                className="range-btn", title="Month to Date"),
                    html.Button("Last Quarter", id="btn-last-quarter",
                                n_clicks=0, className="range-btn"),
                    html.Button("YTD", id="btn-ytd", n_clicks=0,
                                className="range-btn", title="Year to Date"),
                    html.Button("🔄 Reset", id="btn-reset", n_clicks=0,
                                className="range-btn reset-btn"),
                ], style={'display': 'flex', 'gap': '8px', 'marginBottom': '16px', 'flexWrap': 'wrap'}),
                # Date Picker
                html.Div([
                    dcc.DatePickerRange(
                        id='date-range', start_date='2025-07-01', end_date='2025-10-31',
                        display_format='MMM DD, YYYY',
                        style={'width': '100%'}
                    ),
                ], style={'marginBottom': '8px'}),
                # Selected Range Display
                html.Div(id='selected-range-display', style={
                    'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginTop': '8px'
                })
            ], style={
                'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px',
                'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)', 'border': '1px solid #e5e7eb', 'minWidth': '380px'
            }),
            html.Div([
                html.Button("📥 Download CSV", id="btn_csv", style={
                    'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none',
                    'padding': '12px 24px', 'borderRadius': '8px', 'cursor': 'pointer',
                    'fontSize': '14px', 'fontWeight': '600', 'marginLeft': '20px'
                }),
                dcc.Download(id="download-dataframe-csv"),
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={'marginBottom': '30px', 'display': 'flex', 'alignItems': 'center', "width": "100%", "justify-content": "space-between"}),

        # Tab Content
        html.Div(id='tab-content')
    ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '30px', 'backgroundColor': COLORS['light'], 'minHeight': '100vh'}),

    # Footer
    html.Div([
        html.P([html.Span("⚡ ", style={'fontSize': '16px'}), f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
               style={'textAlign': 'center', 'color': COLORS['text_secondary'], 'padding': '24px', 'fontSize': '13px'})
    ])
], style={'backgroundColor': COLORS['light'], 'minHeight': '100vh', 'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif'})


# ============== DATE RANGE PRESET CALLBACK ==============
def get_full_data_range():
    """Get the full date range from the database."""
    conn = get_connection()
    result = pd.read_sql("""
        SELECT MIN(order_date) as min_date, MAX(order_date) as max_date 
        FROM orders_clean
    """, conn)
    conn.close()
    return result['min_date'].iloc[0], result['max_date'].iloc[0]


@app.callback(
    [Output('date-range', 'start_date'),
     Output('date-range', 'end_date')],
    [Input('btn-last-month', 'n_clicks'),
     Input('btn-mtd', 'n_clicks'),
     Input('btn-last-quarter', 'n_clicks'),
     Input('btn-ytd', 'n_clicks'),
     Input('btn-reset', 'n_clicks')],
    prevent_initial_call=True
)
def update_date_range(last_month, mtd, last_quarter, ytd, reset):
    """Update date range based on preset button clicks."""
    from dash import ctx

    # Reference date - using latest data date as "today" for demo
    min_date, max_date = get_full_data_range()
    today = datetime.strptime(max_date[:10], '%Y-%m-%d')

    triggered_id = ctx.triggered_id

    if triggered_id == 'btn-last-month':
        # Last complete month
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return last_month_start.strftime('%Y-%m-%d'), last_month_end.strftime('%Y-%m-%d')

    elif triggered_id == 'btn-mtd':
        # Month to date
        month_start = today.replace(day=1)
        return month_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')

    elif triggered_id == 'btn-last-quarter':
        # Last complete quarter
        current_quarter = (today.month - 1) // 3
        if current_quarter == 0:
            # Q4 of previous year
            quarter_start = datetime(today.year - 1, 10, 1)
            quarter_end = datetime(today.year - 1, 12, 31)
        else:
            quarter_start_month = (current_quarter - 1) * 3 + 1
            quarter_start = datetime(today.year, quarter_start_month, 1)
            quarter_end_month = quarter_start_month + 2
            if quarter_end_month == 12:
                quarter_end = datetime(today.year, 12, 31)
            else:
                quarter_end = datetime(
                    today.year, quarter_end_month + 1, 1) - timedelta(days=1)
        return quarter_start.strftime('%Y-%m-%d'), quarter_end.strftime('%Y-%m-%d')

    elif triggered_id == 'btn-ytd':
        # Year to date
        year_start = datetime(today.year, 1, 1)
        return year_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')

    elif triggered_id == 'btn-reset':
        # Full data range
        return min_date[:10], max_date[:10]

    # Default
    return '2025-07-01', '2025-10-31'


@app.callback(
    Output('selected-range-display', 'children'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_range_display(start_date, end_date):
    """Display the selected date range with duration."""
    if start_date and end_date:
        start = datetime.strptime(start_date[:10], '%Y-%m-%d')
        end = datetime.strptime(end_date[:10], '%Y-%m-%d')
        days = (end - start).days + 1

        start_fmt = start.strftime('%b %d, %Y')
        end_fmt = end.strftime('%b %d, %Y')

        return html.Span([
            html.Strong(f"{days} days"),
            f" selected ({start_fmt} → {end_fmt})"
        ])
    return ""


# ============== TAB CONTENT CALLBACK ==============
@app.callback(
    Output('tab-content', 'children'),
    [Input('report-tabs', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def render_tab_content(tab, start_date, end_date):
    data = get_data()

    if tab == 'overview':
        return render_overview_tab(data, start_date, end_date)
    elif tab == 'sales':
        return render_sales_tab(data, start_date, end_date)
    elif tab == 'products':
        return render_products_tab(data, start_date, end_date)
    elif tab == 'inventory':
        return render_inventory_tab(data, start_date, end_date)
    elif tab == 'customers':
        return render_customers_tab(data, start_date, end_date)
    elif tab == 'payments':
        return render_payments_tab(data, start_date, end_date)
    return html.Div("Select a tab")


# ============== OVERVIEW TAB ==============
def render_overview_tab(data, start_date, end_date):
    mask = (data['orders']['order_date'] >= start_date) & (
        data['orders']['order_date'] <= end_date)
    filtered = data['orders'][mask]

    total_revenue = filtered['total_amount'].sum()
    total_orders = len(filtered)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    unique_customers = filtered['customer_id'].nunique()

    # Previous period
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    delta = end_dt - start_dt
    prev_end = start_dt - timedelta(days=1)
    prev_start = prev_end - delta

    mask_prev = (data['orders']['order_date'] >= prev_start) & (
        data['orders']['order_date'] <= prev_end)
    prev = data['orders'][mask_prev]

    prev_revenue = prev['total_amount'].sum()
    prev_orders = len(prev)
    prev_aov = prev_revenue / prev_orders if prev_orders > 0 else 0
    prev_customers = prev['customer_id'].nunique()

    def calc_trend(curr, prev):
        return ((curr - prev) / prev * 100) if prev > 0 else (100.0 if curr > 0 else 0.0)

    # Monthly revenue trend
    monthly = filtered.groupby(filtered['order_date'].dt.to_period('M'))[
        'total_amount'].sum().reset_index()
    monthly['order_date'] = monthly['order_date'].astype(str)

    revenue_fig = go.Figure()
    revenue_fig.add_trace(go.Scatter(
        x=monthly['order_date'], y=monthly['total_amount'], mode='lines+markers', name='Revenue',
        line=dict(color=COLORS['primary'], width=4),
        marker=dict(size=12, color=COLORS['primary'], line=dict(
            color='white', width=2)),
        fill='tozeroy', fillcolor='rgba(102, 126, 234, 0.1)',
        hovertemplate='<b style="font-size:14px">%{x}</b><br><br>' +
                      '<span style="color:#667eea">●</span> Revenue: <b>$%{y:,.2f}</b><extra></extra>'
    ))
    revenue_fig.update_layout(
        title={'text': "📈 Monthly Revenue Trend", 'font': {
            'size': 20, 'color': COLORS['text_primary']}},
        xaxis_title="Month", yaxis_title="Revenue ($)", template="plotly_white",
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=60, b=40, l=60, r=40)
    )
    apply_hover_style(revenue_fig)

    # Channel distribution
    channel_rev = filtered.groupby('channel_name')[
        'total_amount'].sum().reset_index()
    channel_fig = px.pie(channel_rev, values='total_amount', names='channel_name',
                         title="🛒 Revenue by Sales Channel", hole=0.4,
                         color_discrete_sequence=['#667eea', '#10b981', '#f59e0b', '#06b6d4', '#ef4444'])
    channel_fig.update_traces(
        textposition='inside', textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br><br>Revenue: <b>$%{value:,.2f}</b><br>Share: <b>%{percent}</b><extra></extra>'
    )
    channel_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(channel_fig)

    return html.Div([
        # KPI Cards
        html.Div([
            create_kpi_card("Total Revenue", f"${total_revenue:,.2f}", f"{total_orders} orders",
                            calc_trend(total_revenue, prev_revenue), "vs prev", COLORS['success'], "💵"),
            create_kpi_card("Avg Order Value", f"${avg_order_value:.2f}", "per order",
                            calc_trend(avg_order_value, prev_aov), "vs prev", COLORS['primary'], "🪙"),
            create_kpi_card("Total Orders", f"{total_orders:,}", f"{unique_customers} customers",
                            calc_trend(total_orders, prev_orders), "vs prev", COLORS['info'], "📦"),
            create_kpi_card("Active Customers", f"{unique_customers:,}", "unique customers",
                            calc_trend(unique_customers, prev_customers), "vs prev", COLORS['warning'], "👪")
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(240px, 1fr))', 'gap': '24px', 'marginBottom': '40px'}),

        # Charts
        html.Div([
            dcc.Graph(figure=revenue_fig, config={'displayModeBar': False})
        ], style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px',
                  'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)', 'marginBottom': '30px'}),

        html.Div([
            html.Div([dcc.Graph(figure=channel_fig, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '24px'})
    ])


# ============== SALES & CHANNELS TAB ==============
def render_sales_tab(data, start_date, end_date):
    mask = (data['orders']['order_date'] >= start_date) & (
        data['orders']['order_date'] <= end_date)
    filtered = data['orders'][mask]

    # Channel performance
    channel_perf = filtered.groupby(['channel_name', 'commission_rate']).agg({
        'total_amount': 'sum', 'channel_id': 'count'
    }).reset_index()
    channel_perf.columns = ['channel_name',
                            'commission_rate', 'gross_revenue', 'order_count']
    channel_perf['net_revenue'] = channel_perf['gross_revenue'] * \
        (1 - channel_perf['commission_rate'])
    channel_perf['avg_order_value'] = channel_perf['gross_revenue'] / \
        channel_perf['order_count']

    total_gross = channel_perf['gross_revenue'].sum()
    total_net = channel_perf['net_revenue'].sum()
    total_orders = channel_perf['order_count'].sum()

    # Gross vs Net Revenue Bar Chart
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        name='Gross Revenue', x=channel_perf['channel_name'], y=channel_perf['gross_revenue'],
        marker_color='#3498db',
        hovertemplate='<b>%{x}</b><br><br><span style="color:#3498db">●</span> Gross Revenue: <b>$%{y:,.2f}</b><extra></extra>'
    ))
    bar_fig.add_trace(go.Bar(
        name='Net Revenue', x=channel_perf['channel_name'], y=channel_perf['net_revenue'],
        marker_color='#2ecc71',
        hovertemplate='<b>%{x}</b><br><br><span style="color:#2ecc71">●</span> Net Revenue: <b>$%{y:,.2f}</b><extra></extra>'
    ))
    bar_fig.update_layout(
        title={'text': "💰 Gross vs Net Revenue by Channel", 'font': {'size': 20}},
        barmode='group', template="plotly_white", paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1)
    )
    apply_hover_style(bar_fig)

    # Commission Impact Waterfall
    waterfall_fig = go.Figure(go.Waterfall(
        name="Revenue", orientation="v",
        x=["Gross Revenue", "Commissions", "Net Revenue"],
        y=[total_gross, -(total_gross - total_net), total_net],
        measure=["absolute", "relative", "total"],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#e74c3c"}},
        increasing={"marker": {"color": "#2ecc71"}},
        totals={"marker": {"color": "#3498db"}},
        hovertemplate='<b>%{x}</b><br><br>Amount: <b>$%{y:,.2f}</b><extra></extra>'
    ))
    waterfall_fig.update_layout(title={'text': "📊 Commission Impact Analysis", 'font': {'size': 20}},
                                template="plotly_white", paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(waterfall_fig)

    # Order Volume by Channel
    order_fig = px.bar(channel_perf.sort_values('order_count', ascending=True),
                       x='order_count', y='channel_name', orientation='h',
                       title="📦 Order Volume by Channel", color='order_count',
                       color_continuous_scale=[[0, '#e0e7ff'], [1, '#3498db']])
    order_fig.update_traces(
        hovertemplate='<b>%{y}</b><br><br>Orders: <b>%{x:,}</b><extra></extra>'
    )
    order_fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(order_fig)

    # Prepare table data
    table_df = channel_perf.copy()
    table_df['gross_revenue'] = table_df['gross_revenue'].apply(
        lambda x: f"${x:,.2f}")
    table_df['net_revenue'] = table_df['net_revenue'].apply(
        lambda x: f"${x:,.2f}")
    table_df['commission_rate'] = table_df['commission_rate'].apply(
        lambda x: f"{x*100:.1f}%")
    table_df['order_count'] = table_df['order_count'].apply(lambda x: f"{x:,}")
    table_df['avg_order_value'] = table_df['avg_order_value'].apply(
        lambda x: f"${x:,.2f}")

    columns_config = [
        {'name': 'Channel', 'id': 'channel_name'},
        {'name': 'Gross Revenue', 'id': 'gross_revenue'},
        {'name': 'Net Revenue', 'id': 'net_revenue'},
        {'name': 'Commission', 'id': 'commission_rate'},
        {'name': 'Orders', 'id': 'order_count'},
        {'name': 'AOV', 'id': 'avg_order_value'}
    ]

    return html.Div([
        # Metrics
        html.Div([
            create_metric_card("Total Gross Revenue",
                               f"${total_gross:,.2f}", "💵", TAB_COLORS['sales']),
            create_metric_card("Total Net Revenue",
                               f"${total_net:,.2f}", "💰", COLORS['success']),
            create_metric_card(
                "Total Orders", f"{total_orders:,}", "📦", COLORS['info']),
            create_metric_card(
                "Avg Commission", f"{((total_gross-total_net)/total_gross*100):.1f}%", "📉", COLORS['warning'])
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px', 'marginBottom': '30px'}),

        # Charts Row 1
        html.Div([
            html.Div([dcc.Graph(figure=bar_fig, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),
            html.Div([dcc.Graph(figure=waterfall_fig, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '30px'}),

        # Charts Row 2
        html.Div([
            html.Div([dcc.Graph(figure=order_fig, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),
            html.Div([
                html.H3("Channel Performance Details", style={
                        'marginBottom': '15px', 'color': COLORS['text_primary']}),
                create_styled_table(table_df, columns_config, 'sales')
            ], style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '24px'})
    ])


# ============== PRODUCTS TAB ==============
def render_products_tab(data, start_date, end_date):
    mask = (data['products']['order_date'] >= start_date) & (
        data['products']['order_date'] <= end_date)
    filtered = data['products'][mask]

    # Product aggregations
    product_stats = filtered.groupby('sku').agg({
        'quantity': 'sum', 'unit_price': 'mean', 'order_id': 'nunique'
    }).reset_index()
    product_stats.columns = [
        'sku', 'total_quantity', 'avg_price', 'order_count']
    product_stats['revenue'] = product_stats['total_quantity'] * \
        product_stats['avg_price']
    product_stats = product_stats.sort_values('revenue', ascending=False)

    total_revenue = product_stats['revenue'].sum()
    total_quantity = product_stats['total_quantity'].sum()
    total_orders = filtered['order_id'].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0

    # Top 10 Products by Revenue
    top10 = product_stats.head(10)
    top_fig = px.bar(top10, x='sku', y='revenue', title="📦 Top 10 Products by Revenue",
                     color='revenue', color_continuous_scale=[[0, '#fecaca'], [0.5, '#f87171'], [1, '#dc2626']])
    top_fig.update_traces(
        hovertemplate='<b>%{x}</b><br><br>Revenue: <b>$%{y:,.2f}</b><extra></extra>'
    )
    top_fig.update_layout(
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45)
    apply_hover_style(top_fig)

    # Pareto Chart (80/20 Analysis)
    product_stats_sorted = product_stats.sort_values(
        'revenue', ascending=False).reset_index(drop=True)
    product_stats_sorted['cumulative_revenue'] = product_stats_sorted['revenue'].cumsum(
    )
    product_stats_sorted['cumulative_pct'] = product_stats_sorted['cumulative_revenue'] / \
        total_revenue * 100
    top20 = product_stats_sorted.head(20)

    pareto_fig = go.Figure()
    pareto_fig.add_trace(go.Bar(
        x=top20['sku'], y=top20['revenue'], name='Revenue',
        marker_color='#e74c3c',
        hovertemplate='<b>%{x}</b><br><br><span style="color:#e74c3c">●</span> Revenue: <b>$%{y:,.2f}</b><extra></extra>'
    ))
    pareto_fig.add_trace(go.Scatter(
        x=top20['sku'], y=top20['cumulative_pct'], name='Cumulative %',
        yaxis='y2', mode='lines+markers', line=dict(color='#2c3e50', width=3),
        hovertemplate='<b>%{x}</b><br><br><span style="color:#2c3e50">●</span> Cumulative: <b>%{y:.1f}%</b><extra></extra>'
    ))
    pareto_fig.add_hline(y=80, line_dash="dash", line_color="gray",
                         annotation_text="80% threshold", yref='y2')
    pareto_fig.update_layout(
        title={
            'text': "📊 Revenue Pareto Analysis (80/20 Rule)", 'font': {'size': 20}},
        yaxis=dict(title='Revenue ($)'), yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 105]),
        template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    apply_hover_style(pareto_fig)

    # Quantity vs Revenue Scatter
    scatter_fig = px.scatter(product_stats.head(50), x='total_quantity', y='revenue', size='order_count',
                             color='avg_price', hover_name='sku', title="🎯 Quantity vs Revenue Analysis",
                             color_continuous_scale='RdYlGn')
    scatter_fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br><br>' +
                      'Quantity: <b>%{x:,}</b><br>' +
                      'Revenue: <b>$%{y:,.2f}</b><br>' +
                      'Avg Price: <b>$%{marker.color:.2f}</b><extra></extra>'
    )
    scatter_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(scatter_fig)

    # Prepare table data
    table_df = product_stats.head(15).copy()
    table_df['total_quantity'] = table_df['total_quantity'].apply(
        lambda x: f"{x:,}")
    table_df['revenue'] = table_df['revenue'].apply(lambda x: f"${x:,.2f}")
    table_df['avg_price'] = table_df['avg_price'].apply(lambda x: f"${x:.2f}")
    table_df['order_count'] = table_df['order_count'].apply(lambda x: f"{x:,}")

    columns_config = [
        {'name': 'SKU', 'id': 'sku'},
        {'name': 'Quantity Sold', 'id': 'total_quantity'},
        {'name': 'Revenue', 'id': 'revenue'},
        {'name': 'Avg Price', 'id': 'avg_price'},
        {'name': 'Orders', 'id': 'order_count'}
    ]

    return html.Div([
        # Metrics
        html.Div([
            create_metric_card(
                "Total Revenue", f"${total_revenue:,.2f}", "💰", TAB_COLORS['products']),
            create_metric_card(
                "Units Sold", f"{total_quantity:,}", "📦", COLORS['info']),
            create_metric_card("Avg Order Value",
                               f"${aov:.2f}", "🛒", COLORS['success']),
            create_metric_card(
                "Unique SKUs", f"{len(product_stats):,}", "🏷️", COLORS['warning'])
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px', 'marginBottom': '30px'}),

        # Pareto Chart
        html.Div([dcc.Graph(figure=pareto_fig, config={'displayModeBar': False})],
                 style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '30px'}),

        # Charts Row
        html.Div([
            html.Div([dcc.Graph(figure=top_fig, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),
            html.Div([dcc.Graph(figure=scatter_fig, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '30px'}),

        # Table
        html.Div([
            html.H3("Top Selling Products", style={
                    'marginBottom': '15px', 'color': COLORS['text_primary']}),
            create_styled_table(table_df, columns_config, 'products')
        ], style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px'})
    ])


# ============== INVENTORY TAB ==============
def render_inventory_tab(data, start_date, end_date):
    inv = data['inventory']
    latest_date = inv['snapshot_date'].max()
    latest_inv = inv[inv['snapshot_date'] == latest_date]

    # Get average prices from products
    products = data['products']
    avg_prices = products.groupby('sku')['unit_price'].mean().reset_index()
    avg_prices.columns = ['sku', 'avg_price']

    # Warehouse distribution
    warehouse_dist = latest_inv.groupby('warehouse_id').agg({
        'sku': 'nunique', 'quantity_on_hand': 'sum'
    }).reset_index()
    warehouse_dist.columns = ['warehouse_id', 'unique_skus', 'total_units']

    # Inventory value
    inv_with_price = latest_inv.merge(avg_prices, on='sku', how='left')
    inv_with_price['value'] = inv_with_price['quantity_on_hand'] * \
        inv_with_price['avg_price'].fillna(0)
    warehouse_value = inv_with_price.groupby('warehouse_id').agg({
        'value': 'sum', 'sku': 'nunique'
    }).reset_index()
    warehouse_value.columns = ['warehouse_id', 'inventory_value', 'sku_count']

    total_units = warehouse_dist['total_units'].sum()
    total_value = warehouse_value['inventory_value'].sum()
    total_skus = latest_inv['sku'].nunique()

    # Low stock items
    low_stock = latest_inv[latest_inv['quantity_on_hand'] < 10]
    low_stock_count = len(low_stock)

    # Warehouse Distribution Pie
    warehouse_pie = px.pie(warehouse_dist, values='total_units', names='warehouse_id',
                           title="🏭 Stock Distribution by Warehouse", hole=0.4,
                           color_discrete_sequence=['#27ae60', '#2ecc71', '#1abc9c', '#16a085'])
    warehouse_pie.update_traces(
        textposition='inside', textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br><br>Units: <b>%{value:,}</b><br>Share: <b>%{percent}</b><extra></extra>'
    )
    warehouse_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(warehouse_pie)

    # Inventory Value Bar
    value_bar = px.bar(warehouse_value, x='warehouse_id', y='inventory_value',
                       title="💵 Inventory Value by Warehouse", color='inventory_value',
                       color_continuous_scale=[[0, '#d1fae5'], [1, '#059669']])
    value_bar.update_traces(
        hovertemplate='<b>%{x}</b><br><br>Value: <b>$%{y:,.2f}</b><extra></extra>'
    )
    value_bar.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(value_bar)

    # Inventory Trend Over Time
    inv_trend = inv.groupby('snapshot_date')[
        'quantity_on_hand'].sum().reset_index()
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=inv_trend['snapshot_date'], y=inv_trend['quantity_on_hand'],
        mode='lines+markers', fill='tozeroy', fillcolor='rgba(39, 174, 96, 0.1)',
        line=dict(color='#27ae60', width=3), marker=dict(size=8),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br><br><span style="color:#27ae60">●</span> Stock: <b>%{y:,.0f}</b> units<extra></extra>'
    ))
    trend_fig.update_layout(title={'text': "📈 Inventory Levels Over Time", 'font': {'size': 20}},
                            xaxis_title="Date", yaxis_title="Total Units",
                            template="plotly_white", paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(trend_fig)

    # Prepare low stock table
    low_stock_merged = low_stock.merge(avg_prices, on='sku', how='left')
    table_df = low_stock_merged.head(15).copy()
    table_df['avg_price'] = table_df['avg_price'].apply(
        lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
    table_df['quantity_on_hand'] = table_df['quantity_on_hand'].apply(
        lambda x: f"{x:,}")

    columns_config = [
        {'name': 'SKU', 'id': 'sku'},
        {'name': 'Warehouse', 'id': 'warehouse_id'},
        {'name': 'Quantity', 'id': 'quantity_on_hand'},
        {'name': 'Avg Price', 'id': 'avg_price'}
    ]

    return html.Div([
        # Metrics
        html.Div([
            create_metric_card(
                "Total Units", f"{total_units:,}", "📦", TAB_COLORS['inventory']),
            create_metric_card("Inventory Value",
                               f"${total_value:,.2f}", "💰", COLORS['success']),
            create_metric_card(
                "Unique SKUs", f"{total_skus:,}", "🏷️", COLORS['info']),
            create_metric_card("Low Stock Items",
                               f"{low_stock_count}", "⚠️", COLORS['danger'])
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px', 'marginBottom': '30px'}),

        # Alert Box
        html.Div([
            html.Strong("⚠️ Low Stock Alert: "),
            html.Span(
                f"{low_stock_count} SKUs are below the 10-unit threshold")
        ], style={'backgroundColor': '#fff3cd', 'borderLeft': '4px solid #ffc107', 'padding': '15px',
                  'borderRadius': '4px', 'marginBottom': '30px'}) if low_stock_count > 0 else html.Div(),

        # Trend Chart
        html.Div([dcc.Graph(figure=trend_fig, config={'displayModeBar': False})],
                 style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '30px'}),

        # Charts Row
        html.Div([
            html.Div([dcc.Graph(figure=warehouse_pie, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),
            html.Div([dcc.Graph(figure=value_bar, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '30px'}),

        # Low Stock Table
        html.Div([
            html.H3("🚨 Low Stock Items (< 10 units)", style={
                    'marginBottom': '15px', 'color': COLORS['text_primary']}),
            create_styled_table(table_df, columns_config, 'inventory')
        ], style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px'})
    ])


# ============== CUSTOMERS TAB ==============
def render_customers_tab(data, start_date, end_date):
    mask = (data['customers']['order_date'] >= start_date) & (
        data['customers']['order_date'] <= end_date)
    filtered = data['customers'][mask].dropna(subset=['order_date'])

    # Geographic distribution
    geo_dist = filtered.groupby(['state', 'city']).agg({
        'customer_id': 'nunique', 'total_amount': 'sum', 'order_date': 'count'
    }).reset_index()
    geo_dist.columns = ['state', 'city',
                        'customer_count', 'total_sales', 'order_count']
    geo_dist = geo_dist.sort_values('total_sales', ascending=False)

    # State-level aggregation
    state_sales = geo_dist.groupby('state').agg({
        'customer_count': 'sum', 'total_sales': 'sum', 'order_count': 'sum'
    }).reset_index().sort_values('total_sales', ascending=False)

    total_customers = filtered['customer_id'].nunique()
    total_sales = filtered['total_amount'].sum()
    avg_per_customer = total_sales / total_customers if total_customers > 0 else 0

    # New customer acquisition
    signup_mask = (data['customers']['signup_date'] >= start_date) & (
        data['customers']['signup_date'] <= end_date)
    new_customers = data['customers'][signup_mask].drop_duplicates(
        'customer_id')
    new_customers['signup_month'] = new_customers['signup_date'].dt.to_period(
        'M').astype(str)
    acquisition = new_customers.groupby(
        'signup_month').size().reset_index(name='new_customers')

    # Top States Bar Chart
    top_states = state_sales.head(10)
    state_fig = px.bar(top_states.sort_values('total_sales'), x='total_sales', y='state', orientation='h',
                       title="🗺️ Top 10 States by Sales", color='total_sales',
                       color_continuous_scale=[[0, '#e9d5ff'], [1, '#9333ea']])
    state_fig.update_traces(
        hovertemplate='<b>%{y}</b><br><br>Sales: <b>$%{x:,.2f}</b><extra></extra>'
    )
    state_fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(state_fig)

    # Customer Acquisition Trend
    acq_fig = go.Figure()
    acq_fig.add_trace(go.Bar(
        x=acquisition['signup_month'], y=acquisition['new_customers'],
        marker_color='#9b59b6',
        hovertemplate='<b>%{x}</b><br><br><span style="color:#9b59b6">●</span> New Customers: <b>%{y:,}</b><extra></extra>'
    ))
    acq_fig.update_layout(title={'text': "📈 New Customer Acquisition", 'font': {'size': 20}},
                          xaxis_title="Month", yaxis_title="New Customers",
                          template="plotly_white", paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(acq_fig)

    # Customer Distribution by State (Treemap)
    treemap_fig = px.treemap(state_sales.head(15), path=['state'], values='total_sales',
                             title="🌳 Sales Distribution by State", color='total_sales',
                             color_continuous_scale='Purples')
    treemap_fig.update_traces(
        hovertemplate='<b>%{label}</b><br><br>Sales: <b>$%{value:,.2f}</b><extra></extra>'
    )
    treemap_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(treemap_fig)

    # Prepare table data
    table_df = geo_dist.head(20).copy()
    table_df['customer_count'] = table_df['customer_count'].apply(
        lambda x: f"{x:,}")
    table_df['total_sales'] = table_df['total_sales'].apply(
        lambda x: f"${x:,.2f}")
    table_df['order_count'] = table_df['order_count'].apply(lambda x: f"{x:,}")

    columns_config = [
        {'name': 'State', 'id': 'state'},
        {'name': 'City', 'id': 'city'},
        {'name': 'Customers', 'id': 'customer_count'},
        {'name': 'Total Sales', 'id': 'total_sales'},
        {'name': 'Orders', 'id': 'order_count'}
    ]

    return html.Div([
        # Metrics
        html.Div([
            create_metric_card(
                "Total Customers", f"{total_customers:,}", "👥", TAB_COLORS['customers']),
            create_metric_card(
                "Total Sales", f"${total_sales:,.2f}", "💰", COLORS['success']),
            create_metric_card(
                "Avg per Customer", f"${avg_per_customer:.2f}", "🛒", COLORS['info']),
            create_metric_card(
                "New Customers", f"{len(new_customers):,}", "🆕", COLORS['warning'])
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px', 'marginBottom': '30px'}),

        # Charts Row 1
        html.Div([
            html.Div([dcc.Graph(figure=state_fig, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),
            html.Div([dcc.Graph(figure=acq_fig, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '30px'}),

        # Treemap
        html.Div([dcc.Graph(figure=treemap_fig, config={'displayModeBar': False})],
                 style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '30px'}),

        # Table
        html.Div([
            html.H3("Geographic Distribution", style={
                    'marginBottom': '15px', 'color': COLORS['text_primary']}),
            create_styled_table(table_df, columns_config, 'customers')
        ], style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px'})
    ])


# ============== PAYMENTS TAB ==============
def render_payments_tab(data, start_date, end_date):
    mask = (data['transactions']['transaction_date'] >= start_date) & (
        data['transactions']['transaction_date'] <= end_date)
    filtered = data['transactions'][mask]
    successful = filtered[filtered['status'] == 'SUCCESS']

    # Payment method distribution
    payment_dist = successful.groupby('payment_method').agg({
        'amount': ['sum', 'count', 'mean']
    }).reset_index()
    payment_dist.columns = ['payment_method',
                            'total_amount', 'transaction_count', 'avg_amount']

    total_amount = payment_dist['total_amount'].sum()
    total_transactions = payment_dist['transaction_count'].sum()
    avg_transaction = total_amount / total_transactions if total_transactions > 0 else 0

    # Payment Method Pie
    payment_pie = px.pie(payment_dist, values='total_amount', names='payment_method',
                         title="💳 Payment Method Distribution", hole=0.5,
                         color_discrete_sequence=['#06b6d4', '#f59e0b', '#10b981', '#667eea', '#ef4444'])
    payment_pie.update_traces(
        textposition='outside', textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br><br>Amount: <b>$%{value:,.2f}</b><br>Share: <b>%{percent}</b><extra></extra>'
    )
    payment_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(payment_pie)

    # Transaction Volume Bar
    volume_bar = px.bar(payment_dist.sort_values('transaction_count', ascending=True),
                        x='transaction_count', y='payment_method', orientation='h',
                        title="📊 Transaction Volume by Method", color='transaction_count',
                        color_continuous_scale=[[0, '#cffafe'], [1, '#0891b2']])
    volume_bar.update_traces(
        hovertemplate='<b>%{y}</b><br><br>Transactions: <b>%{x:,}</b><extra></extra>'
    )
    volume_bar.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(volume_bar)

    # Daily Cash Flow
    daily_flow = successful.groupby(successful['transaction_date'].dt.date).agg({
        'amount': 'sum', 'order_id': 'count'
    }).reset_index()
    daily_flow.columns = ['date', 'daily_total', 'transaction_count']

    cashflow_fig = go.Figure()
    cashflow_fig.add_trace(go.Scatter(
        x=daily_flow['date'], y=daily_flow['daily_total'],
        mode='lines+markers', fill='tozeroy', fillcolor='rgba(6, 182, 212, 0.1)',
        line=dict(color='#06b6d4', width=3), marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br><br><span style="color:#06b6d4">●</span> Amount: <b>$%{y:,.2f}</b><extra></extra>'
    ))
    cashflow_fig.update_layout(title={'text': "📈 Daily Cash Flow", 'font': {'size': 20}},
                               xaxis_title="Date", yaxis_title="Amount ($)",
                               template="plotly_white", paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(cashflow_fig)

    # Average Transaction by Method
    avg_bar = px.bar(payment_dist.sort_values('avg_amount'), x='payment_method', y='avg_amount',
                     title="💵 Average Transaction by Method", color='avg_amount',
                     color_continuous_scale=[[0, '#fef3c7'], [1, '#d97706']])
    avg_bar.update_traces(
        hovertemplate='<b>%{x}</b><br><br>Avg Amount: <b>$%{y:,.2f}</b><extra></extra>'
    )
    avg_bar.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
    apply_hover_style(avg_bar)

    # Prepare table data
    table_df = payment_dist.copy()
    table_df['total_amount'] = table_df['total_amount'].apply(
        lambda x: f"${x:,.2f}")
    table_df['transaction_count'] = table_df['transaction_count'].apply(
        lambda x: f"{x:,}")
    table_df['avg_amount'] = table_df['avg_amount'].apply(
        lambda x: f"${x:.2f}")

    columns_config = [
        {'name': 'Payment Method', 'id': 'payment_method'},
        {'name': 'Total Amount', 'id': 'total_amount'},
        {'name': 'Transactions', 'id': 'transaction_count'},
        {'name': 'Avg Amount', 'id': 'avg_amount'}
    ]

    return html.Div([
        # Metrics
        html.Div([
            create_metric_card(
                "Total Processed", f"${total_amount:,.2f}", "💰", TAB_COLORS['payments']),
            create_metric_card(
                "Transactions", f"{total_transactions:,}", "📊", COLORS['info']),
            create_metric_card(
                "Avg Transaction", f"${avg_transaction:.2f}", "💵", COLORS['success']),
            create_metric_card("Payment Methods",
                               f"{len(payment_dist)}", "💳", COLORS['warning'])
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px', 'marginBottom': '30px'}),

        # Cash Flow Chart
        html.Div([dcc.Graph(figure=cashflow_fig, config={'displayModeBar': False})],
                 style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '30px'}),

        # Charts Row
        html.Div([
            html.Div([dcc.Graph(figure=payment_pie, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),
            html.Div([dcc.Graph(figure=volume_bar, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '30px'}),

        # Charts Row 2
        html.Div([
            html.Div([dcc.Graph(figure=avg_bar, config={'displayModeBar': False})],
                     style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),
            html.Div([
                html.H3("Payment Method Summary", style={
                        'marginBottom': '15px', 'color': COLORS['text_primary']}),
                create_styled_table(table_df, columns_config, 'payments')
            ], style={'backgroundColor': COLORS['card_bg'], 'padding': '20px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '24px'})
    ])


# ============== DOWNLOAD CALLBACK ==============
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    [State('date-range', 'start_date'), State('date-range', 'end_date')],
    prevent_initial_call=True,
)
def download_csv(n_clicks, start_date, end_date):
    data = get_data()
    mask = (data['orders']['order_date'] >= start_date) & (
        data['orders']['order_date'] <= end_date)
    filtered = data['orders'][mask]
    return dcc.send_data_frame(filtered.to_csv, f"sales_data_{start_date}_{end_date}.csv", index=False)


if __name__ == '__main__':
    print("🚀 Starting Dash Dashboard...")
    print("📊 Dashboard available at http://127.0.0.1:8050")
    print("\n📑 Available Tabs:")
    print("   • Overview - KPIs and revenue trends")
    print("   • Sales & Channels - Channel performance analysis")
    print("   • Products - Product performance and Pareto analysis")
    print("   • Inventory - Stock levels and low stock alerts")
    print("   • Customers - Geographic and acquisition analysis")
    print("   • Payments - Payment method distribution and cash flow")
    app.run(debug=True, port=8050)
