-- Synthetic demo data only. No personal holdings or account references.
USE investments;

INSERT INTO accounts (id, account_name, broker, account_type, base_currency) VALUES
(1, 'Demo ISK', 'Demo Broker', 'ISK', 'SEK'),
(2, 'Demo Pension', 'Demo Broker', 'Pension', 'SEK');

INSERT INTO assets (id, ticker, name, asset_type, currency, market_symbol, isin, sector, country) VALUES
(1, 'NORDICX', 'Nordic Industrial Demo', 'Stock', 'SEK', NULL, NULL, 'Industrials', 'Sweden'),
(2, 'GLOBALX', 'Global Equity Demo', 'ETF', 'USD', NULL, NULL, 'Fund / ETF', 'Global'),
(3, 'BONDX', 'Swedish Bond Demo', 'Fund', 'SEK', NULL, NULL, 'Fixed Income', 'Sweden');

INSERT INTO transactions (id, asset_id, account_id, transaction_type, quantity, price, fees, transaction_date, fx_rate_to_sek, source) VALUES
(1, 1, 1, 'BUY', 100.00000000, 80.00000000, 9.00000000, '2026-01-15', 1.0000000000, 'SAMPLE'),
(2, 2, 1, 'BUY', 15.00000000, 120.00000000, 1.50000000, '2026-02-10', 10.4000000000, 'SAMPLE'),
(3, 1, 1, 'SELL', 20.00000000, 95.00000000, 9.00000000, '2026-06-12', 1.0000000000, 'SAMPLE'),
(4, 3, 2, 'BUY', 200.00000000, 101.50000000, 0.00000000, '2026-03-03', 1.0000000000, 'SAMPLE');

INSERT INTO cash_movements (id, account_id, movement_date, movement_type, description, amount, currency, fx_rate_to_sek, source) VALUES
(1, 1, '2026-01-10', 'DEPOSIT', 'Synthetic opening deposit', 50000.00, 'SEK', 1.0, 'SAMPLE'),
(2, 1, '2026-01-15', 'BUY', 'Nordic Industrial Demo purchase', -8009.00, 'SEK', 1.0, 'SAMPLE'),
(3, 1, '2026-02-10', 'BUY', 'Global Equity Demo purchase', -18735.60, 'SEK', 1.0, 'SAMPLE'),
(4, 1, '2026-06-12', 'SELL', 'Nordic Industrial Demo sale', 1891.00, 'SEK', 1.0, 'SAMPLE'),
(5, 1, '2026-07-01', 'DIVIDEND', 'Synthetic dividend', 250.00, 'SEK', 1.0, 'SAMPLE'),
(6, 2, '2026-03-01', 'DEPOSIT', 'Synthetic pension contribution', 30000.00, 'SEK', 1.0, 'SAMPLE'),
(7, 2, '2026-03-03', 'BUY', 'Swedish Bond Demo purchase', -20300.00, 'SEK', 1.0, 'SAMPLE');

INSERT INTO dividends (id, asset_id, account_id, payment_date, dividend_per_share, shares_held, currency, fx_rate_to_sek, source) VALUES
(1, 1, 1, '2026-07-01', 3.12500000, 80.00000000, 'SEK', 1.0, 'SAMPLE');

INSERT INTO prices (asset_id, price_date, close_price, adjusted_close_price, currency) VALUES
(1, '2026-08-28', 104.00, 104.00, 'SEK'),
(2, '2026-08-28', 131.00, 131.00, 'USD'),
(3, '2026-08-28', 102.40, 102.40, 'SEK');

INSERT INTO fx_rates (currency, rate_date, sek_per_unit) VALUES
('SEK', '2026-08-28', 1.0000000000),
('USD', '2026-08-28', 10.1500000000);
