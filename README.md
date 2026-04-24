# ACC102-Track4
# Interactive Stock Analysis Dashboard

This project is a Streamlit-based stock analysis dashboard that connects to **WRDS CRSP** data. Users can enter their WRDS login credentials, a stock ticker, and a start year to retrieve stock and market data, calculate financial metrics, and display visualizations in an interactive dashboard.

---

## Features

The application provides the following functions:

- WRDS login with username and password
- Stock ticker input
- Automatic lookup of **PERMNO** from `crsp.stocknames`
- Daily stock data retrieval from `crsp.dsf`
- Market return data retrieval from `crsp.dsi`
- Data cleaning and processing
- Interactive dashboard with four tabs:
  - Overview
  - Price & Return
  - Volume & Distribution
  - Market Comparison

---

## Technologies Used

- Python
- Streamlit
- WRDS
- Pandas
- Matplotlib

---

## Project Structure

```bash
.
├── app.py
├── README.md
└── requirements.txt
