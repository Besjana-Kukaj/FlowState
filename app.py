import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import json
import os

# Page config
st.set_page_config(
    page_title="FlowState - Real-Time Cash Flow Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling with dynamic background
st.markdown("""
<style>
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid #3B82F6;
    }
    .danger-alert {
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .health-excellent { color: #10B981; }
    .health-good { color: #F59E0B; }
    .health-poor { color: #EF4444; }
    .big-number { font-size: 2.5rem; font-weight: bold; }
    .success-message { 
        background-color: #F0FDF4; 
        border: 1px solid #BBF7D0; 
        border-radius: 0.5rem; 
        padding: 0.5rem; 
        margin: 0.5rem 0; 
        color: #15803D;
    }
    .main-header {
        background: linear-gradient(90deg, #1E40AF, #3B82F6);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .balance-positive {
        background: linear-gradient(135deg, #F0FDF4, #DCFCE7);
        border-left: 4px solid #10B981;
    }
    .balance-caution {
        background: linear-gradient(135deg, #FFFBEB, #FEF3C7);
        border-left: 4px solid #F59E0B;
    }
    .balance-danger {
        background: linear-gradient(135deg, #FEF2F2, #FECACA);
        border-left: 4px solid #EF4444;
    }
    .stApp {
        background: var(--background-color);
    }
</style>
""", unsafe_allow_html=True)



def save_data():
    """Save current data to JSON file"""
    data = {
        'transactions': st.session_state.transactions_df.to_dict('records'),
        'current_balance': st.session_state.current_balance,
        'next_id': st.session_state.next_id
    }
    
    with open('cashflow_data.json', 'w') as f:
        json.dump(data, f, default=str)

def load_data():
    """Load data from JSON file"""
    if os.path.exists('cashflow_data.json'):
        try:
            with open('cashflow_data.json', 'r') as f:
                data = json.load(f)
            
            # Convert dates back to datetime
            for transaction in data['transactions']:
                transaction['date'] = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
            
            return pd.DataFrame(data['transactions']), data['current_balance'], data['next_id']
        except Exception as e:
            st.error(f"Error loading data: {e}")
    
    # Return default values if file doesn't exist or error
    return pd.DataFrame(columns=['id', 'type', 'amount', 'date', 'description', 'status', 'probability']), 0, 1

def initialize_session_state():
    """Initialize session state variables"""
    if 'transactions_df' not in st.session_state:
        # Load data from file or start with empty dataframe
        st.session_state.transactions_df, st.session_state.current_balance, st.session_state.next_id = load_data()

def add_transaction(trans_type, amount, date, description, status, probability):
    """Add a new transaction to the dataframe"""
    new_transaction = pd.DataFrame([{
        'id': st.session_state.next_id,
        'type': trans_type,
        'amount': amount,
        'date': date,
        'description': description,
        'status': status,
        'probability': probability
    }])
    
    st.session_state.transactions_df = pd.concat([st.session_state.transactions_df, new_transaction], ignore_index=True)
    st.session_state.next_id += 1
    save_data()  # Save after adding transaction

def update_transaction(transaction_id, trans_type, amount, date, description, status, probability):
    """Update an existing transaction"""
    idx = st.session_state.transactions_df[st.session_state.transactions_df['id'] == transaction_id].index[0]
    st.session_state.transactions_df.loc[idx] = {
        'id': transaction_id,
        'type': trans_type,
        'amount': amount,
        'date': date,
        'description': description,
        'status': status,
        'probability': probability
    }
    save_data()  # Save after updating transaction

def delete_transaction(transaction_id):
    """Delete a transaction"""
    st.session_state.transactions_df = st.session_state.transactions_df[
        st.session_state.transactions_df['id'] != transaction_id
    ].reset_index(drop=True)
    save_data()  # Save after deleting transaction

def apply_scenarios(df, scenario_type, delay_days=0, what_if_expense=0):
    """Apply scenario modifications to transactions"""
    df_scenario = df.copy()
    
    # Check if DataFrame is empty
    if df_scenario.empty:
        return df_scenario
    
    if scenario_type == "Payment Delays":
        # Delay pending income by specified days
        mask = (df_scenario['type'] == 'income') & (df_scenario['status'] == 'pending')
        df_scenario.loc[mask, 'date'] = df_scenario.loc[mask, 'date'] + timedelta(days=delay_days)
    
    if what_if_expense > 0:
        # Add what-if expense
        new_expense = pd.DataFrame([{
            "id": 9999,
            "type": "expense",
            "amount": what_if_expense,
            "date": datetime.now().date() + timedelta(days=3),
            "description": "What-If Expense",
            "status": "projected",
            "probability": 100
        }])
        df_scenario = pd.concat([df_scenario, new_expense], ignore_index=True)
    
    return df_scenario.sort_values('date').reset_index(drop=True)

def calculate_cash_flow_projection(df, starting_balance):
    """Calculate daily cash flow projection"""
    
    # Check if DataFrame is empty
    if df.empty:
        # Return just the starting balance for today
        return pd.DataFrame([{
            'date': datetime.now().date(),
            'balance': starting_balance,
            'daily_income': 0,
            'daily_expenses': 0,
            'net_flow': 0
        }])
    
    # Create date range for projection
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    # Check for NaT values (which can happen with empty DataFrames)
    if pd.isna(min_date) or pd.isna(max_date):
        return pd.DataFrame([{
            'date': datetime.now().date(),
            'balance': starting_balance,
            'daily_income': 0,
            'daily_expenses': 0,
            'net_flow': 0
        }])
    
    # Group transactions by date
    daily_flows = []
    current_balance = starting_balance
    
    # Add starting balance
    daily_flows.append({
        'date': datetime.now().date(),
        'balance': current_balance,
        'daily_income': 0,
        'daily_expenses': 0,
        'net_flow': 0
    })
    
    # Calculate daily balances
    for single_date in pd.date_range(min_date, max_date, freq='D'):
        date = single_date.date()
        day_transactions = df[df['date'] == date]
        
        daily_income = day_transactions[day_transactions['type'] == 'income']['amount'].sum()
        daily_expenses = day_transactions[day_transactions['type'] == 'expense']['amount'].sum()
        net_flow = daily_income - daily_expenses
        current_balance += net_flow
        
        daily_flows.append({
            'date': date,
            'balance': current_balance,
            'daily_income': daily_income,
            'daily_expenses': daily_expenses,
            'net_flow': net_flow
        })
    
    return pd.DataFrame(daily_flows)

def calculate_health_metrics(projection_df, current_balance):
    """Calculate key health metrics"""
    
    # Days until danger (balance goes negative)
    negative_days = projection_df[projection_df['balance'] < 0]
    days_until_danger = None
    if not negative_days.empty:
        danger_date = negative_days.iloc[0]['date']
        days_until_danger = (danger_date - datetime.now().date()).days
    
    # Monthly runway
    if len(projection_df) > 1:
        monthly_expenses = projection_df['daily_expenses'].sum() / len(projection_df) * 30
        monthly_runway = current_balance / monthly_expenses if monthly_expenses > 0 else float('inf')
    else:
        # If only one data point, assume no expenses
        monthly_runway = float('inf')
    
    # Health score calculation
    health_score = 100
    if days_until_danger is not None:
        if days_until_danger < 30:
            health_score = max(0, days_until_danger * 2)
        elif days_until_danger < 60:
            health_score = 60 + (days_until_danger - 30)
        else:
            health_score = 90
    
    # Trend direction
    if len(projection_df) > 1:
        recent_balances = projection_df['balance'].tail(5)
        trend_direction = recent_balances.iloc[-1] - recent_balances.iloc[0] if len(recent_balances) > 1 else 0
    else:
        trend_direction = 0
    
    return {
        'health_score': round(health_score),
        'days_until_danger': days_until_danger,
        'monthly_runway': round(monthly_runway, 1),
        'trend_direction': trend_direction,
        'min_balance': projection_df['balance'].min(),
        'current_balance': current_balance
    }

def get_health_color_class(score):
    """Get CSS class for health score color"""
    if score >= 80:
        return "health-excellent"
    elif score >= 60:
        return "health-good"
    else:
        return "health-poor"

def get_health_status(score):
    """Get health status text"""
    if score >= 80:
        return "Healthy 💚"
    elif score >= 60:
        return "Caution ⚠️"
    else:
        return "Critical 🚨"

def get_background_color(metrics):
    """Get background color based on financial health"""
    if metrics['health_score'] >= 80:
        return "#F0FDF4"  # Light green
    elif metrics['health_score'] >= 60:
        return "#FFFBEB"  # Light yellow
    else:
        return "#FEF2F2"  # Light red

def get_balance_card_class(metrics):
    """Get CSS class for balance card based on financial status"""
    if metrics['health_score'] >= 80:
        return "balance-positive"
    elif metrics['health_score'] >= 60:
        return "balance-caution"
    else:
        return "balance-danger"

def show_transaction_editor():
    """Show the transaction editor interface"""
    st.header("💼 Manage Transactions")
    
    # Add new transaction section
    with st.expander("➕ Add New Transaction", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            new_type = st.selectbox("Type", ["income", "expense"], key="new_type")
            new_amount = st.number_input("Amount ($)", min_value=0, value=1000, step=100, key="new_amount")
            new_date = st.date_input("Date", value=datetime.now().date(), key="new_date")
        
        with col2:
            new_description = st.text_input("Description", key="new_description")
            new_status = st.selectbox("Status", ["confirmed", "pending", "projected"], key="new_status")
            new_probability = st.slider("Probability (%)", 0, 100, 100, key="new_probability")
        
        if st.button("Add Transaction", type="primary"):
            if new_description.strip():
                add_transaction(new_type, new_amount, new_date, new_description, new_status, new_probability)
                st.markdown('<div class="success-message">✅ Transaction added successfully!</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.error("Please enter a description for the transaction.")
    
    # Edit existing transactions
    st.subheader("📝 Edit Existing Transactions")
    
    # Check if there are transactions to edit
    if st.session_state.transactions_df.empty:
        st.info("No transactions to edit. Add some transactions first!")
    else:
        # Show transactions in editable format
        df_display = st.session_state.transactions_df.copy()
        df_display['date'] = pd.to_datetime(df_display['date']).dt.date
        df_display = df_display.sort_values('date')
        
        for idx, row in df_display.iterrows():
            with st.expander(f"{row['description']} - ${row['amount']:,} ({row['date']})"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    edit_type = st.selectbox("Type", ["income", "expense"], 
                                           index=0 if row['type'] == 'income' else 1, 
                                           key=f"edit_type_{row['id']}")
                    edit_amount = st.number_input("Amount ($)", value=float(row['amount']), 
                                                min_value=0.0, step=100.0, 
                                                key=f"edit_amount_{row['id']}")
                    edit_date = st.date_input("Date", value=row['date'], 
                                            key=f"edit_date_{row['id']}")
                
                with col2:
                    edit_description = st.text_input("Description", value=row['description'], 
                                                    key=f"edit_desc_{row['id']}")
                    edit_status = st.selectbox("Status", ["confirmed", "pending", "projected"],
                                             index=["confirmed", "pending", "projected"].index(row['status']),
                                             key=f"edit_status_{row['id']}")
                    edit_probability = st.slider("Probability (%)", 0, 100, int(row['probability']), 
                                               key=f"edit_prob_{row['id']}")
                
                with col3:
                    st.write("") # spacing
                    if st.button("Update", key=f"update_{row['id']}", type="primary"):
                        update_transaction(row['id'], edit_type, edit_amount, edit_date, 
                                         edit_description, edit_status, edit_probability)
                        st.markdown('<div class="success-message">✅ Transaction updated!</div>', unsafe_allow_html=True)
                        st.rerun()
                    
                    if st.button("Delete", key=f"delete_{row['id']}", type="secondary"):
                        delete_transaction(row['id'])
                        st.markdown('<div class="success-message">🗑️ Transaction deleted!</div>', unsafe_allow_html=True)
                        st.rerun()

def show_balance_editor():
    """Show current balance editor"""
    st.header("💰 Current Balance")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        new_balance = st.number_input(
            "Update Current Balance ($)", 
            value=float(st.session_state.current_balance), 
            min_value=0.0, 
            step=1000.0,
            help="This is your actual current bank balance"
        )
    
    with col2:
        st.write("") # spacing
        if st.button("Update Balance", type="primary"):
            st.session_state.current_balance = new_balance
            save_data()  # Save after updating balance
            st.markdown('<div class="success-message">✅ Balance updated!</div>', unsafe_allow_html=True)
            st.rerun()

def show_quick_actions():
    """Show quick action buttons for common scenarios"""
    st.header("⚡ Quick Actions")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("💰 Add Income", type="primary", use_container_width=True):
            st.session_state.show_add_income = True
            st.rerun()
    
    with col2:
        if st.button("💸 Add Expense", type="primary", use_container_width=True):
            st.session_state.show_add_expense = True
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
            st.session_state.transactions_df = pd.DataFrame(columns=['id', 'type', 'amount', 'date', 'description', 'status', 'probability'])
            st.session_state.current_balance = 0
            st.session_state.next_id = 1
            save_data()  # Save after clearing data
            st.markdown('<div class="success-message">✅ All data cleared!</div>', unsafe_allow_html=True)
            st.rerun()
    
    with col4:
        if st.button("💾 Export Data", type="secondary", use_container_width=True):
            st.session_state.show_export = True
            st.rerun()
    
    with col5:
        if st.button("📥 Import Data", type="secondary", use_container_width=True):
            st.session_state.show_import = True
            st.rerun()

def show_quick_add_forms():
    """Show quick add forms for income/expense"""
    
    if st.session_state.get('show_add_income', False):
        with st.expander("💰 Quick Add Income", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount ($)", min_value=0, value=1000, step=100, key="quick_income_amount")
                description = st.text_input("Description", key="quick_income_desc")
            with col2:
                date = st.date_input("Date", value=datetime.now().date(), key="quick_income_date")
                probability = st.slider("Probability (%)", 0, 100, 100, key="quick_income_prob")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("Add Income", type="primary", key="add_income_btn"):
                    if description.strip():
                        add_transaction("income", amount, date, description, "projected", probability)
                        st.session_state.show_add_income = False
                        st.markdown('<div class="success-message">✅ Income added!</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.error("Please enter a description.")
            with col2:
                if st.button("Cancel", type="secondary", key="cancel_income"):
                    st.session_state.show_add_income = False
                    st.rerun()
    
    # Export data functionality
    if st.session_state.get('show_export', False):
        with st.expander("💾 Export Data", expanded=True):
            st.subheader("📤 Export Data")
            if st.button("Download JSON Backup", type="primary", key="download_backup_btn"):
                data = {
                    'transactions': st.session_state.transactions_df.to_dict('records'),
                    'current_balance': st.session_state.current_balance,
                    'next_id': st.session_state.next_id
                }
                st.download_button(
                    label="Download Backup File",
                    data=json.dumps(data, default=str, indent=2),
                    file_name=f"cashflow_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            if st.button("Close", type="secondary", key="close_export"):
                st.session_state.show_export = False
                st.rerun()
    
    # Import data functionality
    if st.session_state.get('show_import', False):
        with st.expander("📥 Import Data", expanded=True):
            st.subheader("📥 Import Data")
            uploaded_file = st.file_uploader("Choose a JSON backup file", type=['json'], key="import_uploader")
            if uploaded_file is not None:
                try:
                    data = json.load(uploaded_file)
                    
                    # Convert dates back to datetime
                    for transaction in data['transactions']:
                        transaction['date'] = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
                    
                    st.session_state.transactions_df = pd.DataFrame(data['transactions'])
                    st.session_state.current_balance = data['current_balance']
                    st.session_state.next_id = data['next_id']
                    save_data()
                    
                    st.markdown('<div class="success-message">✅ Data imported successfully!</div>', unsafe_allow_html=True)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error importing data: {e}")
            
            if st.button("Close", type="secondary", key="close_import"):
                st.session_state.show_import = False
                st.rerun()
    
    if st.session_state.get('show_add_expense', False):
        with st.expander("💸 Quick Add Expense", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount ($)", min_value=0, value=1000, step=100, key="quick_expense_amount")
                description = st.text_input("Description", key="quick_expense_desc")
            with col2:
                date = st.date_input("Date", value=datetime.now().date(), key="quick_expense_date")
                probability = st.slider("Probability (%)", 0, 100, 100, key="quick_expense_prob")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("Add Expense", type="primary", key="add_expense_btn"):
                    if description.strip():
                        add_transaction("expense", amount, date, description, "projected", probability)
                        st.session_state.show_add_expense = False
                        st.markdown('<div class="success-message">✅ Expense added!</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.error("Please enter a description.")
            with col2:
                if st.button("Cancel", type="secondary", key="cancel_expense"):
                    st.session_state.show_add_expense = False
                    st.rerun()

# Main App
def main():
    # Initialize session state
    initialize_session_state()
    
    # Process data for background color
    df_scenario = apply_scenarios(st.session_state.transactions_df, "Base Case", 0, 0)
    projection_df = calculate_cash_flow_projection(df_scenario, st.session_state.current_balance)
    metrics = calculate_health_metrics(projection_df, st.session_state.current_balance)
    
    # Set dynamic background color
    background_color = get_background_color(metrics)
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {background_color} !important;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Header with dynamic styling
    balance_class = get_balance_card_class(metrics)
    st.markdown(f"""
    <div class="main-header">
        <h1>💰 FlowState - Real-Time Cash Flow Dashboard</h1>
        <p><em>Real-time financial health monitoring for your business</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2 = st.tabs(["📊 Dashboard", "⚙️ Manage Data"])
    
    with tab2:
        show_quick_actions()
        st.divider()
        show_quick_add_forms()
        st.divider()
        show_balance_editor()
        st.divider()
        show_transaction_editor()
    
    with tab1:
        # Sidebar for scenario controls
        st.sidebar.header("🎛️ Scenario Planning")
        
        scenario_type = st.sidebar.selectbox(
            "Select Scenario",
            ["Base Case", "Payment Delays"]
        )
        
        delay_days = 0
        if scenario_type == "Payment Delays":
            delay_days = st.sidebar.slider(
                "Payment Delay (days)",
                min_value=0,
                max_value=60,
                value=15,
                help="How many days will pending payments be delayed?"
            )
        
        what_if_expense = st.sidebar.number_input(
            "What-If Expense ($)",
            min_value=0,
            max_value=100000,
            value=0,
            step=1000,
            help="Test the impact of a large expense"
        )
        
        # Process data with scenarios
        df_scenario = apply_scenarios(st.session_state.transactions_df, scenario_type, delay_days, what_if_expense)
        projection_df = calculate_cash_flow_projection(df_scenario, st.session_state.current_balance)
        metrics = calculate_health_metrics(projection_df, st.session_state.current_balance)
        
        # Critical Alert
        if metrics['days_until_danger'] is not None and metrics['days_until_danger'] < 30:
            st.markdown(f"""
            <div class="danger-alert">
                <h3>🚨 Cash Flow Alert!</h3>
                <p>Your balance will go negative in <strong>{metrics['days_until_danger']} days</strong> without action.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Top KPI Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            health_class = get_health_color_class(metrics['health_score'])
            health_status = get_health_status(metrics['health_score'])
            st.markdown(f"""
            <div class="metric-card">
                <h4>💓 Cash Flow Pulse</h4>
                <div class="big-number {health_class}">{metrics['health_score']}</div>
                <p>{health_status}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            danger_class = "health-poor" if metrics['days_until_danger'] and metrics['days_until_danger'] < 30 else "health-excellent"
            danger_value = metrics['days_until_danger'] if metrics['days_until_danger'] else "∞"
            st.markdown(f"""
            <div class="metric-card">
                <h4>📅 Days Until Danger</h4>
                <div class="big-number {danger_class}">{danger_value}</div>
                <p>{'days until negative' if metrics['days_until_danger'] else 'Safe runway'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            runway_value = metrics['monthly_runway'] if metrics['monthly_runway'] != float('inf') else "∞"
            st.markdown(f"""
            <div class="metric-card">
                <h4>🎯 Monthly Runway</h4>
                <div class="big-number health-good">{runway_value}</div>
                <p>months at current burn</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            trend_arrow = "↗️" if metrics['trend_direction'] > 0 else "↘️"
            trend_text = "Improving" if metrics['trend_direction'] > 0 else "Declining"
            trend_class = "health-excellent" if metrics['trend_direction'] > 0 else "health-poor"
            st.markdown(f"""
            <div class="metric-card">
                <h4>📈 Trend</h4>
                <div class="big-number {trend_class}">{trend_arrow}</div>
                <p>{trend_text}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts Row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Cash Flow Projection")
            
            fig_projection = go.Figure()
            fig_projection.add_trace(go.Scatter(
                x=projection_df['date'],
                y=projection_df['balance'],
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(59, 130, 246, 0.1)',
                line=dict(color='#3B82F6', width=3),
                name='Balance'
            ))
            
            # Add zero line
            fig_projection.add_hline(y=0, line_dash="dash", line_color="red", 
                                    annotation_text="Danger Zone", 
                                    annotation_position="bottom right")
            
            fig_projection.update_layout(
                height=400,
                showlegend=False,
                xaxis_title="Date",
                yaxis_title="Balance ($)",
                yaxis_tickformat="$,.0f"
            )
            
            st.plotly_chart(fig_projection, use_container_width=True)
        
        with col2:
            st.subheader("💰 Income vs Expenses")
            
            fig_flow = go.Figure()
            fig_flow.add_trace(go.Scatter(
                x=projection_df['date'],
                y=projection_df['daily_income'],
                mode='lines',
                line=dict(color='#10B981', width=3),
                name='Income'
            ))
            fig_flow.add_trace(go.Scatter(
                x=projection_df['date'],
                y=projection_df['daily_expenses'],
                mode='lines',
                line=dict(color='#EF4444', width=3),
                name='Expenses'
            ))
            
            fig_flow.update_layout(
                height=400,
                xaxis_title="Date",
                yaxis_title="Daily Amount ($)",
                yaxis_tickformat="$,.0f",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            
            st.plotly_chart(fig_flow, use_container_width=True)
        
        # Payment Risk Alerts
        if not df_scenario.empty:
            overdue_payments = df_scenario[
                (df_scenario['type'] == 'income') & 
                (df_scenario['status'] == 'pending') & 
                (df_scenario['date'] < datetime.now().date())
            ]
            
            if not overdue_payments.empty:
                st.subheader("⚠️ Payment Risk Alerts")
                
                for _, payment in overdue_payments.iterrows():
                    days_overdue = (datetime.now().date() - payment['date']).days
                    
                    with st.expander(f"🔴 {payment['description']} - {days_overdue} days overdue"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Amount:** ${payment['amount']:,}")
                            st.write(f"**Original Due Date:** {payment['date']}")
                            st.write(f"**Status:** {payment['status'].title()}")
                        with col2:
                            st.metric("Days Overdue", days_overdue)
        
        # Transaction Summary
        with st.expander("📋 Transaction Summary"):
            if st.session_state.transactions_df.empty:
                st.info("No transactions to display. Add some transactions first!")
            else:
                display_df = st.session_state.transactions_df.copy()
                display_df['amount_display'] = display_df.apply(
                    lambda row: f"${row['amount']:,}" if row['type'] == 'income' else f"-${row['amount']:,}", 
                    axis=1
                )
                st.dataframe(
                    display_df[['date', 'type', 'description', 'amount_display', 'status', 'probability']].sort_values('date'),
                    use_container_width=True,
                    column_config={
                        'amount_display': 'Amount',
                        'date': 'Date',
                        'type': 'Type',
                        'description': 'Description',
                        'status': 'Status',
                        'probability': 'Probability (%)'
                    }
                )

if __name__ == "__main__":
    main()