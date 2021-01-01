-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS positions;
DROP TABLE IF EXISTS current_prices;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE positions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  symbol TEXT NOT NULL,
  eur_amount TEXT NOT NULL,
  date_position TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE current_prices (
id INTEGER PRIMARY KEY AUTOINCREMENT, 
symbol TEXT NOT NULL, 
price FLOAT(2) NOT NULL,
latest_trading_day date,
one_day_change_percent DECIMAL(10,5) 
); 
