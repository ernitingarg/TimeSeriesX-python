import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access environment variables
# read DATABASE configurations
database_host = os.getenv('DATABASE_HOST')
database_user = os.getenv('DATABASE_USER')
database_password = os.getenv('DATABASE_PASSWORD')
database_dbname = os.getenv('DATABASE_DBNAME')


class DbConnection:
    """
    Represents a database connection instance.
    """

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """
        Establishes a connection to the MySQL database.
        """
        self.conn = mysql.connector.connect(
            host=database_host,
            user=database_user,
            password=database_password,
            database=database_dbname
        )

    def disconnect(self):
        """
        Closes the database cursor and connection.
        """
        self.close_cursor()
        if self.conn:
            self.conn.close()
            self.conn = None

    def open_cursor(self):
        """
        Opens a cursor object to execute queries.
        """
        self.cursor = self.conn.cursor()

    def close_cursor(self):
        """
        Closes the cursor object.
        """
        if self.cursor:
            self.cursor.close()
            self.cursor = None
