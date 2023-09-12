import yfinance as yf
import pandas as pd
import talib
import matplotlib.pyplot as plt

# Define the symbol and date range
symbol = "TSLA"
start_date = "2023-04-10"
end_date = "2023-09-10"

# Fetch intraday data at a 5-minute interval
data = yf.download(symbol, start=start_date, end=end_date, interval="5m")

# Calculate the Moving Averages for the data
data['SMA50'] = talib.SMA(data['Close'], timeperiod=50)
data['SMA200'] = talib.SMA(data['Close'], timeperiod=200)

# Detect Head and Shoulders pattern using TA-Lib
head_shoulders_pattern = talib.CDLHEADANDSHOULDERS(data['Open'], data['High'], data['Low'], data['Close'])

# Create a chart
plt.figure(figsize=(12, 6))
plt.plot(data.index, data['Close'], label='Close Price', color='blue')
plt.plot(data.index, data['SMA50'], label='50-minute SMA', color='orange')
plt.plot(data.index, data['SMA200'], label='200-minute SMA', color='green')

# Plot the detected Head and Shoulders pattern
plt.plot(data.index[head_shoulders_pattern > 0], data['Close'][head_shoulders_pattern > 0], 'ro', markersize=8, label='Head and Shoulders Pattern')

plt.title(f'{symbol} 5-Minute Chart with Head and Shoulders Pattern Detection')
plt.xlabel('Time')
plt.ylabel('Price')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility
plt.show()
