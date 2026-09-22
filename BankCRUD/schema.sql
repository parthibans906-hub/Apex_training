CREATE DATABASE bank_db;
USE bank_db;

CREATE TABLE accounts(
    account_holder VARCHAR(100) PRIMARY KEY,
    pin VARCHAR(10),
    balance DECIMAL(10,2)
);
