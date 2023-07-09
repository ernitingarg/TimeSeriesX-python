from typing import List
import sys
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime, date, timedelta
import mysql.connector
from db_connection import DbConnection
from financial_data import FinancialData

# Load environment variables from .env file
load_dotenv()

# Access environment variables
# read API configurations
api_key = os.getenv('API_KEY')
api_url = os.getenv('API_URL')
api_load_period = os.getenv('API_GET_RECENT_DATA_IN_DAYS')
api_symbols = os.getenv('API_SYMBOLS')
api_open_price_keyname = os.getenv('API_OPEN_PRICE_KEYNAME')
api_close_price_keyname = os.getenv('API_CLOSE_PRICE_KEYNAME')
api_volume_keyname = os.getenv('API_VOLUME_KEYNAME')

# Set start and end date to retrieve data from external api
today_date = date.today()
start_date = today_date - timedelta(days=int(api_load_period))
end_date = today_date


def main():
    """
    This function retrieves stock market data using an external API,
    processes the data,
    and saves the processed data into a MySQL database.
    """

    symbols = api_symbols.split(",")

    for symbol in symbols:
        # Create url for API request for given stock symbol
        url = f'{api_url}&symbol={symbol}&apikey={api_key}'

        # Get response from give url
        response = _get_response(url)

        # Get timeseries data from response,
        # filter it for a specific range (default to latest 14 days)
        # and process to prepare final result
        processed_data = _load_and_process_timeseries_data(
            symbol,
            response)

        # Save processed items into mysql db
        _save_items_into_db(processed_data)


def _save_items_into_db(financial_data: List):
    """
    Inserts processed financial data into 
    the MySQL database table.

    Args:
        financial_data (List): 
        A list of financial data to be inserted into the table.

    Returns:
        None.
    """

    db = DbConnection()
    try:
        # Connect to mysql db
        db.connect()

        # Open a cursor to execute queries
        db.open_cursor()

        # Insert records into table by executing cursor
        for item in financial_data:
            query = ("INSERT INTO financial_data (symbol, date, open_price, close_price, volume) "
                     "VALUES (%s, %s, %s, %s, %s) "
                     "ON DUPLICATE KEY UPDATE open_price=%s, close_price=%s, volume=%s")
            val = (item.symbol, item.date, item.open_price, item.close_price, item.volume,
                   item.open_price, item.close_price, item.volume)
            db.cursor.execute(query, val)

        # Commit the inserted records
        db.conn.commit()

        # Close the cursor and the database connection
        db.close_cursor()
        db.disconnect()

    except mysql.connector.Error as error:
        # Handle MYSQL db exceptions that might occur
        print("Failed to insert record into MySQL table: {}".format(error))
        sys.exit(1)


def _load_and_process_timeseries_data(
        symbol: str,
        response: requests.Response) -> List:
    """
    Load and process timeseries data from API response
    for a specific range of dates.

    Args:
        symbol: A string representing the financial symbol.
        response: A response object from API containing time series data.

    Returns:
        A list of financial data objects containing
        symbol, date, open_price, close_price and volume.
    """

    items = []
    try:
        data = response.json()
        ts_data = data[f'Time Series (Daily)']

        for ts_key, ts_value in ts_data.items():
            date = datetime.strptime(ts_key, '%Y-%m-%d').date()

            if (date > end_date or date < start_date):
                continue

            for key, value in ts_value.items():
                keyname = key.split(".")[1].strip()
                if api_open_price_keyname == keyname:
                    open_price = value
                elif api_close_price_keyname == keyname:
                    close_price = value
                elif api_volume_keyname == keyname:
                    volume = value
            item = FinancialData(symbol, date, open_price, close_price, volume)
            items.append(item)

        return items
    except KeyError as error:
        if 'Note' in data:
            print(data['Note'])
        elif 'Error Message' in data:
            print(data['Error Message'])
        else:
            print("KeyError found", error)
        sys.exit(1)
    except json.JSONDecodeError as error:
        print("Response can not be serialized", error)
        sys.exit(1)
    except Exception as error:
        print("Error", error)
        sys.exit(1)


def _get_response(url) -> requests.Response:
    """Gets the http response for a given url.

    Args:
        url (str): API url to be requested

    Returns:
        Response: Response from API
    """

    response = None
    try:
        response = requests.get(url)
        response.raise_for_status()
    # When invalid HTTP response
    except requests.exceptions.HTTPError as error:
        print("Http Error:", error)
    # When there is a network problem (e.g. DNS failure, refused connection, etc)
    except requests.exceptions.ConnectionError as error:
        print("Connection error", error)
    # When request times out
    except requests.exceptions.Timeout as error:
        print("Timeout Error:", error)
    # Any other exception raised by 'Requests'
    except requests.exceptions.RequestException as error:
        print("Exception request", error)

    if response is None:
        sys.exit(1)
    return response


if __name__ == '__main__':
    main()
