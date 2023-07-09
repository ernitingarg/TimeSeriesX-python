CREATE TABLE financial_data (
    symbol VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10, 2) NOT NULL,
    close_price DECIMAL(10, 2) NOT NULL,
    volume INT UNSIGNED NOT NULL,
    PRIMARY KEY (symbol, date)
);