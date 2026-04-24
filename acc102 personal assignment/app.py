import streamlit as st
import wrds
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

st.title("Interactive Stock Analysis Dashboard")
st.write("Enter a stock ticker to load stock data from WRDS CRSP and generate charts.")

st.sidebar.header("Input Parameters")

username = st.sidebar.text_input("WRDS Username")
password = st.sidebar.text_input("WRDS Password", type="password")
ticker_input = st.sidebar.text_input("Enter Stock Ticker", value="AAPL").strip().upper()
start_year = st.sidebar.number_input("Start Year", min_value=2000, max_value=2025, value=2020, step=1)
load_button = st.sidebar.button("Load Data")


def get_permno(conn, ticker):
    query = f"""
        SELECT DISTINCT permno, ticker, comnam, namedt, nameenddt
        FROM crsp.stocknames
        WHERE ticker = '{ticker}'
        ORDER BY nameenddt DESC
    """
    return conn.raw_sql(query)


def get_stock_data(conn, permno, start_year):
    query = f"""
        SELECT date, prc, ret, shrout, cfacpr, vol, permno
        FROM crsp.dsf
        WHERE permno = {permno}
        AND date >= '{start_year}-01-01'
        ORDER BY date
    """
    return conn.raw_sql(query)


def get_market_data(conn, start_year):
    query = f"""
        SELECT date, vwretd
        FROM crsp.dsi
        WHERE date >= '{start_year}-01-01'
        ORDER BY date
    """
    return conn.raw_sql(query)


def process_stock_data(df):
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df["prc"] = pd.to_numeric(df["prc"], errors="coerce")
    df["ret"] = pd.to_numeric(df["ret"], errors="coerce")
    df["shrout"] = pd.to_numeric(df["shrout"], errors="coerce")
    df["cfacpr"] = pd.to_numeric(df["cfacpr"], errors="coerce")
    df["vol"] = pd.to_numeric(df["vol"], errors="coerce")

    df = df.dropna(subset=["prc", "ret", "shrout", "cfacpr", "vol"]).copy()
    df = df[df["cfacpr"] != 0].copy()

    df["adjusted_price"] = df["prc"].abs() / df["cfacpr"]
    df["market_cap"] = df["adjusted_price"] * df["shrout"] * 1000
    df["cumulative_return"] = (1 + df["ret"]).cumprod() - 1

    return df


def process_market_data(market_df):
    if market_df.empty:
        return market_df

    market_df["date"] = pd.to_datetime(market_df["date"])
    market_df["vwretd"] = pd.to_numeric(market_df["vwretd"], errors="coerce")
    market_df = market_df.dropna(subset=["vwretd"]).copy()
    market_df["market_cumulative_return"] = (1 + market_df["vwretd"]).cumprod() - 1

    return market_df


if load_button:
    if not username:
        st.error("Please enter your WRDS username.")
    elif not password:
        st.error("Please enter your WRDS password.")
    elif not ticker_input:
        st.error("Please enter a stock ticker.")
    else:
        conn = None
        try:
            with st.spinner("Connecting to WRDS and loading data..."):
                conn = wrds.Connection(
                    wrds_username=username,
                    wrds_password=password
                )

                permno_df = get_permno(conn, ticker_input)

                if permno_df.empty:
                    st.warning(f"No matching stock found for ticker '{ticker_input}'.")
                else:
                    permno = int(permno_df.iloc[0]["permno"])
                    company_name = permno_df.iloc[0]["comnam"]

                    stock_df = get_stock_data(conn, permno, start_year)
                    market_df = get_market_data(conn, start_year)

                    stock_df = process_stock_data(stock_df)
                    market_df = process_market_data(market_df)

                    if stock_df.empty:
                        st.warning(f"No stock data found for ticker '{ticker_input}' from {start_year}.")
                    else:
                        merged_df = pd.merge(
                            stock_df,
                            market_df[["date", "market_cumulative_return"]],
                            on="date",
                            how="left"
                        )

                        st.success(f"Data loaded successfully for {ticker_input}.")
                        st.write(f"**Company Name:** {company_name}")
                        st.write(f"**PERMNO:** {permno}")

                        latest_price = stock_df["adjusted_price"].iloc[-1]
                        latest_return = stock_df["cumulative_return"].iloc[-1]
                        latest_mktcap = stock_df["market_cap"].iloc[-1]
                        avg_volume = stock_df["vol"].mean()

                        tab1, tab2, tab3, tab4 = st.tabs(
                            ["Overview", "Price & Return", "Volume & Distribution", "Market Comparison"]
                        )

                        with tab1:
                            st.subheader(f"{ticker_input} Key Metrics")
                            col1, col2, col3, col4 = st.columns(4)
                            col1.metric("Latest Adjusted Price", f"{latest_price:.2f}")
                            col2.metric("Cumulative Return", f"{latest_return:.2%}")
                            col3.metric("Latest Market Cap", f"{latest_mktcap:,.0f}")
                            col4.metric("Average Volume", f"{avg_volume:,.0f}")

                            st.subheader("Data Preview")
                            st.dataframe(stock_df.head(20), use_container_width=True)

                        with tab2:
                            col_left, col_right = st.columns(2)

                            with col_left:
                                st.subheader(f"{ticker_input} Adjusted Price")
                                fig1, ax1 = plt.subplots(figsize=(8, 4))
                                ax1.plot(stock_df["date"], stock_df["adjusted_price"], color="blue")
                                ax1.set_title(f"{ticker_input} Adjusted Price")
                                ax1.set_xlabel("Date")
                                ax1.set_ylabel("Adjusted Price")
                                ax1.grid(True)
                                st.pyplot(fig1)

                            with col_right:
                                st.subheader(f"{ticker_input} Cumulative Return")
                                fig2, ax2 = plt.subplots(figsize=(8, 4))
                                ax2.plot(stock_df["date"], stock_df["cumulative_return"], color="green")
                                ax2.set_title(f"{ticker_input} Cumulative Return")
                                ax2.set_xlabel("Date")
                                ax2.set_ylabel("Cumulative Return")
                                ax2.grid(True)
                                st.pyplot(fig2)

                        with tab3:
                            col_left2, col_right2 = st.columns(2)

                            with col_left2:
                                st.subheader(f"{ticker_input} Trading Volume")
                                fig3, ax3 = plt.subplots(figsize=(8, 4))
                                ax3.bar(stock_df["date"], stock_df["vol"], color="orange")
                                ax3.set_title(f"{ticker_input} Trading Volume")
                                ax3.set_xlabel("Date")
                                ax3.set_ylabel("Volume")
                                ax3.grid(True, axis="y")
                                st.pyplot(fig3)

                            with col_right2:
                                st.subheader(f"{ticker_input} Daily Return Distribution")
                                fig4, ax4 = plt.subplots(figsize=(8, 4))
                                ax4.hist(stock_df["ret"], bins=40, color="gray", edgecolor="black")
                                ax4.set_title(f"{ticker_input} Daily Return Distribution")
                                ax4.set_xlabel("Daily Return")
                                ax4.set_ylabel("Frequency")
                                ax4.grid(True)
                                st.pyplot(fig4)

                        with tab4:
                            st.subheader(f"{ticker_input} vs Market Cumulative Return")
                            fig5, ax5 = plt.subplots(figsize=(10, 4))
                            ax5.plot(merged_df["date"], merged_df["cumulative_return"], label=ticker_input, color="blue")
                            ax5.plot(merged_df["date"], merged_df["market_cumulative_return"], label="Market", color="red")
                            ax5.set_title(f"{ticker_input} vs Market Cumulative Return")
                            ax5.set_xlabel("Date")
                            ax5.set_ylabel("Cumulative Return")
                            ax5.legend()
                            ax5.grid(True)
                            st.pyplot(fig5)

        except Exception as e:
            st.error(f"An error occurred: {e}")

        finally:
            if conn is not None:
                try:
                    conn.close()
                except:
                    pass