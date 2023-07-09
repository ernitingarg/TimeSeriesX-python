from datetime import date
from decimal import Decimal
import json


class FinancialData:
    """
      Represents financial data for a
      given stock symbol on a specific date.
      """

    def __init__(
            self,
            symbol: str,
            date: date,
            open_price: Decimal,
            close_price: Decimal,
            volume: int):
        """
            Initializes a new instance of the FinancialData
            class with the specified values.

            :param symbol: The stock symbol.
            :param date: The date of the financial data.
            :param open_price: The opening price of the stock on the specified date.
            :param close_price: The closing price of the stock on the specified date.
            :param volume: The trading volume of the stock on the specified date.
        """
        self.symbol = symbol
        self.date = date
        self.open_price = open_price
        self.close_price = close_price
        self.volume = volume


class FinancialDataEncoder(json.JSONEncoder):
    """
    A custom JSON encoder that serializes FinancialData objects to JSON.
    """

    def default(self, obj):
        """
        Overrides the default() method of the JSONEncoder class
        to handle serialization of FinancialData objects.

        :param obj: The object to be serialized.
        :return: A JSON-serializable representation of the object.
        """

        if isinstance(obj, FinancialData):
            # If the object is an instance of FinancialData,
            # serialize it to a dictionary with its attributes as keys
            # and their serialized values as values.
            return {
                "symbol": obj.symbol,
                "date": obj.date.isoformat(),
                "open_price": str(obj.open_price),
                "close_price": str(obj.close_price),
                "volume": int(obj.volume),
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
