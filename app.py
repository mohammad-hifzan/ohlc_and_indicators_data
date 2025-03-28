from flask import Flask, jsonify, render_template, request
import yfinance as yf
import mysql.connector
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)

# MySQL Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "user",
    "password": "password",
    "database": "algo"
}

# Function to create the database if it doesn't exist
def create_database():
    connection = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS algo;")
    connection.commit()
    cursor.close()
    connection.close()

def drop_table():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS data;")  # Drop table if it exists
    connection.commit()

    cursor.close()
    connection.close()
    print("Table 'data' dropped successfully!")

# Function to create the table
def create_table():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    table_query = """
    CREATE TABLE IF NOT EXISTS data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        datetime DATE NOT NULL,
        open DECIMAL(10,2) NOT NULL,
        high DECIMAL(10,2) NOT NULL,
        low DECIMAL(10,2) NOT NULL,
        close DECIMAL(10,2) NOT NULL,
        sma DECIMAL(10,2),
        rsi DECIMAL(10,2),
        macd DECIMAL(10,2)
    );
    """
    cursor.execute(table_query)
    connection.commit()
    cursor.close()
    connection.close()

# Fetch OHLC data from MySQL
def get_data_from_db(date):
    connection = mysql.connector.connect(**DB_CONFIG)
    date = datetime.strptime(date, "%Y-%m-%d").date() 
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM data WHERE datetime = %s"
    cursor.execute(query, (date,))
    result = cursor.fetchone()
    # cursor.close()
    # connection.close()
    return result

# Fetch OHLC data from yFinance
def fetch_nifty_data():
    ticker = "^NSEI"
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    nifty_data = yf.download(ticker, start=start_date, end=end_date)
    return nifty_data

# Calculate Indicators (SMA, RSI, MACD)
def calculate_indicators(raw_data):
    # Restructure DataFrame
    if raw_data.empty:
        return None
    # Reset index to move Date from index to column
    raw_data.reset_index(inplace=True)
    # Select only needed columns
    data = raw_data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    # Compute indicators
    data["SMA"] = data["Close"].rolling(window=14).mean()
    # RSI Calculation
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))
    # MACD Calculation
    short_ema = data["Close"].ewm(span=12, adjust=False).mean()
    long_ema = data["Close"].ewm(span=26, adjust=False).mean()
    data.loc[:, "MACD"] = short_ema - long_ema

    return data
# Insert new data into MySQL
def insert_data_into_db(data):
    connection = mysql.connector.connect(**DB_CONFIG, autocommit=True)
    cursor = connection.cursor()
    query = """
        INSERT INTO data (datetime, open, high, low, close, sma, rsi, macd)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    for _, row in data.iterrows():
        dt = pd.to_datetime(row["Date"].iloc[0]).to_pydatetime()
        open_price = float(row["Open"].iloc[0])
        high_price = float(row["High"].iloc[0])
        low_price = float(row["Low"].iloc[0])
        close_price = float(row["Close"].iloc[0])
        sma = float(row["SMA"].iloc[0]) if pd.notna(row["SMA"].iloc[0]) else None
        rsi = float(row["RSI"].iloc[0]) if pd.notna(row["RSI"].iloc[0]) else None
        macd = float(row["MACD"].iloc[0]) if pd.notna(row["MACD"].iloc[0]) else None
        cursor.execute(query, (dt, open_price, high_price, low_price, close_price, sma, rsi, macd))

    cursor.close()
    connection.close()
    return "Data inserted successfully!"

# Flask Routes
@app.route('/get_ohlc_indicators', methods=['GET'])
def fetch_ohlc_indicators():
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Date parameter is required"}), 400

    # Check if data exists in MySQL first
    data = get_data_from_db(date)
    if data:
        return jsonify(data)

    # If not found, fetch fresh data
    nifty_data = fetch_nifty_data()

    if nifty_data.empty:
        return jsonify({"error": "No data fetched"}), 400

    nifty_data = calculate_indicators(nifty_data)
    insert_data_into_db(nifty_data)

    # Retrieve the newly inserted data
    data = get_data_from_db(date)
    return jsonify(data)

@app.route("/")
def index():
    return render_template('index.html')

# Initialize database and table before starting the app
# drop_table()
create_database()
create_table()

if __name__ == '__main__':
    app.run(debug=True)
