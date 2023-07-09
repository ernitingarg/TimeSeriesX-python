from datetime import datetime, date
from decimal import Decimal
from typing import List, Tuple
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import parse_qs, urlparse
from mysql.connector.errors import Error

# fmt: off
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from db_connection import DbConnection
from financial_data import FinancialData, FinancialDataEncoder
from avg_financial_data import AverageFinancialData, AverageFinancialDataEncoder
# fmt: on


class FinancialDataRequestHandler(BaseHTTPRequestHandler):
    """
    Request handler class for Financial APIs.
    """

    def do_GET(self):
        """
        Handle GET requests
        """

        # Parse the URL and query parameter
        url_parts = urlparse(self.path)
        query_params = parse_qs(url_parts.query)

        # Check if requested endpoint is valid
        if url_parts.path == '/api/financial_data':
            self._handle_financial_data_api(query_params)
        elif url_parts.path == '/api/statistics':
            self._handle_statistics_api(query_params)
        else:
            self.send_error(404, message="Invalid API endpoint")

    def _handle_financial_data_api(self, query_params):
        """
        Handles the GET requests to the financial data API 
        and returns the data based on the requested query parameters.

        Args:
            query_params (Dict[str, Any]): 
            Query parameters provided by the user.

        Returns:
            None
        """

        # Define a list of supported query parameters
        supported_params = ['start_date',
                            'end_date',
                            'symbol',
                            'limit',
                            'page']

        # Check if all requested query parameters are supported
        for param in query_params.keys():
            if param not in supported_params:
                self.send_error(
                    400, message=f"Unsupported query parameter: {param}")
                return

        try:
            # Get the optional query parameters
            start_date = query_params.get(supported_params[0], [None])[0]
            end_date = query_params.get(supported_params[1], [None])[0]
            symbol = query_params.get(supported_params[2], [None])[0]
            limit = int(query_params.get(supported_params[3], [5])[0])
            page = int(query_params.get(supported_params[4], [1])[0])

            # Fetch the data and total number of records from db
            (data, count) = self._fetch_data_from_db(
                start_date=start_date,
                end_date=end_date,
                symbol=symbol,
                limit=limit,
                page=page)

            # Calculate pagination info
            total_pages = (count + limit - 1) // limit

            # Create the response object
            response = {
                "data": data,
                "pagination": {
                    "count": count,
                    "page": page,
                    "limit": limit,
                    "pages": total_pages,
                },
                "info":  {
                    "error": 'No record found for given parameters.' if not data else ''}
            }

            # Send the response
            self._write_success_response(json.dumps(
                response,
                cls=FinancialDataEncoder))
        # Handle exceptions if occurred
        except Error as error:
            self._write_error_response(500, str(error))
        except ValueError as error:
            self._write_error_response(400, str(error))
        except Exception as error:
            self._write_error_response(500, str(error))

    def _handle_statistics_api(self, query_params):
        """
        Handles API requests to retrieve statistics 
        about the financial data.

        Args:
            query_params (Dict[str, Any]): 
            Query parameters provided by the user.

        Returns:
            None
        """

        # Define a list of supported query parameters
        supported_params = ['start_date',
                            'end_date',
                            'symbol']

        # Check if all requested query parameters are supported
        for param in query_params.keys():
            if param not in supported_params:
                self.send_error(
                    400, message=f"Unsupported query parameter: {param}")
                return

        # Check if there is no missing required parameter
        missing_params = []
        for param in supported_params:
            if param not in query_params:
                missing_params.append(param)
        if len(missing_params) > 0:
            self.send_error(
                400, message=f"Missing required parameters: {', '.join(missing_params)}")
            return

        try:
            # Get the required query parameters
            start_date = query_params.get(supported_params[0])[0]
            end_date = query_params.get(supported_params[1])[0]
            symbol = query_params.get(supported_params[2])[0]

            # Fetch the financial data from db
            (data, _) = self._fetch_data_from_db(
                start_date=start_date,
                end_date=end_date,
                symbol=symbol)

            # Calculate the avergae of financial data
            average_data = self._calculate_average(
                start_date=start_date,
                end_date=end_date,
                symbol=symbol,
                data=data
            )

            # Create the response object
            response = {
                "data": average_data,
                "info":  {
                    "error": 'No record found for given parameters.' if not data else ''}
            }

            # Send the response
            self._write_success_response(json.dumps(
                response,
                cls=AverageFinancialDataEncoder))
        # Handle exceptions if occurred
        except Error as error:
            self._write_error_response(500, str(error))
        except ValueError as error:
            self._write_error_response(400, str(error))
        except Exception as error:
            self._write_error_response(500, str(error))

    def _fetch_data_from_db(
            self,
            start_date: date = None,
            end_date: date = None,
            symbol: str = None,
            limit: int = None,
            page: int = None) -> Tuple[List[FinancialData], int]:
        """
        Fetches financial data from the database based on the query parameters

        Args:
        - self: the instance of the object calling this method
        - start_date (date): start date of the data to fetch
        - end_date (date): end date of the data to fetch
        - symbol (str): the stock symbol of the data to fetch
        - limit (int): maximum number of records to fetch per page
        - page (int): page number of the records to fetch

        Returns:
        A tuple with:
        - data (List[FinancialData]): a list of FinancialData objects fetched from the database
        - count (int): total number of records fetched from the database
        """

       # Connect to mysql db
        db = DbConnection()

        try:
            # Construct the SQL query based on the query parameters
            query_count = "SELECT COUNT(*) FROM financial_data"
            query_get = "SELECT * FROM financial_data"

            conditions = []
            if symbol is not None:
                conditions.append(f"symbol = '{symbol}'")

            if start_date is not None:
                conditions.append(f"date >= '{start_date}'")

            if end_date is not None:
                conditions.append(f"date <= '{end_date}'")

            if conditions:
                query_get += " WHERE " + " AND ".join(conditions)
                query_count += " WHERE " + " AND ".join(conditions)

            if limit:
                offset = (page - 1) * limit
                query_get += f" LIMIT {limit} OFFSET {offset}"

            # Open database connection and cursor to execute queries
            db.connect()
            db.open_cursor()

            # Execute the count query
            db.cursor.execute(query_count)
            # Fetch the result
            count = db.cursor.fetchone()[0]

            # Execute the data query
            db.cursor.execute(query_get)
            # Fetch the results
            results = db.cursor.fetchall()

            # Convert the data to a list of FinancialData
            data = []
            for row in results:
                item = FinancialData(
                    row[0], row[1], row[2], row[3], row[4])
                data.append(item)

            return data, count

        # Close the cursor and the database connection
        finally:
            db.close_cursor()
            db.disconnect()

    def _calculate_average(
            self,
            start_date: date,
            end_date: date,
            symbol: str,
            data: List[FinancialData]) -> AverageFinancialData:
        """
        Calculate the average open price, 
        close price, and volume for a list of FinancialData objects.

        Args:
            start_date (date): Start date of the time period.
            end_date (date): End date of the time period.
            symbol (str): The symbol associated with the financial data.
            data (List[FinancialData]): A list of FinancialData objects to calculate the averages for.

        Returns:
            AverageFinancialData: An object containing the calculated average values.
        """

        if '/' in start_date:
            start_date = datetime.strptime(start_date, '%Y/%m/%d').date()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        if '/' in end_date:
            end_date = datetime.strptime(end_date, '%Y/%m/%d').date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Check if the list is empty
        length = len(data)
        if length == 0:
            return AverageFinancialData(
                start_date=start_date,
                end_date=end_date,
                symbol=symbol)

        # Initialize variables to store total values
        total_open_price = Decimal(0.00)
        total_close_price = Decimal(0.00)
        total_volume = 0

        # Calculate the total values
        for item in data:
            total_open_price += item.open_price
            total_close_price += item.close_price
            total_volume += item.volume

        # Calculate the averages
        avg_open_price = total_open_price / length
        avg_close_price = total_close_price / length
        avg_volume = int(total_volume / length)

        # Create and return an AverageFinancialData object
        return AverageFinancialData(
            start_date=start_date,
            end_date=end_date,
            symbol=symbol,
            average_daily_open_price=avg_open_price,
            average_daily_close_price=avg_close_price,
            average_daily_volume=avg_volume)

    def _write_success_response(self, response: dict):
        """
        Write success response to the client.

        Args:
        - response (dict): the JSON response to send to the client

        Returns:
        - None
        """

        self._write_response(200, response)

    def _write_error_response(self, status: int, error: str):
        """
        Write error response to the client.

        Args:
        - status (int): the HTTP status code to send to the client
        - error (str): the error message to include in the response

        Returns:
        - None
        """

        response = {
            'data': [],
            'pagination': {},
            'info': {'error': error}
        }
        self._write_response(status, json.dumps(response))

    def _write_response(self, status: int, response: dict):
        """
        Write response to the client.

        Args:
        - status (int): the HTTP status code to send to the client
        - response (dict): the JSON response to send to the client

        Returns:
        - None
        """

        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())


def main():
    """
    Starts a HTTP server on port 5000 and serves requests indefinitely.

    Raises:
        KeyboardInterrupt: When user interrupts the process using `Ctrl-C`.
    """

    try:
        # Define the server address and port
        server_address = ('', 5000)

        # Create a new instance of HTTPServer
        httpd = HTTPServer(server_address, FinancialDataRequestHandler)
        print('Server started on port 5000...')

        # Start serving the requests indefinitely
        httpd.serve_forever()

    except KeyboardInterrupt:
        # Stop the server on Ctrl-C
        httpd.server_close()
        print('Server stopped.')


if __name__ == '__main__':
    main()
