from IPython.display import display, HTML

display(HTML("<style>.container { width:90% !important; }</style>"))

import os

import backtest_config
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import timedelta
import time
import talib
cur_path = "C:\\Users\\ashis\\OneDrive\\Desktop\\Anchored_Vwap_Code\\"


# Function to parse the date string
def parse_date(date_str):
    # Split the string to extract the date part without timezone
    date_part = date_str.split(' GMT')[0]
    # Parse the date using the specified format
    return datetime.strptime(date_part, '%a %b %d %Y %H:%M:%S')


def num_days_in_dataframe(df):
    # Convert the date strings to datetime objects
    start_date_str = str(df['parsed_date'].iloc[0])
    end_date_str = str(df['parsed_date'].iloc[-1])
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
    # Calculate the difference between end_date and start_date
    date_difference = end_date - start_date
    # Extract the number of days from the difference
    number_of_days = date_difference.days
    return number_of_days


def get_anchors_from_dataframe(df):
    # Find the highest value in the 'high' column
    #     df['High'] = pd.to_numeric(df['High'], errors='coerce')

    df_copy = df.copy()
    df_copy['High'] = pd.to_numeric(df_copy['High'], errors='coerce')

    highest_high = df_copy['High'].max()

    # Find the index (row) where the highest value occurs
    index_of_highest_high = df_copy['High'].idxmax()
    #     print(f"The highest value in the 'high' column is: {highest_high}")
    #     print(f"The index of the highest value is: {index_of_highest_high}")

    return highest_high, index_of_highest_high


def fetch_data():
    #     df = pd.read_csv(cur_path + 'option_data\\17 aug 45500ce 5min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\17 aug 46000ce 5 min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\17 aug 46500ce 15min.csv', skiprows=2)

    #     df = pd.read_csv(cur_path + 'option_data\\17 aug 45500ce 15min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\10 aug 46500ce 15min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\24 aug 46500ce 15min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\24 aug 46500ce 5min.csv', skiprows=2)

    #     df = pd.read_csv(cur_path + 'option_data\\17 aug 46000ce 5 min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\17 aug 46500ce 5min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\17 aug 45500ce 5min.csv', skiprows=2)

    #     df = pd.read_csv(cur_path + 'option_data\\7 sep 45000ce 15min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\7 sep 45500ce 15min.csv', skiprows=2)
    df = pd.read_csv(cur_path + 'option_data\\7 sep 46000ce 15min.csv', skiprows=2)
    #     df = pd.read_csv(cur_path + 'option_data\\24 aug 46000ce 15min.csv', skiprows=2)
    df.columns = ["Open", "High", "Low", "Close", "Volume", "OpenInterest", "temp"]
    df.drop(["temp"], axis=1, inplace=True)
    df['parsed_date'] = df.index.to_series().apply(parse_date)
    return df


def convert_index_to_datetime(df):
    index = [datetime.strptime(date, "%a %b %d %Y %H:%M:%S %Z%z (India Standard Time)") for date in df.index]
    df = pd.DataFrame(df.values, columns=df.columns, index=index)
    return df


def get_n_days_data_from_dataframe(df, days):
    n = days
    end_date = df["parsed_date"].max()
    start_date = end_date - timedelta(days=n)
    n_days_data = df[df['parsed_date'] >= start_date]
    return n_days_data


def get_multiple_anchors_from_dataframe(train_data):
    num_days = num_days_in_dataframe(train_data)
    if num_days < 9:
        a, b = get_anchors_from_dataframe(train_data)
        return [[a, b]]
    elif 9 <= num_days <= 17:
        global_anchor, global_anchor_timeframe = get_anchors_from_dataframe(train_data)

        seven_days_data = get_n_days_data_from_dataframe(train_data, 7)
        seven_day_anchor, seven_day_anchor_timeframe = get_anchors_from_dataframe(seven_days_data)
        return [[global_anchor, global_anchor_timeframe], [seven_day_anchor, seven_day_anchor_timeframe]]
    elif num_days >= 17:
        global_anchor, global_anchor_timeframe = get_anchors_from_dataframe(train_data)
        seven_days_data = get_n_days_data_from_dataframe(train_data, 7)
        seven_day_anchor, seven_day_anchor_timeframe = get_anchors_from_dataframe(seven_days_data)
        two_weeks_data = get_n_days_data_from_dataframe(train_data, 14)
        two_weeks_data_anchor, two_weeks_data_anchor_timeframe = get_anchors_from_dataframe(two_weeks_data)
        return [[global_anchor, global_anchor_timeframe], [two_weeks_data_anchor, two_weeks_data_anchor_timeframe],
                [seven_day_anchor, seven_day_anchor_timeframe]]
    else:
        return None


def advanced_backtesting_icici(from_date, to_date, time_interval, product_type, stock_code, exchange_code, expiry_name):
    expiry_name = "nifty"
    # from_date = "2023-01-19 12:34:56"
    from_date = "2022-01-19 10:34:56"
    to_date = "2023-09-06 12:34:56"
    time_interval = "30minute"
    product_type = "cash"
    stock_code = "NIFTY"
    exchange_code = "NSE"

    # For options to test
    time_interval_options = time_interval
    stock_code_options = stock_code
    exchange_code_options = "NFO"
    product_type_options = "options"
    expiry_type_options = "monthly"
    expiry_name_options = "nifty"
    # Algo thresholds
    lower_range_threshold = 95/100.0
    upper_range_threshold = 105/100.0

    profit_threshold = 0.25  # 75% profit threshold
    loss_threshold = -0.10  # 25% loss threshold (negative value)
    total_pnl = 0  # Initialize total P&L
    amount_to_invest = 10000000  # Initial investment amount
    stop_loss_percentage = 0.01  # 1% stop loss


    # for caching data
    cache_folder = "cached_strike_data"
    # Ensure the cache folder exists
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    # Algo variables
    positions_dictionary = {}
    buy_price_dictionary = {}
    sell_price_dictionary = {}

    difference_between_strikes = 50
    if stock_code == "NIFTY":
        difference_between_strikes = 50
    elif stock_code == "BANKNIFTY":
        difference_between_strikes = 100
    elif stock_code == "FINNIFTY":
        difference_between_strikes = 50
    elif stock_code == "MIDCAP":
        difference_between_strikes = 25
    elif stock_code == "SENSEX":
        difference_between_strikes = 100

    daily_start_time = "09:25:00"
    daily_end_time = "15:15:00"

    breeze = backtest_config.autologin()

    # todo , cache this data into a file and read from it if it exists
    data = backtest_config.get_historical_data_for_stock_fut_index(breeze, from_date, to_date, time_interval,
                                                                   stock_code, exchange_code, product_type)
    df = pd.DataFrame(data)
    # Convert the 'datetime' column to a pandas datetime object
    df['datetime'] = pd.to_datetime(df['datetime'])
    # Extract the year , month and day into separate columns
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['day'] = df['datetime'].dt.day
    # Get unique years from the 'year' column
    unique_years = df['year'].unique()

    # Strike dataframe cached to avoid repeated api calls for same strikes
    strike_df_cache = {}

    symbol_data_until_candle = pd.DataFrame(columns=df.columns)
    # total booked profit for all the data?
    booked_profit = 0

    # Iterate over each year
    for year in unique_years:
        # Get unique months for the current year
        unique_months = df[df['year'] == year]['month'].unique()
        print(f"In year {year}, there are {len(unique_months)} months in data")
        # Iterate over each month in the current year
        for month in unique_months:
            # Get unique days for the current month in the current year
            unique_days = df[(df['year'] == year) & (df['month'] == month)]['day'].unique()
            print(f"In month {month} of year {year}")
            # Iterate over each day in the current month in the current year
            print(f"No. of days in month {month} of year {year} : {len(unique_days)}")



            for day in unique_days:
                # reset the buy_price_dictionary and sell_price_dictionary for each day
                print("\n\n")
                buy_price_dictionary = {}
                sell_price_dictionary = {}
                positions_dictionary = {}

                print(f"Working on day {day} of month {month} of year {year}")
                # Filter the DataFrame to get data for the current year, month, and day
                filtered_data = df[(df['year'] == year) & (df['month'] == month) & (df['day'] == day)]

                # calculate expiry date using day
                expiry_date_options = backtest_config.get_expiry_date_for_candle_v2(expiry_name_options,
                                                                                 expiry_type_options, day, month, year)

                print(f"Expiry date for {day}-{month}-{year} is {expiry_date_options}")
                # using the first candle of the day in filtered_df, calculate the nearest strike, strikes away and get historical data for it
                symbol_candle_day = filtered_data.iloc[0]
                # get data until given candle
                symbol_ltp = float(symbol_candle_day['close'])
                print(f"Day's {day}-{month}-{year} first candle LTP : {symbol_ltp}")

                # Calculate nearest strike for Nifty
                nearest_strike_integer = backtest_config.get_nearest_strike_v2(symbol_ltp,
                                                                               difference_between_strikes=difference_between_strikes)
                # Calculate strikes away in positive direction
                strikes_away = backtest_config.get_strikes_away_v2(nearest_strike_integer)
                print(f"No. of candles in day {day}-{month}-{year} : {len(filtered_data)}")
                # Get historical data for strike and store it into cache if not present
                for strike in strikes_away:
                    cache_name = str(strike) + str(expiry_date_options)
                    sanitized_cache_name = backtest_config.sanitize_filename(cache_name)
                    cache_path = os.path.join(cache_folder, sanitized_cache_name + ".csv")
                    # READ DATA FROM CACHE BEFORE CALLING API
                    if os.path.exists(cache_path):
                        # If it exists, load it from the CSV file
                        strike_df = pd.read_csv(cache_path)
                    else:
                        strike_df = backtest_config.get_historical_data_for_option(breeze, strike, "call", "auto",
                                                                                   "auto", str(expiry_date_options),
                                                                                   time_interval,
                                                                                   stock_code=stock_code_options,
                                                                                   exchange_code=exchange_code_options,
                                                                                   product_type=product_type_options)
                        # Cache the data into a CSV file
                        strike_df.to_csv(cache_path, index=False)

                    # if strike_df_cache.get(str(strike) + str(expiry_date_options)) is not None:
                    #     strike_df = strike_df_cache.get(str(strike) + str(expiry_date_options))
                    # else:
                    #     strike_df = backtest_config.get_historical_data_for_option(breeze, strike, "call", "auto",
                    #                                                                "auto", str(expiry_date_options),
                    #                                                                time_interval,
                    #                                                                stock_code=stock_code_options,
                    #                                                                exchange_code=exchange_code_options,
                    #                                                                product_type=product_type_options)
                    #     # cache the strike df
                    #     cache_name = str(strike) + str(expiry_date_options)
                    # Store the DataFrame in the cache
                    strike_df_cache[sanitized_cache_name] = strike_df

                # Iterate over each candle and get current candle data
                for index, symbol_candle in filtered_data.iterrows():

                    # cumilative data for symbol until current candle (Ex nifty until 10:30 am)
                    # symbol_data_until_candle = df[df['datetime'] <= symbol_candle['datetime']]
                    print(f"Time : {(symbol_candle['datetime'].strftime('%H:%M:%S'))}___________________")

                    # Anchored vwap logic as if the code is running live
                    for i in range(len(strikes_away)):
                        strike = strikes_away[i]
                        candle_time_formatted = pd.Timestamp(symbol_candle["datetime"]).time()
                        print(f"______________Working on Strike : {strike} , Time : {candle_time_formatted}___________________")
                        option_type = "call"
                        from_date = "auto"
                        to_date = "auto"
                        cache_name = str(strike) + str(expiry_date_options)
                        sanitized_cache_name = backtest_config.sanitize_filename(cache_name)
                        strike_df_until_symbol_candle = strike_df_cache.get(sanitized_cache_name).copy()

                        # Assuming symbol_candle['datetime'] is a datetime object
                        symbol_datetime = symbol_candle['datetime']
                        # Convert the 'datetime' column in strike_df_until_symbol_candle to datetime objects
                        strike_df_until_symbol_candle['datetime'] = strike_df_until_symbol_candle['datetime'].apply(
                            lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
                        )
                        # get historical data for strike until given candle using cache created earlier
                        strike_df_until_symbol_candle = strike_df_until_symbol_candle[
                            strike_df_until_symbol_candle['datetime'] <= symbol_datetime]
                        strike_df_until_symbol_candle = strike_df_until_symbol_candle.reset_index(drop=True)
                        strike_df_until_symbol_candle['ema100'] = talib.EMA(strike_df_until_symbol_candle['close'],
                                                                           timeperiod=100)
                        strike_df_until_symbol_candle['ema50'] = talib.EMA(strike_df_until_symbol_candle['close'],
                                                                           timeperiod=50)

                        # get last strike candle data
                        strike_current_candle = strike_df_until_symbol_candle.iloc[-1]
                        # todo : average this with high and low + close to maybe get an average price during candle's
                        #  existance
                        current_strike_ltp = float(strike_current_candle['close'])

                        anchors = backtest_config.get_multiple_anchors_from_dataframe(strike_df_until_symbol_candle,
                                                                                      expiry_type=expiry_type_options)

                        # filename_dictionary = backtest_config.create_position_files_with_anchors(strike, anchors, backtesting=True)
                        current_close_price = float(strike_current_candle["close"])

                        current_time = pd.Timestamp(symbol_candle["datetime"]).time()
                        if current_time <= pd.Timestamp("09:30:00").time():
                            # we dont take trades before 9:30
                            print(f"_________________________ Time is : {current_time} It's before 9:30\n_____________________________")
                            continue
                        if current_time >= pd.Timestamp("15:00:00").time():
                            for anchor_value, anchor_time in anchors:
                                # check if positions_dictionary[anchor_time] exists
                                if positions_dictionary.get(anchor_time) is None:
                                    positions_dictionary[anchor_time] = None
                                elif positions_dictionary[anchor_time] == "sell":
                                    positions_dictionary[anchor_time] = "buy"
                                    print("_________________________ Time is : {current_time} It's End of Day\n_____________________________")
                                    backtest_config.temp_plot_ohlcv_v2(strike_df_until_symbol_candle, anchor_time)
                                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                                    total_pnl += pnl
                                    print("Found a BUY SIGNAL (End of Day)")
                                    print("Date: " + str(strike_current_candle["datetime"]))
                                    print("Buy Price: " + str(current_close_price))
                                    print("P&L: {:.2f}".format(pnl))
                                    print(
                                        "End of day " + str(current_time) + ". Total P&L: {:.2f}".format(total_pnl))
                                    print("---------------------------------------------------------------------")
                                    print()
                                # Reset position to None
                                positions_dictionary[anchor_time] = None
                            print(f"_________________________ Time is : {current_time} It's End of Day\n_____________________________")

                            continue

                        for anchor_value, anchor_time in anchors:
                            #             print(f"working on anchor {anchor_time}")
                            #                             print(anchors)
                            #                             backtest_config.temp_plot_ohlcv(strike_df_until_symbol_candle, anchor_time)
                            #                             time.sleep(8)
                            print(f"For strike {strike} , working on anchor {anchor_value} at {anchor_time} for expiry {expiry_date_options}")
                            if anchor_time in positions_dictionary.keys():
                                pass
                            else:
                                # print("setting to none")
                                # print(f" {anchor_time} not found in vault")
                                positions_dictionary[anchor_time] = None
                                buy_price_dictionary[anchor_time] = None
                                sell_price_dictionary[anchor_time] = None

                            #             anchor_value, anchor_time = get_anchors_from_dataframe(train_data)
                            anchor_timeframe = anchor_time

                            strike_temporary_df = strike_df_until_symbol_candle.copy()
                            # Set datetime column as the index
                            strike_temporary_df.set_index('datetime', inplace=True)
                            strike_temporary_df.index = pd.to_datetime(strike_temporary_df.index)
                            # Filter the DataFrame based on the anchor datetime
                            filtered_df = strike_temporary_df[
                                strike_temporary_df.index >= anchor_timeframe].copy()  # Make a copy

                            # Calculate the anchored VWAP
                            anchor_vwap = filtered_df['volume'].mul(filtered_df['high']).cumsum() / \
                                          filtered_df['volume'].cumsum()

                            x = len(strike_df_until_symbol_candle)
                            y = len(anchor_vwap)
                            nans = int(x - y)
                            nan_values = pd.Series([np.nan] * nans, dtype=float)
                            #         extended_series = pd.concat([nan_values, anchor_vwap])
                            anchor_vwap = pd.concat([nan_values, anchor_vwap])

                            current_close_price = float(strike_current_candle["close"])
                            current_anchor = float(anchor_vwap.iloc[-1])
                            lower_range = current_anchor * lower_range_threshold
                            upper_range = current_anchor * upper_range_threshold

                            ################ one of the sell logics ############################
                            column_name = 'high'
                            if len(strike_df_until_symbol_candle) >= 5:
                                # Calculate the average of the last 5 candles if there are at least 5 rows
                                average_last_5_candles = strike_df_until_symbol_candle[column_name].tail(5).mean()
                            else:
                                # Calculate the average of all available rows if there are fewer than 5 rows
                                average_last_5_candles = strike_df_until_symbol_candle[column_name].mean()

                            ############## Second: Not sell logic #################################
                            ema100 = float(strike_df_until_symbol_candle['ema100'].iloc[-1])
                            ema50 = float(strike_df_until_symbol_candle['ema50'].iloc[-1])
                            ############################ Buy / sell code conditions ###########################
                            if positions_dictionary[anchor_time] is None:
                                # First condition is always a sell when there's no position
                                if current_close_price >= current_anchor:
                                    print(f"Current close price {current_close_price} is greater than current anchor {current_anchor}")
                                    print(f"We ignore this signal")
                                    pass
                                elif average_last_5_candles >= current_anchor:
                                    print(f"Average of last 5 candles {average_last_5_candles} is greater than current anchor {current_anchor}")
                                    print(f"We ignore this signal")
                                    pass
                                elif average_last_5_candles >= 0.95*anchors[0][0]:
                                    print(f"Average of last 5 candles {average_last_5_candles} higher than ema 100: {ema100}")
                                    print(f"We ignore this signal")
                                    pass
                                elif ema50 > ema100:
                                    print(
                                        f"Market is in supposed uptrend, with ema50: {ema50} higher than ema100: {ema100}")
                                    print(f"We ignore this signal")
                                    pass
                                elif lower_range <= current_close_price:

                                    backtest_config.temp_plot_ohlcv_v2(strike_df_until_symbol_candle, anchor_time)

                                    sell_price_dictionary[anchor_time] = current_close_price
                                    positions_dictionary[anchor_time] = "sell"
                                    print("Found a SELL SIGNAL (First Signal)")
                                    print("Date: " + str(strike_current_candle["datetime"]))
                                    print("Sell Price: " + str(sell_price_dictionary[anchor_time]))

                                    print("Total P&L: {:.2f}".format(total_pnl))
                                    print("\n")

                                    # time.sleep(0.3)
                                else:
                                    print("No signal found")
                            elif positions_dictionary[anchor_time] == "sell":
                                if (sell_price_dictionary[anchor_time] - current_close_price) >= (
                                        profit_threshold * sell_price_dictionary[anchor_time]):
                                    # Buy when profit reaches 25%
                                    print(anchors)
                                    backtest_config.temp_plot_ohlcv_v2(strike_df_until_symbol_candle, anchor_time)

                                    positions_dictionary[anchor_time] = "buy"
                                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                                    total_pnl += pnl
                                    print("Found a BUY SIGNAL (Profit)")
                                    print("Date: " + str(strike_current_candle["datetime"]))
                                    print("Buy Price: " + str(current_close_price))
                                    print("P&L: {:.2f}".format(pnl))

                                    print("Total P&L: {:.2f}".format(total_pnl))
                                    print("\n")
                                    # time.sleep(0.3)
                                elif (sell_price_dictionary[anchor_time] - current_close_price) <= (
                                        loss_threshold * sell_price_dictionary[anchor_time]):
                                    print(anchors)
                                    backtest_config.temp_plot_ohlcv_v2(strike_df_until_symbol_candle, anchor_time)

                                    # Buy when loss reaches 25%
                                    positions_dictionary[anchor_time] = "buy"
                                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                                    total_pnl += pnl
                                    print("Found a BUY SIGNAL (Loss)")
                                    print("Date: " + str(strike_current_candle["datetime"]))
                                    print("Buy Price: " + str(current_close_price))
                                    print("P&L: {:.2f}".format(pnl))

                                    print("Total P&L: {:.2f}".format(total_pnl))
                                    print("\n")

                                    # time.sleep(0.3)
                                elif (total_pnl + (sell_price_dictionary[anchor_time] - current_close_price)) <= -(
                                        stop_loss_percentage * amount_to_invest):
                                    # Exit position completely if total loss exceeds 1% of amount_to_invest
                                    positions_dictionary[anchor_time] = "buy"
                                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                                    total_pnl += pnl
                                    print("Found a BUY SIGNAL (Stop Loss)")
                                    print("Date: " + str(strike_current_candle["datetime"]))
                                    print("Buy Price: " + str(current_close_price))
                                    print("P&L: {:.2f}".format(pnl))
                                    print("Stop Loss Hit. Total Loss: {:.2f}".format(total_pnl))
                                else:
                                    print("There already exists a position. But no buyback signal was found.")
                                    print(
                                        f"Selling price = {sell_price_dictionary[anchor_time]} , Current price = {current_close_price}")
                                    print(
                                        f"Profit/loss in this trade currently = {sell_price_dictionary[anchor_time] - current_close_price}")
                                    print(f"time is {current_time}")
                            elif positions_dictionary[anchor_time] == "buy":
                                # Check for take profit
                                if total_pnl >= (profit_threshold * amount_to_invest):
                                    positions_dictionary[anchor_time] = "buy"
                                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                                    total_pnl += pnl
                                    print("Found a BUY SIGNAL (Take Profit)")
                                    print("Date: " + str(strike_current_candle["datetime"]))
                                    print("Buy Price: " + str(current_close_price))
                                    print("P&L: {:.2f}".format(pnl))
                                    print("Take Profit Hit. Total Profit: {:.2f}".format(total_pnl))

                        # for anchor_value, anchor_time in anchors:
                        #     # Ensure the last position is a buy if not already
                        #     if positions_dictionary[anchor_time] == "sell":
                        #         positions_dictionary[anchor_time] = "buy"
                        #         pnl = sell_price_dictionary[anchor_time] - current_close_price
                        #         total_pnl += pnl
                        #         print("Found a BUY SIGNAL (End of Data)")
                        #         print("Date: " + str(candle_data["parsed_date"]))
                        #         print("Buy Price: " + str(current_close_price))
                        #         print("P&L: {:.2f}".format(pnl))
                        #         print("End of Data. Total P&L: {:.2f}".format(total_pnl))
                        #
                        # print("Total P&L: {:.2f}".format(total_pnl))


def backtest_actual():
    df = fetch_data()
    number_of_days = num_days_in_dataframe(df)
    print(f"Number of days in the date range: {number_of_days} days")

    # Calculate the index at which to split the data (70% for training)
    split_index = int(0.3 * len(df))

    # Split the DataFrame into training and testing sets
    train_data = df.iloc[:split_index]  # First 70% of the data
    test_data = df.iloc[split_index:]  # Remaining 30% of the data

    print(f"len_train_data: {len(train_data)} ,,, len_test_data: {len(test_data)} ")

    train_data = convert_index_to_datetime(train_data)
    test_data = convert_index_to_datetime(test_data)

    # Convert OHLCV values to float/int for vwap calculations
    train_data['Open'] = train_data['Open'].astype(float)
    train_data['High'] = train_data['High'].astype(float)
    train_data['Low'] = train_data['Low'].astype(float)
    train_data['Close'] = train_data['Close'].astype(float)
    train_data['Volume'] = train_data['Volume'].astype(int)  # If Volume is expected to be an integer
    #     lower_range_arr = []
    #     upper_range_arr = []

    ####################### Code to buy / sell ################################

    profit_threshold = 0.75  # 75% profit threshold
    loss_threshold = -0.25  # 25% loss threshold (negative value)
    total_pnl = 0  # Initialize total P&L
    amount_to_invest = 10000  # Initial investment amount
    stop_loss_percentage = 0.01  # 1% stop loss
    positions_dictionary = {}

    buy_price_dictionary = {}
    sell_price_dictionary = {}
    anchors = get_multiple_anchors_from_dataframe(train_data)
    print(anchors)
    for idx in range(len(test_data)):
        # Test data candle -> Append to Train data
        # Calculate Anchored Vwap for the new Train_Data
        # Check if current_candle_close is in range of AnchoredVwap
        # if it is, Buy condition

        candle_data = test_data.iloc[idx]

        # Check if it's past 3:00 pm and exit all existing positions
        current_time = pd.Timestamp(candle_data["parsed_date"]).time()
        if current_time >= pd.Timestamp("15:00:00").time():
            for anchor_value, anchor_time in anchors:
                if positions_dictionary[anchor_time] == "sell":
                    positions_dictionary[anchor_time] = "buy"
                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                    total_pnl += pnl
                    print("Found a BUY SIGNAL (End of Day)")
                    print("Date: " + str(candle_data["parsed_date"]))
                    print("Buy Price: " + str(current_close_price))
                    print("P&L: {:.2f}".format(pnl))
                    print("End of day " + str(current_time) + ". Total P&L: {:.2f}".format(total_pnl))
                    print("---------------------------------------------------------------------")
                    print()
                # Reset position to None
                positions_dictionary[anchor_time] = None

        parsed_date = candle_data["parsed_date"]
        row_to_append_df = pd.DataFrame([candle_data], columns=train_data.columns)
        train_data = pd.concat([train_data, row_to_append_df])

        # Check if the time is within the intraday trading window (9:20 am to 3:00 pm)
        trading_start_time = parsed_date.replace(hour=9, minute=20, second=0)
        trading_end_time = parsed_date.replace(hour=15, minute=0, second=0)
        ################### Multiple anchors code
        #         anchors = get_multiple_anchors_from_dataframe(train_data)

        #         print(f"No of anchor {len(anchors)}")
        if parsed_date < trading_start_time:
            continue  # Skip this data point if before 9:20 am
        elif parsed_date >= trading_end_time:
            continue  # Stop trading if it's 3:00 pm or later
        for anchor_value, anchor_time in anchors:
            #             print(f"working on anchor {anchor_time}")
            if anchor_time in positions_dictionary.keys():
                pass
            else:
                print("setting to none")
                print(f" {anchor_time} not found in vault")
                positions_dictionary[anchor_time] = None
                buy_price_dictionary[anchor_time] = None
                sell_price_dictionary[anchor_time] = None

            #             anchor_value, anchor_time = get_anchors_from_dataframe(train_data)
            anchor_timeframe = anchor_time

            anchor_vwap = train_data.loc[anchor_timeframe:]['Volume'].mul(
                train_data.loc[anchor_timeframe:]['Close']).cumsum() / \
                          train_data.loc[anchor_timeframe:]['Volume'].cumsum()

            x = len(train_data)
            y = len(anchor_vwap)
            nans = int(x - y)
            nan_values = pd.Series([np.nan] * nans, dtype=float)
            #         extended_series = pd.concat([nan_values, anchor_vwap])
            anchor_vwap = pd.concat([nan_values, anchor_vwap])

            current_close_price = float(candle_data["Close"])
            current_anchor = float(anchor_vwap.iloc[-1])
            lower_range = current_anchor * 0.85
            upper_range = current_anchor * 1.15

            ############################ Buy / sell code conditions ###########################
            if positions_dictionary[anchor_time] is None:
                # First condition is always a sell when there's no position
                if lower_range <= current_close_price:
                    sell_price_dictionary[anchor_time] = current_close_price
                    positions_dictionary[anchor_time] = "sell"
                    print("Found a SELL SIGNAL (First Signal)")
                    print("Date: " + str(candle_data["parsed_date"]))
                    print("Sell Price: " + str(sell_price_dictionary[anchor_time]))
            elif positions_dictionary[anchor_time] == "sell":
                if (sell_price_dictionary[anchor_time] - current_close_price) >= (
                        profit_threshold * sell_price_dictionary[anchor_time]):
                    # Buy when profit reaches 25%
                    positions_dictionary[anchor_time] = "buy"
                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                    total_pnl += pnl
                    print("Found a BUY SIGNAL (Profit)")
                    print("Date: " + str(candle_data["parsed_date"]))
                    print("Buy Price: " + str(current_close_price))
                    print("P&L: {:.2f}".format(pnl))
                elif (sell_price_dictionary[anchor_time] - current_close_price) <= (
                        loss_threshold * sell_price_dictionary[anchor_time]):
                    # Buy when loss reaches 25%
                    positions_dictionary[anchor_time] = "buy"
                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                    total_pnl += pnl
                    print("Found a BUY SIGNAL (Loss)")
                    print("Date: " + str(candle_data["parsed_date"]))
                    print("Buy Price: " + str(current_close_price))
                    print("P&L: {:.2f}".format(pnl))
                elif (total_pnl + (sell_price_dictionary[anchor_time] - current_close_price)) <= -(
                        stop_loss_percentage * amount_to_invest):
                    # Exit position completely if total loss exceeds 1% of amount_to_invest
                    positions_dictionary[anchor_time] = "buy"
                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                    total_pnl += pnl
                    print("Found a BUY SIGNAL (Stop Loss)")
                    print("Date: " + str(candle_data["parsed_date"]))
                    print("Buy Price: " + str(current_close_price))
                    print("P&L: {:.2f}".format(pnl))
                    print("Stop Loss Hit. Total Loss: {:.2f}".format(total_pnl))
            elif positions_dictionary[anchor_time] == "buy":
                # Check for take profit
                if total_pnl >= (profit_threshold * amount_to_invest):
                    positions_dictionary[anchor_time] = "buy"
                    pnl = sell_price_dictionary[anchor_time] - current_close_price
                    total_pnl += pnl
                    print("Found a BUY SIGNAL (Take Profit)")
                    print("Date: " + str(candle_data["parsed_date"]))
                    print("Buy Price: " + str(current_close_price))
                    print("P&L: {:.2f}".format(pnl))
                    print("Take Profit Hit. Total Profit: {:.2f}".format(total_pnl))
            print("Total P&L: {:.2f}".format(total_pnl))

    for anchor_value, anchor_time in anchors:
        # Ensure the last position is a buy if not already
        if positions_dictionary[anchor_time] == "sell":
            positions_dictionary[anchor_time] = "buy"
            pnl = sell_price_dictionary[anchor_time] - current_close_price
            total_pnl += pnl
            print("Found a BUY SIGNAL (End of Data)")
            print("Date: " + str(candle_data["parsed_date"]))
            print("Buy Price: " + str(current_close_price))
            print("P&L: {:.2f}".format(pnl))
            print("End of Data. Total P&L: {:.2f}".format(total_pnl))

    ############################ Buy / sell code conditions ###########################


#     x = len(train_data)
#     y = len(lower_range_arr)
#     nans = int(x-y)
#     nan_values = pd.Series([np.nan] * nans, dtype=float)
# #     lower_range_arr = pd.concat([nan_values, pd.Series(lower_range_arr)])
# #     upper_range_arr = pd.concat([nan_values, pd.Series(upper_range_arr)])
#     apd = mpf.make_addplot( anchor_vwap.values, color='blue', title='Anchored VWAP')
# #     apd1 = mpf.make_addplot( lower_range_arr, color='red', title='asdf VWAP')
# #     apd2 = mpf.make_addplot( upper_range_arr, color='green', title='da VWAP')
# #     mpf.plot(train_data, type='candle', style='yahoo', volume=True, addplot=[apd, apd1, apd2])
#     mpf.plot(train_data, type='candle', style='yahoo', volume=True, addplot=[apd, apd1])
#     plt.show()

def backtest():
    df = fetch_data()
    number_of_days = num_days_in_dataframe(df)
    print(f"Number of days in the date range: {number_of_days} days")

    # Calculate the index at which to split the data (70% for training)
    split_index = int(0.7 * len(df))

    # Split the DataFrame into training and testing sets
    train_data = df.iloc[:split_index]  # First 70% of the data
    test_data = df.iloc[split_index:]  # Remaining 30% of the data
    train_data = convert_index_to_datetime(train_data)
    test_data = convert_index_to_datetime(test_data)

    backtest_actual()


def strategy_main():
    expiry_name = "nifty"
    from_date = "2023-04-19 12:34:56"
    to_date = "2023-09-06 12:34:56"
    time_interval = "30minute"
    product_type = "cash"
    stock_code = "NIFTY"
    exchange_code = "NSE"
    advanced_backtesting_icici(from_date, to_date, time_interval, product_type, stock_code, exchange_code, expiry_name)


#     test_temp()


if __name__ == '__main__':
    strategy_main()
