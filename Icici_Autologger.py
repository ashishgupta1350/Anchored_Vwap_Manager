from pyotp import TOTP
from selenium import webdriver
import time
import urllib.parse
import urllib
# from breezeapi import BreezeConnect
import login as l
from datetime import datetime
from breeze_connect import BreezeConnect
def autologin():
    curdate = datetime.now().strftime("%d-%m-%Y")
    token_filename = 'token_' + curdate + '.txt'

    #check if token_filename exists and is not empty
    try:
        with open(token_filename, 'r') as f:
            token = f.read()
            if token:
                breeze = BreezeConnect(api_key=l.api_key)
                breeze.generate_session(api_secret=l.api_secret, session_token=token)
                print(breeze.get_funds())
    except Exception as e:
        print("Token does not exits or is empty")
        print("Getting token now!")

    browser = webdriver.Chrome()
    browser.get("https://api.icicidirect.com/apiuser/Login?api_key="+urllib.parse.quote_plus(l.api_key))
    browser.implicitly_wait(5)
    breeze = BreezeConnect(api_key=l.api_key)


    username = browser.find_element("xpath",'/html/body/form/div[2]/div/div/div[1]/div[2]/div/div[1]/input')
    password = browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[1]/div[2]/div/div[3]/div/input')

    username.send_keys(l.userID)
    password.send_keys(l.password)
    #Checkbox
    browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[1]/div[2]/div/div[4]/div/input').click()

    # Click Login Button
    browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[1]/div[2]/div/div[5]/input[1]').click()
    time.sleep(2)
    pin = browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[2]/div/div[2]/div[2]/div[3]/div/div[1]/input')
    totp = TOTP(l.totp)
    token = totp.now()
    pin.send_keys(token)
    browser.find_element("xpath", '/html/body/form/div[2]/div/div/div[2]/div/div[2]/div[2]/div[4]/input[1]').click()
    time.sleep(1)


    temp_token=browser.current_url.split('apisession=')[1][:8]
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

autologin()