-- ============================================================
-- Financial Portfolio Analytics Dashboard
-- Public / anonymized MySQL schema
-- Compatible with Dashboard.py in this repository
-- ============================================================

CREATE DATABASE IF NOT EXISTS investments
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE investments;

-- The application is designed to run with a restricted LOCAL MySQL user.
-- Grant SELECT, INSERT, UPDATE and DELETE only. Do not grant CREATE/ALTER/DROP
-- to the dashboard user. Create/upgrade the schema with an administrator user.

CREATE TABLE IF NOT EXISTS accounts (
    id INT NOT NULL AUTO_INCREMENT,
    account_name VARCHAR(120) NOT NULL,
    broker VARCHAR(120) NOT NULL,
    account_type VARCHAR(40) NOT NULL,
    base_currency CHAR(3) NOT NULL DEFAULT 'SEK',
    PRIMARY KEY (id),
    KEY idx_accounts_broker (broker)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS assets (
    id INT NOT NULL AUTO_INCREMENT,
    ticker VARCHAR(40) NOT NULL,
    name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(40) NOT NULL DEFAULT 'Other',
    currency CHAR(3) NOT NULL DEFAULT 'SEK',
    market_symbol VARCHAR(80) DEFAULT NULL,
    isin VARCHAR(24) DEFAULT NULL,
    sector VARCHAR(160) DEFAULT NULL,
    country VARCHAR(160) DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_assets_ticker (ticker),
    UNIQUE KEY uq_assets_isin (isin),
    UNIQUE KEY uq_assets_market_symbol (market_symbol),
    KEY idx_assets_name (name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS import_batches (
    id INT NOT NULL AUTO_INCREMENT,
    account_id INT DEFAULT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_hash CHAR(64) NOT NULL,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_import_batches_file_hash (file_hash),
    KEY idx_import_batches_account (account_id),
    CONSTRAINT fk_import_batches_account
        FOREIGN KEY (account_id) REFERENCES accounts(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    asset_id INT NOT NULL,
    account_id INT DEFAULT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(24,8) NOT NULL,
    price DECIMAL(24,8) NOT NULL,
    fees DECIMAL(24,8) NOT NULL DEFAULT 0,
    transaction_date DATE NOT NULL,
    fx_rate_to_sek DECIMAL(24,10) DEFAULT NULL,
    source VARCHAR(40) NOT NULL DEFAULT 'MANUAL',
    external_transaction_id VARCHAR(160) DEFAULT NULL,
    transaction_hash CHAR(64) DEFAULT NULL,
    import_batch_id INT DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_transactions_hash (transaction_hash),
    KEY idx_transactions_asset_date (asset_id, transaction_date),
    KEY idx_transactions_account_date (account_id, transaction_date),
    KEY idx_transactions_batch (import_batch_id),
    CONSTRAINT fk_transactions_asset
        FOREIGN KEY (asset_id) REFERENCES assets(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_transactions_account
        FOREIGN KEY (account_id) REFERENCES accounts(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_transactions_batch
        FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dividends (
    id BIGINT NOT NULL AUTO_INCREMENT,
    asset_id INT NOT NULL,
    account_id INT DEFAULT NULL,
    payment_date DATE NOT NULL,
    dividend_per_share DECIMAL(24,8) NOT NULL,
    shares_held DECIMAL(24,8) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'SEK',
    fx_rate_to_sek DECIMAL(24,10) NOT NULL DEFAULT 1,
    transaction_hash CHAR(64) DEFAULT NULL,
    import_batch_id INT DEFAULT NULL,
    source VARCHAR(40) NOT NULL DEFAULT 'MANUAL',
    PRIMARY KEY (id),
    UNIQUE KEY uq_dividends_hash (transaction_hash),
    KEY idx_dividends_asset_date (asset_id, payment_date),
    KEY idx_dividends_account_date (account_id, payment_date),
    KEY idx_dividends_batch (import_batch_id),
    CONSTRAINT fk_dividends_asset
        FOREIGN KEY (asset_id) REFERENCES assets(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_dividends_account
        FOREIGN KEY (account_id) REFERENCES accounts(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_dividends_batch
        FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cash_movements (
    id BIGINT NOT NULL AUTO_INCREMENT,
    account_id INT NOT NULL,
    movement_date DATE NOT NULL,
    movement_type VARCHAR(50) NOT NULL,
    description VARCHAR(255) DEFAULT NULL,
    amount DECIMAL(24,8) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'SEK',
    fx_rate_to_sek DECIMAL(24,10) NOT NULL DEFAULT 1,
    transaction_hash CHAR(64) DEFAULT NULL,
    import_batch_id INT DEFAULT NULL,
    source VARCHAR(40) NOT NULL DEFAULT 'MANUAL',
    PRIMARY KEY (id),
    UNIQUE KEY uq_cash_movements_hash (transaction_hash),
    KEY idx_cash_account_date (account_id, movement_date),
    KEY idx_cash_batch (import_batch_id),
    CONSTRAINT fk_cash_account
        FOREIGN KEY (account_id) REFERENCES accounts(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_cash_batch
        FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS corporate_actions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    asset_id INT NOT NULL,
    action_date DATE NOT NULL,
    action_type VARCHAR(40) NOT NULL,
    ratio_new DECIMAL(24,8) DEFAULT NULL,
    ratio_old DECIMAL(24,8) DEFAULT NULL,
    notes VARCHAR(255) DEFAULT NULL,
    import_batch_id INT DEFAULT NULL,
    source VARCHAR(40) NOT NULL DEFAULT 'MANUAL',
    PRIMARY KEY (id),
    KEY idx_corporate_actions_asset_date (asset_id, action_date),
    KEY idx_corporate_actions_batch (import_batch_id),
    CONSTRAINT fk_corporate_actions_asset
        FOREIGN KEY (asset_id) REFERENCES assets(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_corporate_actions_batch
        FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prices (
    id BIGINT NOT NULL AUTO_INCREMENT,
    asset_id INT NOT NULL,
    price_date DATE NOT NULL,
    close_price DECIMAL(24,8) NOT NULL,
    adjusted_close_price DECIMAL(24,8) DEFAULT NULL,
    currency CHAR(3) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_prices_asset_date (asset_id, price_date),
    KEY idx_prices_date (price_date),
    CONSTRAINT fk_prices_asset
        FOREIGN KEY (asset_id) REFERENCES assets(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fx_rates (
    id BIGINT NOT NULL AUTO_INCREMENT,
    currency CHAR(3) NOT NULL,
    rate_date DATE NOT NULL,
    sek_per_unit DECIMAL(24,10) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_fx_currency_date (currency, rate_date),
    KEY idx_fx_rate_date (rate_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS benchmarks (
    id INT NOT NULL AUTO_INCREMENT,
    symbol VARCHAR(40) NOT NULL,
    name VARCHAR(180) NOT NULL,
    currency CHAR(3) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_benchmarks_symbol (symbol)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS benchmark_prices (
    id BIGINT NOT NULL AUTO_INCREMENT,
    benchmark_id INT NOT NULL,
    price_date DATE NOT NULL,
    close_price DECIMAL(24,8) NOT NULL,
    adjusted_close_price DECIMAL(24,8) DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_benchmark_prices_date (benchmark_id, price_date),
    KEY idx_benchmark_prices_date (price_date),
    CONSTRAINT fk_benchmark_prices_benchmark
        FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS risk_free_rates (
    rate_date DATE NOT NULL,
    annual_rate_decimal DECIMAL(18,10) NOT NULL,
    source VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (rate_date)
) ENGINE=InnoDB;
