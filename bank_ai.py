import json
import PyPDF2
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

api_key = "YOUR_API_KEY"
#api_key = os.getenv('GEMINI_API_KEY')

def extract_pdf_text(pdf_file):
    """Extract text from uploaded PDF file object"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text, None
    except Exception as e:
        return None, f"Error reading PDF: {str(e)}"

def convert_pdf_to_json(pdf_file, filename):
    """
    Main function: Convert PDF to JSON format
    Called by app.py when user uploads PDF
    """
        
    # Step 1: Extract text from PDF
    pdf_text, error = extract_pdf_text(pdf_file)
    if error:
        return None, error
    
    if not pdf_text or len(pdf_text.strip()) < 50:
        return None, "PDF appears to be empty or contains very little text"
    
    # Step 2: Process with Gemini AI
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Analyze this bank statement text from file "{filename}" and extract ALL transactions as JSON.
        
        For each transaction, provide:
        - date: in YYYY-MM-DD format
        - description: clean, descriptive text (remove extra spaces/codes/reference numbers)
        - amount: positive number for income/deposits, negative for expenses/withdrawals
        - type: "income" for deposits/credits, "expense" for withdrawals/debits
        - category: intelligent guess like "payroll", "rent", "client_payment", "office_supplies", "utilities", "equipment", etc.
        - confidence: 90-100 for clear transactions, lower if uncertain
        
        Rules:
        - Only include actual transactions (skip headers, totals, balances, fees summaries)
        - Clean up messy descriptions (e.g., "ACH DEP PAYROLL CO ABC123" → "Payroll Deposit - Company ABC")
        - Detect income vs expenses based on transaction type and amount signs
        - Make intelligent category guesses based on description patterns
        - Parse amounts correctly (remove commas, handle negative signs)
        - Skip duplicate entries or running balance lines
        - Focus on meaningful business transactions
        - The current balance is the ending balance of the bank account.
        
        Return ONLY a valid JSON array in this exact format:
    {{
    "transactions": [
        {{
            "id": 1,
            "type": "income",
            "amount": 5000.00,
            "date": "2025-08-01",
            "description": "Client Payment - ABC Corp",
            "status": "confirmed",
            "probability": 95
        }},
        {{
            "id": 2,
            "type": "expense",
            "amount": -2500.00,
            "date": "2025-08-02",
            "description": "Office Rent Payment",
            "status": "confirmed",
            "probability": 98
        }}
    ],
    "current_balance": 500.0,
    "next_id": 6
}}
        
        
        Do not include any explanatory text, markdown formatting, or code blocks - only the raw JSON array.
        """
        
        full_prompt = f"{prompt}\n\nBank Statement Text:\n{pdf_text}"
        
        response = model.generate_content(full_prompt)
        
        # Clean up response
        response_text = response.text.strip()
        
        # Remove markdown formatting if present
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()
        
        # Parse JSON
        transactions = json.loads(response_text)
        
        # Step 3: Save to cashflow_data.json in the format app.py expects
        save_to_cashflow_data(transactions)
        
        return transactions, None
        
    except json.JSONDecodeError as e:
        return None, f"Failed to parse AI response as JSON: {str(e)}"
    except Exception as e:
        return None, f"Error processing with Gemini: {str(e)}"

def save_to_cashflow_data(transactions):
    """
    Save transactions directly to cashflow_data.json
    This is where app.py reads from
    """
    try:
        # Try to load existing data
        try:
            with open('cashflow_data.json', 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is corrupted, start fresh
            existing_data = {
                'transactions': [],
                'current_balance': 0,
                'next_id': 1
            }
        
        # Convert bank AI transactions to FlowState format
        next_id = existing_data['next_id']
        
        # Extract the transactions array from the response
        transaction_list = transactions.get('transactions', [])
        
        for transaction in transaction_list:
            # Convert to FlowState format
            flowstate_transaction = {
                'id': next_id,
                'type': transaction['type'],
                'amount': abs(float(transaction['amount'])),  # Always positive in FlowState
                'date': transaction['date'],  # Keep as string for JSON
                'description': transaction['description'],
                'status': 'confirmed',  # Bank transactions are confirmed
                'probability': 100  # Bank transactions are 100% certain
            }
            
            existing_data['transactions'].append(flowstate_transaction)
            next_id += 1
        
        # Update current balance if provided
        if 'current_balance' in transactions:
            existing_data['current_balance'] = float(transactions['current_balance'])
        
        # Update next_id
        existing_data['next_id'] = next_id
        
        # Save back to file
        with open('cashflow_data.json', 'w') as f:
            json.dump(existing_data, f, default=str, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error saving to cashflow_data.json: {e}")
        return False