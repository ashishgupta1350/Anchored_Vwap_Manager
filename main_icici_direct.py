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


# def convert_to_iso8601(date_string):
#     try:
#         # Assuming the input date_string is in the format "YYYY-MM-DD HH:MM:SS"
#         # You can adjust the format if your input is different
#         dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

#         # Convert to ISO 8601 format
#         iso8601_date = dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

#         return iso8601_date
#     except ValueError:
#         return None

# def plot_data(option_data):
#     data = option_data.copy()
#     data = data[:]

#     data['close'] = data['close'].astype(float)
#     # Assuming 'put_data' is your DataFrame
#     data['datetime'] = pd.to_datetime(data['datetime'])  # Convert 'datetime' column to datetime type if it's not already

#     put_data1 = data.copy()
#     put_data1['datetime'] = data['datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))

#     # Create a line plot
#     plt.figure(figsize=(12, 6))  # Set the figure size
#     plt.plot(put_data1['datetime'], put_data1['close'], marker='o', linestyle='-')
#     plt.title('Close Price Over Time')
#     plt.xlabel('Datetime')
#     plt.ylabel('Close Price')
#     plt.grid(True)
#     plt.xticks(rotation=45)  # Rotate x-axis labels for better readability

#     plt.tight_layout()
#     plt.show()


def autologin():
    curdate = datetime.now().strftime("%d-%m-%Y")
    token_filename = 'token_' + curdate + '.txt'

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


# Assume you have logged in using breeze-connect
breeze = autologin()

# Defining global variables
time_frame_options_data = '5minute'  # 5minute, 1minute, 30minute, 1day is allowed by icici


# product_type can be "futures" , "options",

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


def get_historical_data_for_option(strike_price, option_type, from_date, to_date, expiry_date, time_interval,
                                   stock_code="NIFTY", exchange_code="NFO", product_type="options"):
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

    return pd.DataFrame(response['Success'])


def convert_to_iso8601(date_string):
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

def get_expiry_date_v2():
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


def get_expiry_date_next_to_next_thursday():
    import datetime
    today = datetime.date.today()
    days_until_next_thursday = (3 - today.weekday()) % 7
    next_thursday = today + datetime.timedelta(days=days_until_next_thursday)
    next_to_next_thursday = next_thursday + datetime.timedelta(days=7)
    last_day_of_month = datetime.date(today.year, today.month, 1) + datetime.timedelta(days=32) - datetime.timedelta(
        days=32)
    days_until_month_end_thursday = (3 - last_day_of_month.weekday()) % 7
    month_end_thursday = last_day_of_month - datetime.timedelta(days=days_until_month_end_thursday)
    if next_to_next_thursday == month_end_thursday:
        print("Next to next thursday will be a Monthly Expiry.")
    else:
        print("Next to next thursday will be Weekly Expiry.")

    return next_to_next_thursday, month_end_thursday


def get_from_date_to_date():
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


def get_nearest_strike(nifty_ltp):
    return int(round(nifty_ltp / 50.0)) * 50


def get_strikes_away(nearest_strike):
    first_strike = int(round(nearest_strike * 1.0125 / 50.0)) * 50
    second_strike = first_strike + 50
    third_strike = second_strike + 50
    return [first_strike, second_strike, third_strike]

def get_strikes_away_v2(nearest_strike):
    nearest_strike = int(nearest_strike)  # Ensure nearest_strike is an integer
    percent_away = 0.0225  # 2.25%
    first_strike = nearest_strike + int(nearest_strike * percent_away)
    first_strike = (first_strike // 100) * 100  # Round down to the nearest multiple of 100
    second_strike = first_strike + 100
    third_strike = first_strike + 200  # 100 apart from the second strike
    return [first_strike, second_strike, third_strike]

def create_position_files_with_anchors(strike, anchors):
    # print(f"anchoors are : {anchors}")
    filename_dictionary = {}
    orders_folder = "orders"
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


def get_options_ltp_icici(strike_price, expiry_date, stock_code='NIFTY', exchange_code='NFO', product_type='options',
                          right='call'):
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
def get_options_ltp_icici_v2(strike_price, expiry_date, stock_code='NIFTY', exchange_code='NFO', product_type='options',
                          right='call'):
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


def get_historical_data_for_strike(strike, expiry_date, time_frame_options_data):
    print("get_historical_data_for_strike called!")


def print_signal(strike, price_executed, buy_or_sell, time_interval):
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


stock_code = "NIFTY"
exchange_code = "NSE"
product_type = "cash"
right = "others"

# Get LTP for nifty
current_nifty_ltp = get_ltp_icici(breeze, stock_code, exchange_code, product_type, right)

# Calculate nearest strike for Nifty
nearest_strike = get_nearest_strike(current_nifty_ltp)

# Calculate strikes away in positive direction
strikes_away = get_strikes_away_v2(nearest_strike)


# Create position files for each strike
# create_position_files(strikes_away)
#
# Code variables (these stay kindof safe for entire execution of code)

time_interval = "30minute"
stock_code = "NIFTY"
exchange_code = "NSE"
product_type_nifty = "cash"

time_interval_options = "30minute"
stock_code_options = "NIFTY"
exchange_code_options = "NFO"
product_type_options = "options"

profit_threshold = 15
loss_threshold = 5

# calculate expiry date
weekly_expiry_date, monthly_expiry_date = get_expiry_date_v2()

formatted_weekly_expiry_date = weekly_expiry_date.strftime("%Y-%m-%d %H:%M:%S")
formatted_monthly_expiry_date = monthly_expiry_date.strftime("%Y-%m-%d %H:%M:%S")

# Expiry type for trading anchored vwap strategy
expiry_type = "monthly" # "weekly" or "monthly"
expiry_to_use = expiry_type

booked_profit = 0
last_booked_profit_for_strike = ""
# Monitor positions for each strike until 3:00 pm
while pd.Timestamp.now().hour < 15 or True:
    print("______________________________________________________________________________________________")
    print()
    total_profit = 0
    active_positions = []

    for i in range(len(strikes_away)):
        strike = strikes_away[i]
        print(f"___________________________Working on Strike : {strike}_______________________________")

        #         filename = os.path.join("orders", datetime.now().strftime("%m-%d-%Y"), f"{strike}.txt")
        #         with open(filename) as f:
        #             orders = f.readlines()

        ############# Get Historical Data from icici_direct ###################
        option_type = "call"
        from_date, to_date = get_from_date_to_date()
        #         weekly_expiry_date, monthly_expiry_date = get_expiry_date_next_to_next_thursday()
        #         formatted_weekly_expiry_date = weekly_expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        #         formatted_monthly_expiry_date = monthly_expiry_date.strftime("%Y-%m-%d %H:%M:%S")

        #         from_date_converted = convert_to_iso8601(from_date)
        #         to_date_converted = convert_to_iso8601(to_date)
        #         expiry_date_converted = convert_to_iso8601(expiry_date)

        time_interval = "30minute"
        stock_code = "NIFTY"
        exchange_code = "NFO"
        product_type = "options"

        if expiry_to_use == "weekly":
            ohlcv_option_data = get_historical_data_for_option(strike, option_type, from_date, to_date,
                                                           formatted_weekly_expiry_date, time_interval,
                                                           stock_code="NIFTY", exchange_code="NFO",
                                                           product_type="options")
        elif expiry_to_use == "monthly":
            ohlcv_option_data = get_historical_data_for_option(strike, option_type, from_date, to_date,
                                                               formatted_monthly_expiry_date, time_interval,
                                                               stock_code="NIFTY", exchange_code="NFO",
                                                               product_type="options")
        else:
            ohlcv_option_data = get_historical_data_for_option(strike, option_type, from_date, to_date,
                                                               formatted_monthly_expiry_date, time_interval,
                                                               stock_code="NIFTY", exchange_code="NFO",
                                                               product_type="options")
        # print("OHLCV Data is fetched!")

        ############################## Fetch LTP of option strike ###################################
        if expiry_to_use == "weekly":
            expiry_date = convert_to_iso8601(formatted_weekly_expiry_date)
        elif expiry_to_use == "monthly":
            expiry_date = convert_to_iso8601(formatted_monthly_expiry_date)
        else:
            expiry_date = convert_to_iso8601(formatted_monthly_expiry_date)
        # print(f"Expiry date for getltp option is {expiry_date} ")

        current_strike_ltp = get_options_ltp_icici_v2(strike, expiry_date, stock_code='NIFTY', exchange_code='NFO',
                                                   product_type='options', right='call')
        # print(f"current_strike_ltp is : {current_strike_ltp}")

        ######################## Get anchored_vwap for strike ##########################################
        #             anchor_value, anchor_time = get_anchors_from_dataframe(ohlcv_option_data)
        anchors = get_multiple_anchors_from_dataframe(ohlcv_option_data , expiry_type="monthly")
        # print(f"Anchors are {anchors}")
        # Create file structure for anchored positions to be stored and viewed
        filename_dictionary = create_position_files_with_anchors(strike, anchors)

        for anchor_value, anchor_time in anchors:
            print(f"________Working on Anchor_value {anchor_value} for Strike {strike} ______")
            print(f"Anchor time is {anchor_time}")
            # 1 seconds sleep for api limit
            # time.sleep(1)
            # for date, create filename_with_anchors
            #             anchor_time = anchors[-1][1]
            #             anchor_value = anchors[-1][0]
            anchor_datetime = anchor_time
            df = ohlcv_option_data.copy()
            # Set datetime column as the index
            df.set_index('datetime', inplace=True)
            df.index = pd.to_datetime(df.index)

            # Convert the anchor datetime to a pandas Timestamp
            anchor_timestamp = pd.Timestamp(anchor_datetime)

            # Filter the DataFrame based on the anchor datetime
            filtered_df = df[df.index >= anchor_timestamp].copy()  # Make a copy

            anchor_vwap = filtered_df['volume'].mul(filtered_df['close']).cumsum() / \
                          filtered_df['volume'].cumsum()

            x = len(df)
            y = len(anchor_vwap)
            nans = int(x - y)
            nan_values = pd.Series([np.nan] * nans, dtype=float)
            anchor_vwap = pd.concat([nan_values, anchor_vwap])

            current_anchor = float(anchor_vwap.iloc[-1])
            lower_range = current_anchor * 0.95
            upper_range = current_anchor * 1.05
            print(f"Got anchor : {current_anchor} , Lower_range for anchor is : {lower_range} and Current Strike {strike} LTP is : {current_strike_ltp}")

            ##################### BUY SELL and Exit conditions ######################################

            dictionary_key = f"{strike}_{str(anchor_value)}"
            orders_file = filename_dictionary[dictionary_key]
            with open(orders_file) as f:
                orders = f.readlines()
            # TODO ADD CONDTION TO CHECK IF AVERAGE OF LAST 5 CANDLE IS ABOVE THE LOWER RANGE / ANCHORED_VWAP

            ################################# New Code Addition ########################################
            if len(orders) == 0:
                # If there are no open positions , check for a buy signal
                if lower_range <= current_strike_ltp <= current_anchor:
                    # take the buy position
                    with open(orders_file, "w") as f:
                        f.write(f"{current_strike_ltp}\n")
                    # print lower_range <= current_strike_ltp <= upper_range:
                    print()
                    print(f"!!!!!!!!!!!!!!!! SELL SIGNAL !!!!!!!!!!!!!!!!!")
                    print_signal(strike, current_strike_ltp, "sell", time_interval)
                    print()
                else:
                    # Sleep for 5 seconds ( to not hit api limit and retry)
                    print(f"Current LTP {current_strike_ltp} is not in range of {lower_range} and {upper_range}")
                    print("Nothing to do for this anchor!!!")
                    time.sleep(5)
            else:
                # There is an open position, check for sl or target
                print()
                print(f"!!! There is an open position for strike {strike} , anchor {anchor_value} and anchor_time {anchor_time}!!!")
                print()
                # fetch buy price from the file
                filedata = None
                with open(orders_file, "r") as f:
                    filedata = f.read()
                f.close()
                strike_buy_price = float(filedata)

                pnl = strike_buy_price - current_strike_ltp

                # Add to active positions list
                active_positions.append([strike, pnl, anchor_value, anchor_time])

                print(f"Pnl points is {pnl}")
                print(f"Waiting for profit of Rs. {(strike_buy_price * profit_threshold) / 100.0}")
                print(f"Will Exit at loss of Rs. {(strike_buy_price * loss_threshold) / 100.0}")
                total_profit += pnl
                # check if buy price - current_ltp hits target, if it does, book profit, exit and clean the file
                if pnl > (strike_buy_price * profit_threshold) / 100.0:
                    booked_profit += pnl
                    last_booked_profit_for_strike = strike
                    print(f"Profit threshold of {profit_threshold} % reached for strike {strike}")
                    print(f"Price of purchase was {strike_buy_price} & Current LTP is {current_strike_ltp}")
                    print(f"Points profit is {pnl}. Exiting trade! ")
                    with open(orders_file, "w") as f:
                        f.write("")
                # check if buy price (-) current ltp hits my sl , if it does, exit and clean the file
                elif pnl < -1*(strike_buy_price * loss_threshold) / 100.0:
                    booked_profit += pnl
                    last_booked_profit_for_strike = strike

                    print(f"Pnl is {pnl} which is less than {loss_threshold} % of {strike_buy_price}")
                    print(f"Loss threshold of {loss_threshold} % reached for strike {strike}")
                    print(f"Price of purchase was {strike_buy_price} & Current LTP is {current_strike_ltp}")
                    print(f"Points loss is {pnl}. Exiting trade! ")
                    with open(orders_file, "w") as f:
                        f.write("")

            # if lower_range <= current_strike_ltp <= upper_range:
            #     # If no position exists for the strike, do this
            #     if len(orders) == 0:
            #         # take the buy position
            #         with open(orders_file, "w") as f:
            #             f.write(f"{current_strike_ltp}\n")
            #         # print lower_range <= current_strike_ltp <= upper_range:
            #         print()
            #         print(f"!!!!!!!!!!!!!!!! SELL SIGNAL !!!!!!!!!!!!!!!!!")
            #         print_signal(strike, current_strike_ltp, "sell", time_interval)
            #         print()
            #
            #     # else if there is an open position, check for sl or target
            #     else:
            #         # fetch buy price from the file
            #         filedata = None
            #         with open(orders_file, "r") as f:
            #             filedata = f.read()
            #         f.close()
            #         strike_buy_price = float(filedata)
            #
            #         pnl = current_strike_ltp - strike_buy_price
            #
            #         # check if buy price - current_ltp hits target, if it does, book profit, exit and clean the file
            #         if pnl > (strike_buy_price * profit_threshold) / 100.0:
            #             print(f"Profit threshold of {profit_threshold} % reached for strike {strike}")
            #             print(f"Price of purchase was {strike_buy_price} & Current LTP is {current_strike_ltp}")
            #             print(f"Points profit is {pnl}. Exiting trade! ")
            #             with open(orders_file, "w") as f:
            #                 f.write("")
            #         # check if buy price (-) current ltp hits my sl , if it does, exit and clean the file
            #         elif pnl < -1*(strike_buy_price * loss_threshold) / 100.0:
            #             print(f"Pnl is {pnl} which is less than {loss_threshold} % of {strike_buy_price}")
            #             print(f"Loss threshold of {loss_threshold} % reached for strike {strike}")
            #             print(f"Price of purchase was {strike_buy_price} & Current LTP is {current_strike_ltp}")
            #             print(f"Points loss is {pnl}. Exiting trade! ")
            #             with open(orders_file, "w") as f:
            #                 f.write("")
            # else:
            #     # Sleep for 5 seconds ( to not hit api limit and retry)
            #     print(f"Current LTP {current_strike_ltp} is not in range of {lower_range} and {upper_range}")
            #     print("Nothing to do for this anchor!!!")
            #     time.sleep(5)

            print("__________________________________________________________")
            print()

    # stop execution for 10 seconds to not hit api limit
    print("Waiting 10 seconds to run code again....")
    print()
    print("________________________________________________________________________")
    print(f"Total Profit is {total_profit + booked_profit} (Incl. Current Positions)")
    print(f"Total Booked Profit is {booked_profit}")
    print(f"Last Booked Profit was for strike : {last_booked_profit_for_strike}")
    print(f"Active Position and it's pnl are : ")
    for positions in active_positions:
        print(f"Strike : {positions[0]} , Pnl : {positions[1]} , Anchor : {positions[2]} , Anchor Time : {positions[3]}")
    print("________________________________________________________________________")
    time.sleep(10)

print("Its 3:00 pm or later, exiting all the strikes, clearing the files!")
# # Exit all positions and erase all orders file after 3:00 pm
# for i in range(len(strikes_away)):
#     filename = os.path.join("orders", datetime.now().strftime("%m-%d-%Y"), f"{strikes_away[i]}.txt")
#     with open(filename, "w") as f:
#         f.write("")
