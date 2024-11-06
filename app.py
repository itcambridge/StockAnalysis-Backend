from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
import time
import random
import requests
from openai import OpenAI
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": [
    "https://replit.com",
    "https://2c1132b0-24ac-4122-8a5c-430f2df20c14-00-27luvvyohvweb.riker.replit.dev:3001",
    "https://*.repl.co",
    "https://*.replit.dev",
    "https://*.riker.replit.dev"
]}},
supports_credentials=True,
allow_headers=["Content-Type", "Authorization", "Accept"],
methods=["GET", "POST", "OPTIONS"])

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in [
        "https://replit.com",
        "https://2c1132b0-24ac-4122-8a5c-430f2df20c14-00-27luvvyohvweb.riker.replit.dev:3001"
    ]:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "CORS test successful"})
    # Add these routes to your app.py after the test route

@app.route('/api/portfolio', methods=['GET'])

def get_portfolio():
        try:
            # Get the token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "No token provided"}), 401

            token = auth_header.split('Bearer ')[1]

            # Verify the Firebase token
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']

            # Get user's portfolio from Firestore
            doc_ref = db.collection('portfolios').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                return jsonify({"portfolio": doc.to_dict().get('stocks', [])})
            else:
                # If no portfolio exists, return empty array
                return jsonify({"portfolio": []})

        except Exception as e:
            print(f"Error getting portfolio: {str(e)}")
            return jsonify({"error": "Failed to get portfolio"}), 400

@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
        try:
            # Get the token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "No token provided"}), 401

            token = auth_header.split('Bearer ')[1]

            # Verify the Firebase token
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']

            # Get the stock data from request
            stock_data = request.json

            # Get user's portfolio reference
            doc_ref = db.collection('portfolios').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                # Add to existing portfolio
                portfolio = doc.to_dict()
                stocks = portfolio.get('stocks', [])
                stocks.append(stock_data)
                doc_ref.update({'stocks': stocks})
            else:
                # Create new portfolio
                doc_ref.set({'stocks': [stock_data]})

            return jsonify({"message": "Stock added successfully"})

        except Exception as e:
            print(f"Error adding to portfolio: {str(e)}")
            return jsonify({"error": "Failed to add stock"}), 400

@app.route('/api/portfolio/remove', methods=['POST'])
def remove_from_portfolio():
        try:
            # Get the token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "No token provided"}), 401

            token = auth_header.split('Bearer ')[1]

            # Verify the Firebase token
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']

            # Get the index from request
            index = request.json.get('index')

            # Get user's portfolio
            doc_ref = db.collection('portfolios').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                portfolio = doc.to_dict()
                stocks = portfolio.get('stocks', [])
                if 0 <= index < len(stocks):
                    stocks.pop(index)
                    doc_ref.update({'stocks': stocks})
                    return jsonify({"message": "Stock removed successfully"})
                else:
                    return jsonify({"error": "Invalid index"}), 400
            else:
                return jsonify({"error": "Portfolio not found"}), 404

        except Exception as e:
            print(f"Error removing from portfolio: {str(e)}")
            return jsonify({"error": "Failed to remove stock"}), 400

@app.route('/api/interest-rates', methods=['GET'])
def get_interest_rates():
    try:
        # This is example data - replace with real data source
        data = {
            'fedFundsRate': 5.33,
            'tenYearYield': 4.25,
            'twoYearYield': 4.89,
            'defaultRate': 2.1
        }
        return jsonify(data)
    except Exception as e:
        print(f"Error getting interest rates: {str(e)}")
        return jsonify({"error": "Failed to get interest rates"}), 400

# Load environment variables
load_dotenv()

# Initialize OpenAI client using environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Firebase Admin
cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "serviceAccountKey.json"))
firebase_admin.initialize_app(cred)
db = firestore.client()

# ... rest of your original app.py code (all the functions and routes) ...

def get_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    ]
    return random.choice(user_agents)

def safe_float_convert(value):
    """Safely convert a value to float, returning None if conversion fails"""
    if value is None or value == 'None' or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def get_stock_info(symbol, max_retries=3):
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not ALPHA_VANTAGE_API_KEY:
        print("Warning: ALPHA_VANTAGE_API_KEY not found in environment variables")
        return None
    
    for attempt in range(max_retries):
        try:
            # Get Overview data
            overview_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
            overview_response = requests.get(overview_url, timeout=5)
            overview_data = overview_response.json()

            # Add delay to avoid API rate limits
            time.sleep(0.5)

            # Get Quote data
            quote_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
            quote_response = requests.get(quote_url, timeout=5)
            quote_data = quote_response.json()

            # Add delay to avoid API rate limits
            time.sleep(0.5)

            # Get Cash Flow Statement
            cashflow_url = f'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
            cashflow_response = requests.get(cashflow_url, timeout=5)
            cashflow_data = cashflow_response.json()

            # Add Balance Sheet request for quarterly data
            balance_sheet_url = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
            balance_sheet_response = requests.get(balance_sheet_url, timeout=5)
            balance_sheet_data = balance_sheet_response.json()

            if 'Global Quote' in quote_data and overview_data:
                quote = quote_data['Global Quote']
                
                # Calculate Free Cash Flow (TTM) from quarterly data
                free_cash_flow = None
                if 'quarterlyReports' in cashflow_data and len(cashflow_data['quarterlyReports']) >= 4:
                    ttm_free_cash_flow = 0
                    for quarter in cashflow_data['quarterlyReports'][:4]:  # Get last 4 quarters
                        operating_cashflow = safe_float_convert(quarter.get('operatingCashflow', '0'))
                        capital_expenditure = safe_float_convert(quarter.get('capitalExpenditures', '0'))
                        
                        if operating_cashflow is not None and capital_expenditure is not None:
                            quarter_fcf = operating_cashflow - abs(capital_expenditure)
                            ttm_free_cash_flow += quarter_fcf
                    
                    free_cash_flow = ttm_free_cash_flow

                # Calculate Debt to Equity from quarterly data
                debt_to_equity = None
                if 'quarterlyReports' in balance_sheet_data and balance_sheet_data['quarterlyReports']:
                    latest_quarter = balance_sheet_data['quarterlyReports'][0]
                    
                    long_term_debt = safe_float_convert(latest_quarter.get('longTermDebt', '0'))
                    short_term_debt = safe_float_convert(latest_quarter.get('shortTermDebt', '0'))
                    current_debt = safe_float_convert(latest_quarter.get('currentDebt', '0'))
                    operating_lease = safe_float_convert(latest_quarter.get('operatingLeaseNonCurrent', '0'))
                    total_equity = safe_float_convert(latest_quarter.get('totalShareholderEquity', '0'))
                    
                    if total_equity and total_equity != 0:
                        total_debt = (long_term_debt or 0) + (short_term_debt or 0) + (current_debt or 0) + (operating_lease or 0)
                        debt_to_equity = round(total_debt / total_equity, 4)

                info = {
                    'longName': overview_data.get('Name', symbol),
                    'currentPrice': safe_float_convert(quote.get('05. price')),
                    'sector': overview_data.get('Sector', 'N/A'),
                    'industry': overview_data.get('Industry', 'N/A'),
                    'trailingPE': safe_float_convert(overview_data.get('TrailingPE')),
                    'forwardPE': safe_float_convert(overview_data.get('ForwardPE')),
                    'priceToBook': safe_float_convert(overview_data.get('PriceToBookRatio')),
                    'pegRatio': safe_float_convert(overview_data.get('PEGRatio')),
                    'evToEBITDA': safe_float_convert(overview_data.get('EVToEBITDA')),
                    'dividendYield': safe_float_convert(overview_data.get('DividendYield')),
                    'marketCap': safe_float_convert(overview_data.get('MarketCapitalization')),
                    'revenueGrowth': safe_float_convert(overview_data.get('QuarterlyRevenueGrowthYOY')),
                    'profitMargin': safe_float_convert(overview_data.get('ProfitMargin')),
                    'operatingMargin': safe_float_convert(overview_data.get('OperatingMarginTTM')),
                    'debtToEquity': debt_to_equity,
                    'returnOnEquity': safe_float_convert(overview_data.get('ReturnOnEquityTTM')),
                    'freeCashFlow': free_cash_flow
                }
                
                return info

            print(f"Attempt {attempt + 1}: Invalid response format")
            if attempt < max_retries - 1:
                time.sleep(1)
                
        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1} timed out")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            
        if attempt < max_retries - 1:
            time.sleep(2)
            
    return None

def get_gpt_analysis(data):
    try:
        prompt = f"""
        You are a financial analyst. Based on the following stock data, provide a brief analysis 
        of the stock's financial health and potential as an investment. Consider:
        1. Valuation (PE Ratio, PEG Ratio, Price to Book)
        2. Financial Health (Debt to Equity, Free Cash Flow)
        3. Growth Metrics (Revenue Growth, Return on Equity)
        
        Keep your response focused and under 150 words.

        {data}

        Analysis:
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a concise financial analyst focused on key metrics and their implications."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT Analysis error: {str(e)}")
        return "AI analysis temporarily unavailable. Please try again later."

@app.route('/api/analyze/<symbol>', methods=['GET'])
def analyze_stock(symbol):
    try:
        info = get_stock_info(symbol.upper())
        
        if not info:
            return jsonify({"error": "Unable to fetch stock data. Please try again later."}), 400

        # Create data for GPT analysis
        data_for_gpt = f"""
        Stock: {symbol.upper()}
        Company: {info.get('longName', 'N/A')}
        Current Price: ${info.get('currentPrice', 'N/A')}
        
        Key Statistics:
        PE Ratio: {info.get('trailingPE', 'N/A')}
        Forward PE: {info.get('forwardPE', 'N/A')}
        PEG Ratio: {info.get('pegRatio', 'N/A')}
        Price to Book: {info.get('priceToBook', 'N/A')}
        Market Cap: {info.get('marketCap', 'N/A')}
        Revenue Growth: {info.get('revenueGrowth', 'N/A')}
        Debt to Equity: {info.get('debtToEquity', 'N/A')}
        Return on Equity: {info.get('returnOnEquity', 'N/A')}
        Free Cash Flow: {info.get('freeCashFlow', 'N/A')}
        """

        return jsonify({
            "companyName": info.get('longName', 'N/A'),
            "currentPrice": info.get('currentPrice'),
            "sector": info.get('sector'),
            "industry": info.get('industry'),
            "statistics": {
                "Valuation Metrics": {
                    "PE Ratio": info.get('trailingPE'),
                    "Forward PE": info.get('forwardPE'),
                    "PEG Ratio": info.get('pegRatio'),
                    "Price to Book": info.get('priceToBook'),
                    "Dividend Yield": info.get('dividendYield')
                },
                "Financial Health": {
                    "Market Cap": info.get('marketCap'),
                    "Revenue Growth": info.get('revenueGrowth'),
                    "Debt to Equity": info.get('debtToEquity'),
                    "Return on Equity": info.get('returnOnEquity'),
                    "Free Cash Flow": info.get('freeCashFlow')
                }
            },
            "gptAnalysis": get_gpt_analysis(data_for_gpt)
        })

    except Exception as e:
        print(f"Error processing request for symbol {symbol}: {str(e)}")
        return jsonify({
            "error": "Unable to fetch stock data. Please try again."
        }), 400

@app.route('/', methods=['GET'])
def home():
    print("Home route accessed!")  # Debug log
    return jsonify({
        "status": "running",
        "message": "Backend is up and running"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
