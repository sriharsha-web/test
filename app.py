import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
from io import StringIO

# Set page configuration
st.set_page_config(
    page_title="Stock Data Visualization",
    page_icon="📈",
    layout="wide"
)

# Title of the application
st.title("📈 Stock Data Visualization")
st.write("Enter a stock symbol to view financial data and visualizations.")

# Function to get stock data
def get_stock_data(ticker_symbol, period="1y"):
    """Fetch stock data from Yahoo Finance using the yfinance package"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Get historical market data
        hist = ticker.history(period=period)
        # Get general info about the stock
        info = ticker.info
        return hist, info, None
    except Exception as e:
        return None, None, str(e)

# Function to create downloadable CSV
def get_table_download_link(df, filename="data.csv", text="Download CSV"):
    """Generates a link allowing the data in a given dataframe to be downloaded as a CSV file"""
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Function to plot interactive stock chart
def plot_stock_chart(data, ticker_symbol):
    """Create an interactive Plotly chart of stock price history"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        name='Close Price',
        line=dict(color='royalblue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['High'],
        name='High',
        line=dict(color='green', width=1, dash='dot')
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Low'],
        name='Low',
        line=dict(color='red', width=1, dash='dot')
    ))
    
    fig.update_layout(
        title=f'{ticker_symbol} Stock Price',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        legend_title='Price Type',
        hovermode='x unified',
        height=500
    )
    
    return fig

# Function to format financial metrics
def format_number(num):
    """Format numbers for better readability"""
    if num is None:
        return "N/A"
    
    if isinstance(num, str):
        return num
    
    abs_num = abs(num)
    
    if abs_num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"${num / 1_000:.2f}K"
    else:
        return f"${num:.2f}"

# Function to get key financial metrics
def get_financial_metrics(info):
    """Extract and organize key financial metrics from stock info"""
    metrics = {}
    
    # These keys may or may not be present in the info dictionary
    # So we use the get method with a default value of None
    metrics["Market Cap"] = info.get("marketCap")
    metrics["PE Ratio"] = info.get("trailingPE")
    metrics["EPS (TTM)"] = info.get("trailingEps")
    metrics["Dividend Yield"] = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None
    metrics["52 Week High"] = info.get("fiftyTwoWeekHigh")
    metrics["52 Week Low"] = info.get("fiftyTwoWeekLow")
    metrics["50 Day Average"] = info.get("fiftyDayAverage")
    metrics["200 Day Average"] = info.get("twoHundredDayAverage")
    metrics["Forward PE"] = info.get("forwardPE")
    metrics["PEG Ratio"] = info.get("pegRatio")
    metrics["Beta"] = info.get("beta")
    metrics["Volume"] = info.get("volume")
    metrics["Avg Volume"] = info.get("averageVolume")
    
    # Create a DataFrame with the metrics
    metrics_df = pd.DataFrame({
        'Metric': list(metrics.keys()),
        'Value': [format_number(val) if isinstance(val, (int, float)) else "N/A" for val in metrics.values()]
    })
    
    return metrics_df

# Input section for stock symbol
with st.container():
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ticker_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, GOOGL)", "AAPL").upper()
    
    with col2:
        period_options = {
            "1 Month": "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y",
            "2 Years": "2y",
            "5 Years": "5y",
            "Max": "max"
        }
        selected_period = st.selectbox("Select Time Period", list(period_options.keys()))
        period = period_options[selected_period]

# Main content section
if ticker_symbol:
    with st.spinner(f'Loading data for {ticker_symbol}...'):
        # Fetch stock data
        history_data, stock_info, error = get_stock_data(ticker_symbol, period)
        
        if error:
            st.error(f"Error retrieving data for {ticker_symbol}: {error}")
        elif history_data is not None and not history_data.empty and stock_info:
            # Create a two-column layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Display company name and current price info
                company_name = stock_info.get('shortName', ticker_symbol)
                st.subheader(f"{company_name} ({ticker_symbol})")
                
                current_price = stock_info.get('currentPrice', history_data['Close'].iloc[-1])
                previous_close = stock_info.get('previousClose')
                
                if current_price and previous_close:
                    price_change = current_price - previous_close
                    price_change_percent = (price_change / previous_close) * 100
                    
                    price_color = "green" if price_change >= 0 else "red"
                    sign = "+" if price_change >= 0 else ""
                    
                    st.markdown(f"""
                    <div style='display: flex; align-items: baseline;'>
                        <h2 style='margin-right: 10px;'>${current_price:.2f}</h2>
                        <span style='color: {price_color}; font-size: 18px;'>{sign}{price_change:.2f} ({sign}{price_change_percent:.2f}%)</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Create and display interactive stock chart
                st.plotly_chart(plot_stock_chart(history_data, ticker_symbol), use_container_width=True)
                
                # Historical data table with download button
                st.subheader("Historical Price Data")
                
                # Format date index for display
                formatted_data = history_data.copy()
                formatted_data.index = formatted_data.index.strftime('%Y-%m-%d')
                
                # Display the data
                st.dataframe(formatted_data)
                
                # Add download button for CSV
                st.markdown(get_table_download_link(history_data, f"{ticker_symbol}_historical_data.csv", "Download Historical Data as CSV"), unsafe_allow_html=True)
            
            with col2:
                # Display key financial metrics
                st.subheader("Key Financial Metrics")
                
                if stock_info:
                    metrics_df = get_financial_metrics(stock_info)
                    st.table(metrics_df)
                    
                    # Add download button for metrics CSV
                    st.markdown(get_table_download_link(metrics_df, f"{ticker_symbol}_financial_metrics.csv", "Download Metrics as CSV"), unsafe_allow_html=True)
                    
                    # Display company information
                    st.subheader("Company Information")
                    business_summary = stock_info.get('longBusinessSummary', 'No information available')
                    st.write(business_summary)
                else:
                    st.info("Financial metrics not available for this stock.")
        else:
            st.warning(f"No data found for symbol: {ticker_symbol}. Please check if the symbol is correct.")

# Footer
st.markdown("---")
st.write("Data provided by Yahoo Finance. Updated at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
