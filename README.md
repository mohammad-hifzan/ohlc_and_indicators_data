# OHLC & Indicators Data

A small Flask app that fetches daily NIFTY 50 (`^NSEI`) OHLC data from Yahoo Finance, computes common technical indicators (SMA, RSI, MACD), caches the results in MySQL, and serves them through a JSON API and a simple web UI.

## Features

- Fetches daily OHLC data for NIFTY 50 via [yfinance](https://pypi.org/project/yfinance/)
- Calculates technical indicators:
  - **SMA** – 14-period Simple Moving Average
  - **RSI** – 14-period Relative Strength Index
  - **MACD** – 12/26 EMA convergence-divergence
- Caches computed data in MySQL (auto-creates the database and table on startup)
- Serves data by date through a REST endpoint and a Bootstrap-based web page

## Tech Stack

- Python / Flask
- yfinance, pandas
- MySQL (`mysql-connector-python`)
- Bootstrap 5 (front end)

## Requirements

- Python 3.8+
- A running MySQL server

## Setup

1. Install dependencies:

   ```bash
   pip install flask yfinance mysql-connector-python pandas
   ```

2. Configure the database connection in `app.py`:

   ```python
   DB_CONFIG = {
       "host": "localhost",
       "user": "user",
       "password": "password",
       "database": "algo"
   }
   ```

3. Run the app:

   ```bash
   python app.py
   ```

   The app starts on `http://127.0.0.1:5000/` and creates the `algo` database and `data` table automatically.

## Usage

### Web UI

Open `http://127.0.0.1:5000/`, pick a date, and click **Show Data** to view OHLC values and indicators for that date.

### API

```
GET /get_ohlc_indicators?date=YYYY-MM-DD
```

Returns cached data for the given date if available, otherwise fetches the last year of data, computes indicators, stores it, and returns the requested day.

**Example**

```bash
curl "http://127.0.0.1:5000/get_ohlc_indicators?date=2025-01-15"
```

**Response**

```json
{
  "id": 1,
  "datetime": "2025-01-15",
  "open": 23200.50,
  "high": 23350.75,
  "low": 23100.25,
  "close": 23300.00,
  "sma": 23250.40,
  "rsi": 55.20,
  "macd": 12.35
}
```

## Project Structure

```
.
├── app.py               # Flask app: data fetching, indicators, DB, routes
└── templates/
    └── index.html       # Web UI for viewing data by date
```
