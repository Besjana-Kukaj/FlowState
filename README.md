# 💰 FlowState - Real-Time Cash Flow Dashboard

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**FlowState** is an intelligent cash flow management dashboard designed for small businesses and freelancers. Monitor your financial health in real-time, predict cash crunches before they happen, and make data-driven decisions with AI-powered bank statement processing.

## 🚀 Key Features

### 📊 **Real-Time Financial Health Monitoring**
- **Cash Flow Pulse Score**: 0-100 health rating with instant visual feedback
- **Days Until Danger**: Predictive alerts when your balance will go negative
- **Monthly Runway**: Calculate how long your current balance will last
- **Trend Analysis**: Track if your financial situation is improving or declining

### 🤖 **AI-Powered Bank Statement Processing**
- Upload PDF bank statements for automatic transaction extraction
- Powered by Google Gemini AI for intelligent categorization
- Smart description cleaning and duplicate detection
- Automatic income vs expense classification

### 🎛️ **Scenario Planning & Forecasting**
- **Payment Delay Modeling**: See impact of late client payments
- **What-If Analysis**: Test large expense scenarios
- **Interactive Projections**: Visualize multiple financial scenarios
- **Risk Alerts**: Get warned about overdue payments and cash flow risks

### 💼 **Complete Transaction Management**
- Add, edit, and delete transactions with probability scoring
- Support for confirmed, pending, and projected transactions
- Quick action buttons for common operations
- Comprehensive transaction history and filtering

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/flowstate.git
   cd flowstate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

The dashboard will open in your browser at `http://localhost:8501`

## 📋 Requirements

Create a `requirements.txt` file with these dependencies:

```
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
numpy>=1.24.0
PyPDF2>=3.0.0
google-generativeai>=0.3.0
python-dotenv>=1.0.0
```

## 🎯 Quick Start Guide

### 1. **Set Your Current Balance**
- Go to the "Manage Data" tab
- Update your current bank balance
- This is your starting point for all projections

### 2. **Add Transactions**
Use one of three methods:
- **Manual Entry**: Use quick action buttons or detailed forms
- **AI Import**: Upload PDF bank statements for automatic processing
- **JSON Import**: Restore from previous backups

### 3. **Monitor Your Health**
- **Green (80-100)**: Healthy cash flow, low risk
- **Yellow (60-79)**: Caution needed, monitor closely  
- **Red (0-59)**: Critical - immediate action required

### 4. **Plan Scenarios**
- Test "what-if" expenses in the sidebar
- Model payment delays to see impact
- Use projections to make informed decisions

## 🏗️ Project Structure

```
FlowState/
├── app.py              # Main Streamlit application
├── bank_ai.py          # AI-powered PDF processing module
├── cashflow_data.json  # Local data storage (auto-generated)
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## 🔧 Configuration

### Google Gemini AI Setup
1. Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to your `.env` file as `GEMINI_API_KEY=your_key_here`
3. The AI will automatically categorize and clean up your bank transactions

### Data Storage
- All data is stored locally in `cashflow_data.json`
- No external databases required
- Easy to backup and restore
- Export functionality for data portability

## 📊 Understanding the Metrics

### **Cash Flow Pulse Score**
- **90-100**: Excellent - Strong runway, no immediate risks
- **80-89**: Good - Healthy with minor areas to watch  
- **60-79**: Caution - Some risks present, monitor closely
- **40-59**: Poor - Action needed to prevent problems
- **0-39**: Critical - Immediate intervention required

### **Days Until Danger**
- Shows when your balance will go negative
- Based on confirmed and projected transactions
- Updates in real-time as you add/modify data
- ∞ means safe runway with current projections

### **Monthly Runway**
- How many months your current balance will last
- Based on average monthly burn rate
- Helps with long-term planning
- Factors in both fixed and variable expenses

## 🤖 AI Features

### Bank Statement Processing
The AI can process PDF bank statements and automatically:
- Extract transaction dates, amounts, and descriptions
- Categorize transactions (payroll, rent, utilities, etc.)
- Clean up messy bank descriptions
- Detect income vs expenses
- Handle multiple date formats
- Skip irrelevant entries (headers, balances, etc.)

### Supported Bank Formats
- Most major US banks (Chase, Bank of America, Wells Fargo, etc.)
- Credit union statements
- Business banking statements
- Standard PDF formats with clear transaction tables

## 🔒 Privacy & Security

- **Local First**: All data stays on your computer
- **No Cloud Storage**: Your financial data never leaves your device
- **API Calls**: Only bank statement text is sent to Google Gemini for processing
- **No Personal Info**: The AI only sees transaction descriptions, not account numbers

## 🚀 Advanced Usage

### Scenario Planning
Use the sidebar controls to model different scenarios:
- **Payment Delays**: See impact of late client payments
- **Large Expenses**: Test equipment purchases or emergency costs
- **Multiple Scenarios**: Compare different financial strategies

### Data Management
- **Export**: Create JSON backups of all your data
- **Import**: Restore from previous backups
- **Clear**: Start fresh (with confirmation)
- **Bulk Operations**: Process multiple transactions at once

