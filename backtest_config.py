import pandas as pd
import os
from datetime import timedelta
from pyotp import TOTP
from datetime import datetime
from selenium import webdriver
import time
import urllib.parse
import urllib
# from breezeapi import BreezeConnect
import login as l
from breeze_connect import BreezeConnect
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt


def autologin():
    curdate = datetime.now().strftime("%d-%m-%Y")
    token_filename = r'C:\Users\ashis\OneDrive\Desktop\Anchored_Vwap_Code\login_details\token_' + curdate + '.txt'
    # token_filename = 'token_' + curdate + '.txt'

    # check if token_filename exists and is not empty
    try:
        with open(token_filename, 'r') as f:
            token = f.read()
            if token:
                breeze = BreezeConnect(api_key=l.api_key)
                breeze.generate_session(api_secret=l.api_secret, session_token=token)
                print(breeze.get_funds())
                return breeze
    except Exception as e:
        print("Token does not exits or is empty")
        print("Getting token now!")

    browser = webdriver.Chrome()
    browser.get("https://api.icicidirect.com/apiuser/Login?api_key=" + urllib.parse.quote_plus(l.api_key))
    browser.implicitly_wait(5)
    breeze = BreezeConnect(api_key=l.api_key)

    username = browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[1]/div[2]/div/div[1]/input')
    password = browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[1]/div[2]/div/div[3]/div/input')

    username.send_keys(l.userID)
    password.send_keys(l.password)
    # Checkbox
    browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[1]/div[2]/div/div[4]/div/input').click()

    # Click Login Button
    browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[1]/div[2]/div/div[5]/input[1]').click()
    time.sleep(2)
    pin = browser.find_element("xpath",
                               '/html/body/form/div[2]/div/div/div[2]/div/div[2]/div[2]/div[3]/div/div[1]/input')
    totp = TOTP(l.totp)
    token = totp.now()
    pin.send_keys(token)
    browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[2]/div/div[2]/div[2]/div[4]/input[1]').click()
    time.sleep(1)

    temp_token = browser.current_url.split('apisession=')[1][:8]
    print('Generated token is as follows: ', temp_token)
    # save temp_token to token.txt
    with open(token_filename, 'w') as f:
        f.write(temp_token)
    token = lambda: open(token_filename, 'r').read()

    # Save in Database or text File
    print('temp_token', token())
    breeze.generate_session(api_secret=l.api_secret, session_token=temp_token)

    print(breeze.get_funds())
    browser.quit()
    return breeze


def num_days_in_dataframe(df):
    # Convert the date strings to datetime objects
    start_date_str = str(df['datetime'].iloc[0])
    end_date_str = str(df['datetime'].iloc[-1])
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
    # Calculate the difference between end_date and start_date
    date_difference = end_date - start_date
    # Extract the number of days from the difference
    number_of_days = date_difference.days
    return number_of_days


def get_anchors_from_dataframe(df):
    # Find the highest value in the 'high' column
    df_copy = df.copy()
    df_copy['high'] = pd.to_numeric(df_copy['high'], errors='coerce')
    df_copy.set_index('datetime', inplace=True)

    highest_high = df_copy['high'].max()

    # Find the index (row) where the highest value occurs
    index_of_highest_high = df_copy['high'].idxmax()

    return highest_high, index_of_highest_high


def get_n_days_data_from_dataframe(df, days):
    df_copy = df.copy()
    df_copy['datetime'] = pd.to_datetime(df_copy['datetime'])
    n = days

    end_date = df_copy["datetime"].max()
    start_date = end_date - timedelta(days=n)
    n_days_data = df_copy[df_copy['datetime'] >= start_date]
    return n_days_data


def get_multiple_anchors_from_dataframe(train_data, expiry_type="monthly"):
    """
    Gets multiple anchors from a dataframe
    :param train_data:  Dataframe with datetime and high columns
    :param expiry_type:
    :return:
    """
    if expiry_type == "monthly":
        smallest_anchor_days = 25
        mid_anchor_days = 45
    elif expiry_type == "weekly":
        smallest_anchor_days = 9
        mid_anchor_days = 17
    else:
        print("Invalid expiry_type passed to get_multiple_anchors_from_dataframe")
        return None
    num_days = num_days_in_dataframe(train_data)
    if num_days < smallest_anchor_days:
        a, b = get_anchors_from_dataframe(train_data)
        return [[a, b]]
    elif smallest_anchor_days <= num_days <= mid_anchor_days:
        global_anchor, global_anchor_timeframe = get_anchors_from_dataframe(train_data)

        seven_days_data = get_n_days_data_from_dataframe(train_data, smallest_anchor_days)
        seven_day_anchor, seven_day_anchor_timeframe = get_anchors_from_dataframe(seven_days_data)
        return [[global_anchor, global_anchor_timeframe], [seven_day_anchor, seven_day_anchor_timeframe]]
    elif num_days >= mid_anchor_days:
        global_anchor, global_anchor_timeframe = get_anchors_from_dataframe(train_data)
        seven_days_data = get_n_days_data_from_dataframe(train_data, smallest_anchor_days)
        seven_day_anchor, seven_day_anchor_timeframe = get_anchors_from_dataframe(seven_days_data)
        two_weeks_data = get_n_days_data_from_dataframe(train_data, mid_anchor_days)
        two_weeks_data_anchor, two_weeks_data_anchor_timeframe = get_anchors_from_dataframe(two_weeks_data)
        return [[global_anchor, global_anchor_timeframe], [two_weeks_data_anchor, two_weeks_data_anchor_timeframe],
                [seven_day_anchor, seven_day_anchor_timeframe]]

    else:
        return None


#

# ICICI returns at max 1000 candles for data at a time, to get more than 1000 candles, we need to make multiple requests
def get_stock_fut_index_data_helper(breeze, from_date, to_date, time_interval, stock_code="NIFTY", exchange_code="NSE",
                                  product_type="cash"):
    """

        :param breeze: BreezeConnect object
        :param from_date: Ex: "2023-04-19 12:34:56"
        :param to_date: Ex : "2023-09-06 12:34:56"
        :param time_interval: Ex "5minute" , "1minute" , "30minute" , "1day"
        :param stock_code: "NIFTY" , "BANKNIFTY" ETC
        :param exchange_code: "NSE" , "BSE" ETC
        :param product_type: "options"
        :return: Historical data for a stock / future/ index, expiry date as : pd.DataFrame(response['Success'])
        """
    #     from_date = "2023-04-19 12:34:56"
    #     to_date = "2023-09-06 12:34:56"
    #     time_interval = "5minute"
    #     product_type="cash"
    #     stock_code="NIFTY"
    #     exchange_code = "NSE"
    #     print()
    #     print("STOCK DATA in getHistoricalData: ")
    #     print(f"From Date: {from_date}")
    #     print(f"To Date: {to_date}")
    #     print(f"Time Interval: {time_interval}")
    #     print(f"Product Type: {product_type}")
    #     print(f"Stock Code: {stock_code}")
    #     print(f"Exchange Code: {exchange_code}")
    #     print()

    from_date_converted = convert_to_iso8601(from_date)
    to_date_converted = convert_to_iso8601(to_date)

    response = None
    try:
        response = breeze.get_historical_data_v2(interval=time_interval,
                                                 from_date=str(from_date_converted),
                                                 to_date=str(to_date_converted),
                                                 stock_code=stock_code,
                                                 exchange_code=exchange_code,
                                                 product_type=product_type)
    except Exception as e:
        time.sleep(1)
        try:
            response = breeze.get_historical_data_v2(interval=time_interval,
                                                     from_date=str(from_date_converted),
                                                     to_date=str(to_date_converted),
                                                     stock_code=stock_code,
                                                     exchange_code=exchange_code,
                                                     product_type=product_type)
        except Exception as e:
            print("breeze.get_historical_data_v2 did not respond. Probably api isn't working properly. Check ASAP!")
            return []
    if response['Success'] == []:
        print(f"Error recieving data for stock: {stock_code}")
        print("More information: ")
        # from_date = "2023-04-19 12:34:56"
        # to_date = "2023-09-06 12:34:56"
        # time_interval = "5minute"
        # product_type = "cash"
        # stock_code = "NIFTY"
        # exchange_code = "NSE"
        print()
        print("STOCK DATA in getHistoricalData: ")
        print(f"From Date: {from_date}")
        print(f"To Date: {to_date}")
        print(f"Time Interval: {time_interval}")
        print(f"Product Type: {product_type}")
        print(f"Stock Code: {stock_code}")
        print(f"Exchange Code: {exchange_code}")
        print()
        print("Returning [] for response!")
        return response['Success']
    return response['Success']

def get_historical_data_for_stock_fut_index(breeze, from_date, to_date, time_interval, stock_code="NIFTY", exchange_code="NSE",
                                  product_type="cash"):

    data = get_stock_fut_index_data_helper(breeze, from_date, to_date, time_interval, stock_code, exchange_code, product_type)
    if len(data) < 1000:
        return data
    else:
        while True:
            to_date_new = data[0]['datetime']
            from_date = from_date
            time.sleep(1)
            data_new = get_stock_fut_index_data_helper(breeze, from_date, to_date_new, time_interval, stock_code, exchange_code, product_type)
            # data = data_new - the last point of data_new + data
            data = data_new[:-1] + data
            if len(data_new) < 1000:
                return data


def get_historical_data_for_option_helper(breeze, strike_price, option_type, from_date, to_date, expiry_date, time_interval,
                                   stock_code="NIFTY", exchange_code="NFO", product_type="options"):
    """

    :param strike_price: INT : Example: 19500
    :param option_type: Striing : Example: "call"
    :param from_date: Ex: "2023-04-19 12:34:56"
    :param to_date: Ex : "2023-09-06 12:34:56"
    :param expiry_date: Ex :"2023-09-14 00:00:00"
    :param time_interval: Ex "5minute" , "1minute" , "30minute" , "1day"
    :param stock_code: "NIFTY" , "BANKNIFTY" ETC
    :param exchange_code: "NSE" , "BSE" ETC
    :param product_type: "options"
    :return: Historical data for option with given strike price, expiry date as : pd.DataFrame(response['Success'])
    """
    #     from_date = "2023-04-19 12:34:56"
    #     to_date = "2023-09-06 12:34:56"
    #     expiry_date = "2023-09-14 00:00:00"
    #     time_interval = "5minute"
    #     product_type="options"
    #     stock_code="NIFTY"
    #     exchange_code = "NFO"
    #     strike_price = 19500
    #     option_type = "call"
    #     print()
    #     print("OPTION DATA in getHistoricalData: ")
    #     print(f"From Date: {from_date}")
    #     print(f"To Date: {to_date}")
    #     print(f"Expiry Date: {expiry_date}")
    #     print(f"Time Interval: {time_interval}")
    #     print(f"Product Type: {product_type}")
    #     print(f"Stock Code: {stock_code}")
    #     print(f"Exchange Code: {exchange_code}")
    #     print(f"Strike Price: {strike_price}")
    #     print(f"Option Type: {option_type}")
    #     print()

    from_date_converted = convert_to_iso8601(from_date)
    to_date_converted = convert_to_iso8601(to_date)
    expiry_date_converted = convert_to_iso8601(expiry_date)

    response = None
    try:
        response = breeze.get_historical_data_v2(interval=time_interval,
                                                 from_date=str(from_date_converted),
                                                 to_date=str(to_date_converted),
                                                 stock_code=stock_code,
                                                 exchange_code=exchange_code,
                                                 product_type=product_type,
                                                 expiry_date=str(expiry_date_converted),
                                                 right=option_type,
                                                 strike_price=str(strike_price))
    except Exception as e:
        time.sleep(1)
        try:
            response = breeze.get_historical_data_v2(interval=time_interval,
                                                     from_date=str(from_date_converted),
                                                     to_date=str(to_date_converted),
                                                     stock_code=stock_code,
                                                     exchange_code=exchange_code,
                                                     product_type=product_type,
                                                     expiry_date=str(expiry_date_converted),
                                                     right=option_type,
                                                     strike_price=str(strike_price))
        except Exception as e:
            print("breeze.get_historical_data_v2 did not respond. Probably api isn't working properly. Check ASAP!")
            return []
    if response['Success'] == []:
        print(f"Error recieving data for strike: {strike_price} for expiry: {expiry_date}")
        print("More information: ")
        print(f"From Date: {from_date}")
        print(f"To Date: {to_date}")
        print(f"Expiry Date: {expiry_date}")
        print(f"Time Interval: {time_interval}")
        print(f"Product Type: {product_type}")
        print(f"Stock Code: {stock_code}")
        print(f"Exchange Code: {exchange_code}")
        print(f"Strike Price: {strike_price}")
        print(f"Option Type: {option_type}")
        print()
        print("Returning [] for response!")
        return response['Success']

    return response['Success']


def get_historical_data_for_option(breeze, strike_price, option_type, from_date, to_date, expiry_date, time_interval,
                                   stock_code="NIFTY", exchange_code="NFO", product_type="options"):
    """

    :param strike_price: INT : Example: 19500
    :param option_type: Striing : Example: "call"
    :param from_date: Ex: "2023-04-19 12:34:56"
    :param to_date: Ex : "2023-09-06 12:34:56"
    :param expiry_date: Ex :"2023-09-14 00:00:00"
    :param time_interval: Ex "5minute" , "1minute" , "30minute" , "1day"
    :param stock_code: "NIFTY" , "BANKNIFTY" ETC
    :param exchange_code: "NSE" , "BSE" ETC
    :param product_type: "options"
    :return: Historical data for option with given strike price, expiry date as : pd.DataFrame(response['Success'])
    """
    if from_date == "auto":
        from_date = "1990-08-01 12:34:56"
    if to_date == "auto":
        to_date = "2100-09-06 12:34:56"

    data = get_historical_data_for_option_helper(breeze, strike_price, option_type, from_date, to_date, expiry_date, time_interval,
                                   stock_code, exchange_code, product_type)
    if len(data) < 1000:
        return pd.DataFrame(data)

    else:
        while True:
            to_date_new = data[0]['datetime']
            from_date = from_date
            time.sleep(1)
            data_new = get_historical_data_for_option_helper(breeze, strike_price, option_type, from_date, to_date_new, expiry_date, time_interval,
                                   stock_code, exchange_code, product_type)
            # data = data_new - the last point of data_new + data
            data = data_new[:-1] + data
            if len(data_new) < 1000:
                return pd.DataFrame(data)


def get_complete_historical_data_for_option(breeze, strike_price, option_type, expiry_date, time_interval,
                                   stock_code="NIFTY", exchange_code="NFO", product_type="options"):
    """
    Gets total historical data for option automatically without inputing from and to date
    :param strike_price: INT : Example: 19500
    :param option_type: Striing : Example: "call"
    :param from_date: Ex: "2023-04-19 12:34:56"
    :param to_date: Ex : "2023-09-06 12:34:56"
    :param expiry_date: Ex :"2023-09-14 00:00:00"
    :param time_interval: Ex "5minute" , "1minute" , "30minute" , "1day"
    :param stock_code: "NIFTY" , "BANKNIFTY" ETC
    :param exchange_code: "NSE" , "BSE" ETC
    :param product_type: "options"
    :return: Historical data for option with given strike price, expiry date as : pd.DataFrame(response['Success'])
    """
    #     from_date = "2023-04-19 12:34:56"
    #     to_date = "2023-09-06 12:34:56"
    #     expiry_date = "2023-09-14 00:00:00"
    #     time_interval = "5minute"
    #     product_type="options"
    #     stock_code="NIFTY"
    #     exchange_code = "NFO"
    #     strike_price = 19500
    #     option_type = "call"
    #     print()
    #     print("OPTION DATA in getHistoricalData: ")
    #     print(f"From Date: {from_date}")
    #     print(f"To Date: {to_date}")
    #     print(f"Expiry Date: {expiry_date}")
    #     print(f"Time Interval: {time_interval}")
    #     print(f"Product Type: {product_type}")
    #     print(f"Stock Code: {stock_code}")
    #     print(f"Exchange Code: {exchange_code}")
    #     print(f"Strike Price: {strike_price}")
    #     print(f"Option Type: {option_type}")
    #     print()
    # from_date = "2023-04-19 12:34:56"
    # to_date = "2023-09-06 12:34:56"
    # super far from and to dates to get all the data for every option
    from_date = "1990-08-01 12:34:56"
    to_date = "2100-09-06 12:34:56"
    from_date_converted = convert_to_iso8601(from_date)
    to_date_converted = convert_to_iso8601(to_date)
    expiry_date_converted = convert_to_iso8601(expiry_date)

    response = None
    try:
        response = breeze.get_historical_data_v2(interval=time_interval,
                                                 from_date=str(from_date_converted),
                                                 to_date=str(to_date_converted),
                                                 stock_code=stock_code,
                                                 exchange_code=exchange_code,
                                                 product_type=product_type,
                                                 expiry_date=str(expiry_date_converted),
                                                 right=option_type,
                                                 strike_price=str(strike_price))
    except Exception as e:
        time.sleep(1)
        try:
            response = breeze.get_historical_data_v2(interval=time_interval,
                                                     from_date=str(from_date_converted),
                                                     to_date=str(to_date_converted),
                                                     stock_code=stock_code,
                                                     exchange_code=exchange_code,
                                                     product_type=product_type,
                                                     expiry_date=str(expiry_date_converted),
                                                     right=option_type,
                                                     strike_price=str(strike_price))
        except Exception as e:
            print("breeze.get_historical_data_v2 did not respond. Probably api isn't working properly. Check ASAP!")
            return []
    if response['Success'] == []:
        print(f"Error recieving data for strike: {strike_price} for expiry: {expiry_date}")
        print("More information: ")
        print(f"From Date: {from_date}")
        print(f"To Date: {to_date}")
        print(f"Expiry Date: {expiry_date}")
        print(f"Time Interval: {time_interval}")
        print(f"Product Type: {product_type}")
        print(f"Stock Code: {stock_code}")
        print(f"Exchange Code: {exchange_code}")
        print(f"Strike Price: {strike_price}")
        print(f"Option Type: {option_type}")
        print()
        print("Returning [] for response!")
        return response['Success']

    return pd.DataFrame(response['Success'])


def convert_to_iso8601(date_string):
    """

    :param date_string: Format YYYY-MM-DD HH:MM:SS
    :return: iso8601_date in format YYYY-MM-DDTHH:MM:SS.000Z required for ICICI
    """
    try:
        # Assuming the input date_string is in the format "YYYY-MM-DD HH:MM:SS"
        # You can adjust the format if your input is different
        dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

        # Convert to ISO 8601 format
        iso8601_date = dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        return iso8601_date
    except ValueError:
        return None


def plot_data(option_data):
    """

    :param option_data: Gets options OHLCV data and plots it by close and datetime fields (Data has datetime and close fields)
    """
    data = option_data.copy()
    data = data[:]

    data['close'] = data['close'].astype(float)
    # Assuming 'put_data' is your DataFrame
    data['datetime'] = pd.to_datetime(
        data['datetime'])  # Convert 'datetime' column to datetime type if it's not already

    put_data1 = data.copy()
    put_data1['datetime'] = data['datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))

    # Create a line plot
    plt.figure(figsize=(12, 6))  # Set the figure size
    plt.plot(put_data1['datetime'], put_data1['close'], marker='o', linestyle='-')
    plt.title('Close Price Over Time')
    plt.xlabel('Datetime')
    plt.ylabel('Close Price')
    plt.grid(True)
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability

    plt.tight_layout()
    plt.show()


def plot_ohlc_v2(ohlcv_option_data):
    """

    :param ohlcv_option_data:  Gets options OHLCV data and plots it by close and datetime fields (Data has datetime and close fields)
    Does not require index to be converted to string
    """
    df = ohlcv_option_data.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['close'] = pd.to_numeric(df['close'])

    # Set datetime column as the index
    df.set_index('datetime', inplace=True)

    # Define your anchor datetime (you can replace this with your specific anchor datetime)
    anchor_datetime = "2023-08-17 15:30:00"

    # Convert the anchor datetime to a pandas Timestamp
    anchor_timestamp = pd.Timestamp(anchor_datetime)

    # Filter the DataFrame based on the anchor datetime
    filtered_df = df[df.index >= anchor_timestamp].copy()  # Make a copy

    # Calculate VWAP in the copy
    filtered_df['vwap'] = (filtered_df['close'] * filtered_df['volume']).cumsum() / filtered_df['volume'].cumsum()
    # Create a candlestick chart using mplfinance
    ohlc = mpf.make_addplot(filtered_df, type='candle', panel=0)
    vwap = mpf.make_addplot(filtered_df['vwap'], panel=0, color='blue', secondary_y=False)

    mpf.plot(filtered_df, type='candle', addplot=[ohlc, vwap], style='yahoo',
             title="Candlestick Chart with Anchored VWAP")
    plt.show()


# def get_expiry_date():

#     today = datetime.date.today()
#     days_until_next_thursday = (3 - today.weekday()) % 7
#     next_thursday = today + datetime.timedelta(days=days_until_next_thursday)
#     last_day_of_month = datetime.date(today.year, today.month, 1) + datetime.timedelta(days=32) - datetime.timedelta(days=32)
#     days_until_month_end_thursday = (3 - last_day_of_month.weekday()) % 7
#     month_end_thursday = last_day_of_month - datetime.timedelta(days=days_until_month_end_thursday)
#     if next_thursday == month_end_thursday:
#         print("Next expiry is a Monthly Expiry.")
#     else:
#         print("Next expiry is a Weekly Expiry.")

#     return next_thursday, month_end_thursday


def get_expiry_date_for_candle(expiry_name, expiry_type, day, month, year):
    """
    Given a day, month, and year, this function returns the next expiry date for the given expiry_name and expiry_type

    :param expiry_name: "nifty" , "sensex" , "banknifty" , "midcap" , "finnifty"
    :param expiry_type: "weekly" , "monthly"
    :param day: 1-31
    :param month: 1-12
    :param year: any year (int)
    :return: Returns the next expiry date for the given expiry_name, expiry_type, day, month, and year
    """
    # Define a dictionary to map expiry names to their respective weekday
    expiry_day_mapping = {
        "nifty": 3,  # Thursday
        "sensex": 4,  # Friday
        "banknifty": 2,  # Wednesday
        "midcap": 0,  # Monday
        "finnifty": 1  # Tuesday
    }

    # Determine the day of the week for the specified expiry_name
    if expiry_name in expiry_day_mapping:
        expiry_day = expiry_day_mapping[expiry_name]
    else:
        raise ValueError("Invalid expiry_name")

    # Create a datetime object for the specified day, month, and year
    specified_date = dt.datetime(year, month, day)

    if expiry_type == "weekly":
        # Calculate the number of days to add for weekly expiry
        days_until_expiry = (expiry_day - specified_date.weekday() + 7) % 7

        # Calculate the expiry date by adding the days_until_expiry to the specified date
        expiry_date = specified_date + dt.timedelta(days=days_until_expiry)
    elif expiry_type == "monthly":
        # Calculate the last day of the month for the specified month and year
        last_day_of_month = dt.datetime(year, month, 1) + dt.timedelta(days=31)
        while last_day_of_month.month != month:
            last_day_of_month -= dt.timedelta(days=1)

        # Find the last weekday (Monday to Friday) of the month
        while last_day_of_month.weekday() != expiry_day:
            last_day_of_month -= dt.timedelta(days=1)

        expiry_date = last_day_of_month
    else:
        raise ValueError("Invalid expiry_type")


    return expiry_date


def get_expiry_date_v2():
    """

    :return: Returns the next to next thursday and last thursday of the current month (From Today)
    """
    # Get today's date
    today = dt.date.today()

    # Find the day of the week (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
    day_of_week = today.weekday()

    # Calculate the number of days to the next Thursday
    days_until_next_thursday = (3 - day_of_week + 7) % 7

    # Calculate the date of the next Thursday
    next_thursday = today + dt.timedelta(days=days_until_next_thursday)

    # Calculate the date of the next to next Thursday (7 days from next Thursday)
    next_to_next_thursday = next_thursday + dt.timedelta(days=7)

    # Calculate the last Thursday of the current month
    last_day_of_month = dt.date(today.year, today.month, 1) + dt.timedelta(days=32)
    last_thursday = last_day_of_month.replace(day=1) - dt.timedelta(days=1)

    while last_thursday.weekday() != 3:
        last_thursday -= dt.timedelta(days=1)

    return next_to_next_thursday, last_thursday


# def get_expiry_date_next_to_next_thursday():
#     import datetime
#     today = datetime.date.today()
#     days_until_next_thursday = (3 - today.weekday()) % 7
#     next_thursday = today + datetime.timedelta(days=days_until_next_thursday)
#     next_to_next_thursday = next_thursday + datetime.timedelta(days=7)
#     last_day_of_month = datetime.date(today.year, today.month, 1) + datetime.timedelta(days=32) - datetime.timedelta(
#         days=32)
#     days_until_month_end_thursday = (3 - last_day_of_month.weekday()) % 7
#     month_end_thursday = last_day_of_month - datetime.timedelta(days=days_until_month_end_thursday)
#     if next_to_next_thursday == month_end_thursday:
#         print("Next to next thursday will be a Monthly Expiry.")
#     else:
#         print("Next to next thursday will be Weekly Expiry.")
#
#     return next_to_next_thursday, month_end_thursday
#

def get_from_date_to_date():
    """

    :return: five months ago and 2 months forward to capture all the data of option (By default, if you give really big time frame,
             it returns all the candles available) (MAX 1000 candles / request)
    """
    # Get today's date
    today = datetime.today()
    # Calculate the date 5 months back
    five_months_ago = today - timedelta(days=5 * 30)  # Assuming an average of 30 days per month
    # Calculate the date 2 months forward
    two_months_forward = today + timedelta(days=2 * 30)  # Assuming an average of 30 days per month
    # Format the dates as strings in the desired format
    formatted_five_months_ago = five_months_ago.strftime("%Y-%m-%d %H:%M:%S")
    formatted_two_months_forward = two_months_forward.strftime("%Y-%m-%d %H:%M:%S")

    from_date = formatted_five_months_ago
    to_date = formatted_two_months_forward
    return from_date, to_date


def get_nearest_strike_v2(symbol_ltp, difference_between_strikes = 50):
    """
    Generic function to get the nearest strike to the symbol_ltp
    :param symbol_ltp: Generic symbol LTP to get the nearest strike (19223 -> 19200)
    :param difference_between_strikes: 50 for nifty, 100 for banknifty , sensex, 25 for midcap
    :return: nearest strike to the nifty_ltp
    """
    return int(round(symbol_ltp / float(difference_between_strikes))) * difference_between_strikes


def get_strikes_away(nearest_strike):
    """

    :param nearest_strike:  19000 (Nifty LTP rounded to nearest strike ex 19223 -> 19200)
    :return: returns 3 strikes in the multiple of 50 (19000 -> [19200, 19250, 19300]) (1.25% away from LTP , +50 , +100)
    """
    first_strike = int(round(nearest_strike * 1.0125 / 50.0)) * 50
    second_strike = first_strike + 50
    third_strike = second_strike + 50
    return [first_strike, second_strike, third_strike]


def get_strikes_away_v2(nearest_strike):
    """

    :param nearest_strike: nearest_strike:  19000 (Nifty LTP rounded to nearest strike ex 19223 -> 19200)
    :return: returns 3 strikes in the multiple of 100 (18800 -> [19200, 19300, 19400]) (2.25% away from LTP , +100 , +200)
    """
    nearest_strike = int(nearest_strike)  # Ensure nearest_strike is an integer
    percent_away = 0.0075  # 0.75% away
    first_strike = nearest_strike + int(nearest_strike * percent_away)
    first_strike = (first_strike // 100) * 100  # Round down to the nearest multiple of 100
    second_strike = first_strike + 100
    third_strike = first_strike + 200  # 100 apart from the second strike
    return [first_strike, second_strike, third_strike]


def create_position_files_with_anchors(strike, anchors, backtesting = False):
    """

    :param backtesting: False or True
    :param strike: INT : Example: 19500
    :param anchors: Array of Anchors tuples : Example: [(235, "2023-09-06 12:34:56"), (123, "2023-08-12 10:55:03")]
    :return:
    """
    # print(f"anchoors are : {anchors}")
    filename_dictionary = {}
    orders_folder = "orders"

    if backtesting:
        orders_folder = "backtesting_orders"

    today_folder = datetime.now().strftime("%m-%d-%Y")
    if not os.path.exists(orders_folder):
        os.mkdir(orders_folder)
    if not os.path.exists(os.path.join(orders_folder, today_folder)):
        os.mkdir(os.path.join(orders_folder, today_folder))
    for anchor_value, anchor_time in anchors:
        filename = f"{strike}_{str(anchor_value)}.txt"
        # Define the file path
        file_path = os.path.join(orders_folder, today_folder, filename)

        dictionary_key = f"{strike}_{str(anchor_value)}"
        filename_dictionary[dictionary_key] = file_path

        # Check if the file exists
        if os.path.exists(file_path):
            # print(f"The file {file_path} exists.")
            pass
        else:
            # print(f"The file {file_path} does not exist.")
            with open(os.path.join(orders_folder, today_folder, filename), "w") as f:
                f.write("")
                # for date, create filename_with_anchors
    return filename_dictionary


def create_position_files(strikes):
    orders_folder = "orders"
    today_folder = datetime.now().strftime("%m-%d-%Y")
    if not os.path.exists(orders_folder):
        os.mkdir(orders_folder)
    if not os.path.exists(os.path.join(orders_folder, today_folder)):
        os.mkdir(os.path.join(orders_folder, today_folder))
    for strike in strikes:
        with open(os.path.join(orders_folder, today_folder, f"{strike}.txt"), "w") as f:
            f.write("")


def get_ltp_icici(breeze, stock_code, exchange_code="NSE", product_type="cash", right="others"):
    # todo : edit comments for this function later
    """

    :param breeze: breeze_api_point_of_contact
    :param stock_code: "NIFTY", "BANKNIFTY" ETC
    :param exchange_code: "NSE" , "BSE" ETC
    :param product_type: "cash" etc
    :param right: "others" etc
    :return:
    """
    current_nifty_ltp = None
    try:
        nifty_object = breeze.get_quotes(stock_code=stock_code,
                                         exchange_code=exchange_code,
                                         product_type=product_type,
                                         right=right)
        current_nifty_ltp = float(nifty_object['Success'][0]['ltp'])
    except Exception as e:
        try:
            # print("Problem fetching nifty ltp from BREEZE_CONNECT!")
            time.sleep(0.3)
            # print("Retrying to get nifty ltp from breeze_connect!")
            nifty_object = breeze.get_quotes(stock_code=stock_code,
                                             exchange_code=exchange_code,
                                             product_type=product_type,
                                             right=right)
            current_nifty_ltp = float(nifty_object['Success'][0]['ltp'])
        except Exception as e:
            print("Failed to get nifty ltp, returning None ")
            return None
    return current_nifty_ltp


def get_options_ltp_icici(breeze, strike_price, expiry_date, stock_code='NIFTY', exchange_code='NFO',
                          product_type='options',
                          right='call'):
    """

    :param strike_price: Ex: 19200
    :param expiry_date: Ex : "2023-09-14 00:00:00"
    :param stock_code: Ex : "NIFTY"
    :param exchange_code: Ex : "NFO"
    :param product_type: Ex : "options"
    :param right: Ex : "call"
    :return: Option LTP
    """
    options_ltp = None
    try:
        nifty_object = breeze.get_quotes(
            stock_code=stock_code,
            exchange_code=exchange_code,
            expiry_date=expiry_date,
            product_type=product_type,
            right=right,
            strike_price=strike_price
        )
        options_ltp = float(nifty_object['Success'][0]['ltp'])
    except Exception as e:
        try:
            # print(f"Problem fetching options : {strike_price} ltp from BREEZE_CONNECT!")
            time.sleep(0.3)
            # print(f"Retrying to get options : {strike_price} ltp from breeze_connect!")
            nifty_object = breeze.get_quotes(
                stock_code=stock_code,
                exchange_code=exchange_code,
                expiry_date=expiry_date,
                product_type=product_type,
                right=right,
                strike_price=strike_price
            )
            options_ltp = float(nifty_object['Success'][0]['ltp'])
        except Exception as e:
            print(f"Failed to get options : {strike_price} ltp, returning None ")
            return None
    return options_ltp


# Tries 5 times to get options ltp before returning none
def get_options_ltp_icici_v2(breeze, strike_price, expiry_date, stock_code='NIFTY', exchange_code='NFO',
                             product_type='options',
                             right='call'):
    """
    Tries 5 times to get option LTP from ICICI before returning as None. Sometimes ICICi API doesn't respond properly.

    :param strike_price: Ex: 19200
    :param expiry_date: Ex : "2023-09-14 00:00:00"
    :param stock_code: Ex : "NIFTY"
    :param exchange_code: Ex : "NFO"
    :param product_type: Ex : "options"
    :param right: Ex : "call"
    :return: Option LTP
    """
    options_ltp = None
    max_retries = 5  # Maximum number of retries

    for attempt in range(max_retries):
        try:
            nifty_object = breeze.get_quotes(
                stock_code=stock_code,
                exchange_code=exchange_code,
                expiry_date=expiry_date,
                product_type=product_type,
                right=right,
                strike_price=strike_price
            )
            options_ltp = float(nifty_object['Success'][0]['ltp'])
            break  # Success, exit the loop
        except Exception as e:
            print(f"Attempt {attempt + 1} failed to get options : {strike_price} ltp")
            if attempt < max_retries - 1:
                print("Retrying...")
                time.sleep(0.5)
            else:
                print(f"All {max_retries} attempts failed. Returning None.")
                return None

    return options_ltp


def print_signal(strike, price_executed, buy_or_sell, time_interval):
    """
    Prints signal in a certain format (Way to clean code a bit)
    :param strike: Ex: 19200
    :param price_executed: Ex : 52
    :param buy_or_sell: Ex : "SELL" or "BUY"
    :param time_interval:  Ex : "30minute"
    :return: Nothing
    """
    current_datetime = datetime.now()
    current_hour = current_datetime.hour
    current_minute = current_datetime.minute
    current_second = current_datetime.second
    # Generate signal!
    if (buy_or_sell == "buy"):
        print("Signal Generated - BUY_SIGNAL")
    else:
        print("Signal Generated - SELL_SIGNAL")

    print("Signal Details")
    print(f"LTP: {price_executed}")
    print(f"Current Time: {current_hour}:{current_minute}:{current_second}")
    print(f"Strike price: {strike}")
    print(f"Charting Timeframe: {time_interval}")
    return
