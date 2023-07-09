from datetime import date
from decimal import Decimal
import json


class AverageFinancialData:
    """
      Represents the average financial data for a given symbol
       within a certain time period.
      """

    def __init__(
            self,
            start_date: date,
            end_date: date,
            symbol: str,
            average_daily_open_price: Decimal = Decimal(0.00),
            average_daily_close_price: Decimal = Decimal(0.00),
            average_daily_volume: int = 0):
        """
        Initialize an AverageFinancialData instance with the given parameters.

        :param start_date: Start date of the time period.
        :param end_date: End date of the time period.
        :param symbol: The financial symbol for which the data is being averaged.
        :param average_daily_open_price: The average daily opening price for the symbol.
        :param average_daily_close_price: The average daily closing price for the symbol.
        :param average_daily_volume: The average daily volume for the symbol.
        """

        self.start_date = start_date
        self.end_date = end_date
        self.symbol = symbol
        self.average_daily_open_price = average_daily_open_price
        self.average_daily_close_price = average_daily_close_price
        self.average_daily_volume = average_daily_volume


class AverageFinancialDataEncoder(json.JSONEncoder):
    """
    A custom JSON encoder that serializes 
    AverageFinancialData objects to JSON.
    """

    def default(self, obj):
        """
        Overrides the default() method of the JSONEncoder class
        to handle serialization of AverageFinancialData objects.

        :param obj: The object to be serialized.
        :return: A JSON-serializable representation of the object.
        """

        if isinstance(obj, AverageFinancialData):
            # If the object is an instance of AverageFinancialData,
            # serialize it to a dictionary with its attributes as keys
            # and their serialized values as values.
            return {
                "start_date": obj.start_date.isoformat(),
                "end_date": obj.end_date.isoformat(),
                "symbol": obj.symbol,
                "average_daily_open_price": f"{obj.average_daily_open_price:.2f}",
                "average_daily_close_price": f"{obj.average_daily_close_price:.2f}",
                "average_daily_volume": obj.average_daily_volume,
            }
        elif isinstance(obj, Decimal):
            # Serialize Decimal objects to strings
            return str(obj)
        elif isinstance(obj, date):
            # Serialize date objects to ISO format strings
            return obj.isoformat()
        else:
            # For all other objects, fallback to the default serialization behavior
            return super().default(obj)
