# TimeSeriesX project

This project exposes few API endpoints to manage stock market timeseries data retrieved from external api [alphavantage](www.alphavantage.co).

The application has below main roles:
- Get stock timeseries data from external api.
- Process financial data and store them in MYSQL database.
- Provide API to fetch financial data from database for a given set of optional parameters.
- Provide API to calculate average of financial data of a specific stock for a specific date range.
- Provide dockerized based environment for MYSQL DB and APIs.

## Setup local environment

To run the application, the first thing we need to setup environment to deploy our application.
Please follow below steps:

- Run below command to clone the repository
	```
	git clone https://github.com/ernitingarg09/TimeSeriesX.git
	```
- Go to `TimeSeriesX` folder

- Run below command to setup docker environment
	```
	docker-compose up
	
	# If you want to run in detach mode, run below command
	docker-compose up -d
	```
- Run below command to make sure following containers are up and running
	```
	docker-compose ps
	```
	
	- `tsx_mysql`
		- This container runs MYSQL database locally.
		- The default database name is `timeseriesdb`
		- The default user name is `root`
		- The default password for root user is `pass`
		- If you prefer to override these values, then go to [.env](.env) file and update below values based on your need
			```
			DATABASE_HOST=localhost
			DATABASE_USER=root
			DATABASE_PASSWORD=pass
			DATABASE_DBNAME=timeseriesdb
			```
	- `tsx_api`
		- This container runs below 2 REST APIs at port `5000`
			- `api/financial_data`: It fetches data from database based on requested optional query parameters.
			- `api/statistics`: It fetches data from database for a requested symbol/stock and required date range and then, calculates average of financial data.

- Once docker containers are running, the next step is to validate below APIs are `accessible` (note: as of now there is no data):
	- http://localhost:5000/api/financial_data?start_date=2023-05-05&end_date=2023-05-14&symbol=IBM&limit=2&page=1 OR
	- http://localhost:5000/api/financial_data?start_date=2023/05/05&end_date=2023/05/14&symbol=IBM&limit=2&page=1
	```json
	{
	  "data": [],
	  "pagination": {
		"count": 0,
		"page": 1,
		"limit": 2,
		"pages": 0
	  },
	  "info": {
		"error": "No record found for given parameters."
	  }
	}
	```
		
	- http://localhost:5000/api/statistics?start_date=2023-05-05&end_date=2023-05-14&symbol=IBM OR
	- http://localhost:5000/api/statistics?start_date=2023/05/05&end_date=2023/05/14&symbol=IBM
	```json
	{
	  "data": {
		"start_date": "2023-05-05",
		"end_date": "2023-05-14",
		"symbol": "IBM",
		"average_daily_open_price": "0.00",
		"average_daily_close_price": "0.00",
		"average_daily_volume": 0
	  },
	  "info": {
		"error": "No record found for given parameters."
	  }
	}
	```

## Initialize Database

As there is no record in database, the next step is to initialize database by requesting external api `alphavantage` and process response data.

This operation is done by another python tool [get_raw_data.py](get_raw_data.py).

As this tool is not part of dockerized environment, please follow below steps:

- Run below command to install required packages
	```
	pip install -r requirements.txt
	```

- (Optional) If needed, please change the [.env](.env) file to override external API specific parameters.
	```
	API_KEY=OA0CY103EIRLMAB1
	API_SYMBOLS=IBM,AAPL
	API_GET_RECENT_DATA_IN_DAYS=14
	```

- Run below command which gets data from external api, processes them and inserts into MYSQL db.
	```
	python get_raw_data.py
	```
- Once its done, please check below APIs again
	- http://localhost:5000/api/financial_data?start_date=2023-05-05&end_date=2023-05-14&symbol=IBM&limit=2&page=1 OR
	- http://localhost:5000/api/financial_data?start_date=2023/05/05&end_date=2023/05/14&symbol=IBM&limit=2&page=1
	```json
	{
	  "data": [
		{
		  "symbol": "IBM",
		  "date": "2023-05-05",
		  "open_price": "123.11",
		  "close_price": "123.65",
		  "volume": 4971936
		},
		{
		  "symbol": "IBM",
		  "date": "2023-05-08",
		  "open_price": "123.76",
		  "close_price": "123.40",
		  "volume": 3663818
		}
	  ],
	  "pagination": {
		"count": 6,
		"page": 1,
		"limit": 2,
		"pages": 3
	  },
	  "info": {
		"error": ""
	  }
	}
	```
		
	- http://localhost:5000/api/statistics?start_date=2023-05-05&end_date=2023-05-14&symbol=IBM OR
	- http://localhost:5000/api/statistics?start_date=2023/05/05&end_date=2023/05/14&symbol=IBM
	```json
	{
	  "data": {
		"start_date": "2023-05-05",
		"end_date": "2023-05-14",
		"symbol": "IBM",
		"average_daily_open_price": "122.36",
		"average_daily_close_price": "122.33",
		"average_daily_volume": 4229383
	  },
	  "info": {
		"error": ""
	  }
	}
	```
	
## Questions

### How to maintain the API key in both local development and production environment?

The best practice for managing API keys is to keep them secret and secure. Below are few ways to secure them:
- Store them in environment variable
	- `Local`: Set these API keys variable in `.env` file.
	- `Production`: Set these variables in server environment or use a cloud provider's environment variable management system. (eg: Azure App service -> Configuration)
- Use a configuration file to store API keys
	- `Local`: A local configuration file that contains the API keys
	- `Production`: A Separate configuration file that is not version-controlled.
- **[Recommended]** Use a secrets management tool:
	Secrets management tools such as Azure KeyVault or AWS Secrets Manager can help manage API keys.

### How to cleanup dockerized environment?

- Run below command which should remove container, image, network and also the data volume. 
	```
	docker-compose down -v --rmi all
	```

### How to connect database manually?

- Run below commands to connect to db and run query
	```
	# Go to the container
	docker exec -it tsx_mysql mysql -u root -p ## Please enter password (default is pass)
	
	# Set database
	
	mysql> Use timeseriesdb
	Reading table information for completion of table and column names
	You can turn off this feature to get a quicker startup with -A

	Database changed
	
	# Run select query
	
	mysql> select * from financial_data;
	+--------+------------+------------+-------------+-----------+
	| symbol | date       | open_price | close_price | volume    |
	+--------+------------+------------+-------------+-----------+
	| AAPL   | 2023-05-01 |     169.28 |      169.59 |  52472936 |
	| AAPL   | 2023-05-02 |     170.09 |      168.54 |  48425696 |
	| AAPL   | 2023-05-03 |     169.50 |      167.45 |  65136018 |
	| AAPL   | 2023-05-04 |     164.89 |      165.79 |  81235427 |
	| AAPL   | 2023-05-05 |     170.98 |      173.57 | 113453171 |
	| AAPL   | 2023-05-08 |     172.48 |      173.50 |  55962793 |
	| AAPL   | 2023-05-09 |     173.05 |      171.77 |  45326874 |
	| AAPL   | 2023-05-10 |     173.02 |      173.56 |  53724501 |
	| AAPL   | 2023-05-11 |     173.85 |      173.75 |  49514676 |
	| AAPL   | 2023-05-12 |     173.62 |      172.57 |  45533138 |
	| IBM    | 2023-05-01 |     126.35 |      126.09 |   2724992 |
	| IBM    | 2023-05-02 |     126.30 |      125.16 |   4445283 |
	| IBM    | 2023-05-03 |     125.46 |      123.45 |   4554212 |
	| IBM    | 2023-05-04 |     123.03 |      122.57 |   4468237 |
	| IBM    | 2023-05-05 |     123.11 |      123.65 |   4971936 |
	| IBM    | 2023-05-08 |     123.76 |      123.40 |   3663818 |
	| IBM    | 2023-05-09 |     121.90 |      121.17 |   4540047 |
	| IBM    | 2023-05-10 |     121.99 |      122.02 |   4189222 |
	| IBM    | 2023-05-11 |     122.02 |      120.90 |   3446452 |
	| IBM    | 2023-05-12 |     121.41 |      122.84 |   4564825 |
	+--------+------------+------------+-------------+-----------+
	20 rows in set (0.00 sec)
	```

## Few Testing URL

Below are few testing URL for quick testing:

### api/financial_data
- Invalid api (error) : http://localhost:5000/api/financial_data_xx
- Unsuppoted query parameter (error): http://localhost:5000/api/financial_data?my_date=2023-05-05
- Invalid date format (error) : http://localhost:5000/api/financial_data?start_date=2023-05
- Without query parameter (success) : http://localhost:5000/api/financial_data
- With `start_date` (success): http://localhost:5000/api/financial_data?start_date=2023-05-05
- With `end_date` (success) : http://localhost:5000/api/financial_data?end_date=2023-05-14
- With `symbol` (success): http://localhost:5000/api/financial_data?symbol=IBM
- With `limit` (success): http://localhost:5000/api/financial_data?limit=6
- With `page` (success): http://localhost:5000/api/financial_data?page=2
- Few combination of above query parameters can be tried
- Exception can be tested as below:
	- Stop MYSQL container `docker stop tsx_mysql`
	- Hit URL: http://localhost:5000/api/financial_data

### api/statistics
- Invalid api (error) : http://localhost:5000/api/statistics_xx
- Without query parameter (error): http://localhost:5000/api/statistics
- Unsuppoted query parameter (error): http://localhost:5000/api/statistics?my_date=2023-05-05
- Few combination of above query parameters can be tried
- Exception can be tested as below:
	- Stop MYSQL container `docker stop tsx_mysql`
	- Hit URL: http://localhost:5000/api/statistics?start_date=2023-05-05&end_date=2023-05-14&symbol=IBM