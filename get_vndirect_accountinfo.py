import requests
import json
import pandas as pd

def get_login_token():
    login_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJpc3N1ZXIiLCJzdWIiOiJzdWJqZWN0IiwiYXVkIjpbImF1ZGllbmNlIiwiaW9zIiwib25saW5lIiwidHJhZGVhcGkiLCJhdXRoIl0sImV4cCI6MTYxODI2MDk2OSwibmJmIjoxNjE4MjE3NDY5LCJ0cmFkaW5nRXhwIjowLCJpZGdJZCI6bnVsbCwicm9sZXMiOiJbXSIsImFjY291bnRUeXBlIjoiVW5rbm93biIsImN1c3RvbWVySWQiOiIwMDAxMTY2MjY3IiwidXNlcklkIjoibnVsbCIsInZlcnNpb24iOiJWMiIsImN1c3RvbWVyTmFtZSI6Ik5ndXnhu4VuIEhvw6BpIELDo28iLCJlbWFpbCI6ImhvYWliYW8ubmhiQGdtYWlsLmNvbSIsInVzZXJuYW1lIjoiaG9haWJhbzQ0OTMiLCJzdGF0dXMiOiJBQ1RJVkFURUQifQ.3Dysqnnu6IfK_Gf7uxbsjtZZqkYIjmDhGKwh6EAlwSaabkyrGPrs3A3SnQI1e8QZZlULSWL6WQ9fcRKAooAsO7PRAP8md-waaAfB1o9j6_5h0ZMDoCJrKBpW4HdzUdqvnYey9BrqM283i-RkNxXilZ1Pqi8phF_SCxPhWw880mTXjq7jjsL-rC0RWGv9E7LuK4K_s0u2rVhaR1dTHR-0JtfKleZGL3NbX6bZGonmePy0rKWSY2iNoFz9sSFtzWH726ExIZbXA8eV3Ml2smBrnK82jLNzTWW4R3UyccVQfsB2Gm0KnXhfk2Qj8QDgKgkYroS7iC-b-M0XUpnu4j-Ygw"
    return login_token

def get_portfolio():
    #get all stocks are currently in portfolio
    login_token = get_login_token()

    url = "https://trade-api.vndirect.com.vn/accounts/v3/{}/portfolio".format(acc_id)
 
    querystring = {"secType":"in:001,002,008,010,013,015,016"}

    headers = {
        'x-auth-token': login_token,
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    response_text = response.content.decode(encoding='utf-8')
    stock_res = json.loads(response_text)['stocks']
    stock_df = pd.io.json.json_normalize(stock_res)
    stock_df = stock_df[stock_df['quantity'] != 0].reset_index()
    del stock_df['index']
    return stock_df

def get_stocks():
    #get all stocks are currently in portfolio
    login_token = get_login_token()

    url = "https://trade-api.vndirect.com.vn/accounts/v3/{}/stocks".format(acc_id)
 
    querystring = {}

    headers = {
        'x-auth-token': login_token,
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    response_text = response.content.decode(encoding='utf-8')
    stock_res = json.loads(response_text)['stocks']
    stock_df = pd.io.json.json_normalize(stock_res)
    stock_df = stock_df[stock_df['quantity'] != 0].reset_index()
    del stock_df['index']
    return stock_df

def get_account_info():
    login_token = get_login_token()
    url = 'https://trade-bo-api.vndirect.com.vn/accounts/v3/{}/assets'.format(acc_id)
    headers = {
        'x-auth-token': login_token,
    }
    querystring = {}
    response = requests.request("GET", url, headers=headers, params=querystring)
    response_text = response.content.decode(encoding='utf-8')
    acc_info_json = json.loads(response_text)
    return acc_info_json

if __name__ == '__main__':
    global acc_id 
    acc_id = '0001165217'
    #my_stocks = get_portfolio()


    
