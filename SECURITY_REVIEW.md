# Security review for public GitHub release

Reviewed file: `Dashboard.py`

## Checks passed

- No hardcoded MySQL password, API key, bearer token, email address, Swedish personal identity number, or private key was found in the source.
- MySQL credentials are loaded from Streamlit secrets / `.streamlit/secrets.toml` rather than embedded in source code.
- The application explicitly limits the database host to loopback addresses (`127.0.0.1`, `localhost`, `::1`).
- User-entered SQL values are parameterized in the normal database operations.
- Broker CSV files are processed in memory; the source code does not contain real account/depot identifiers or real broker export contents.
- External HTTP calls use HTTPS endpoints.
- The source compiles successfully with Python's `py_compile` check.

## Changes made for the public copy

1. Escaped the dynamically rendered account label before inserting it into an `unsafe_allow_html=True` block.
2. Added an explicit whitelist for the table/column pairs used by the dynamic duplicate-hash SQL helper.
3. Added `.gitignore` rules for `secrets.toml`, environment files, database dumps, PDFs, spreadsheets and private broker-export folders.
4. Added `.streamlit/secrets.toml.example` containing placeholders only.

## Operational cautions

- Never commit `.streamlit/secrets.toml` or any `.env` file.
- Never commit original Avanza/Nordnet exports, transaction PDFs, SQL dumps from the real database, or screenshots containing account identifiers.
- The app makes outbound requests to Yahoo Finance, Stooq, the Riksbank API and a public currency API. Availability and returned market data are external dependencies.
- This repository is designed for a local MySQL database. Do not remove the local-host guardrail unless database/network security is redesigned.
- Streamlit upload limits should be kept reasonable if the app is ever exposed beyond a trusted local environment.

## Public-release status

Suitable for a portfolio repository after using only synthetic/sample data and sanitized screenshots.
