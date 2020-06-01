import tdameritrade as td
import pandas
import os
import csv
import datetime
import math
from time import sleep


retry = []

today = datetime.datetime.today()
twenty_three_days = (today + datetime.timedelta(days=23)).strftime('%Y-%m-%d')
thirty_seven_days = (today + datetime.timedelta(days=37)).strftime('%Y-%m-%d')
twenty_five_days = (today + datetime.timedelta(days=25)).strftime('%Y-%m-%d')
fifty_days = (today + datetime.timedelta(days=50)).strftime('%Y-%m-%d')

client_id = os.getenv('TDAMERITRADE_CLIENT_ID')
account_id = os.getenv('TDAMERITRADE_ACCOUNT_ID')
refresh_token = os.getenv('TDAMERITRADE_REFRESH_TOKEN')

td_client = td.client.TDClient(client_id=client_id, refresh_token=refresh_token, account_ids=[account_id])


def mid_val(val1, val2):
    return (val1 + val2)/2


def impl_vol(ticker):
    '''
    Take all options that have expiration dates 23-37 days out (7 days around 30) that are at most two strikes away from ATM.
    - So if there are two expiration dates 23-37 days out, then you would have 8 options (four puts, four calls). Two puts and two calls for each expiration date.

    For each strike price on an expiration date, where the call is ITM and put is OTM, average the call and puts IVs.
    - Do this for all expiration dates. Find the average of all these values.

    Repeat for put side (put is ITM and call is OTM).

    Average the two sides.

    Somewhat based upon VIX, but simpler since I have IV values for individual options:
    http://www.cboe.com/framed/pdfframed?content=/micro/vix/vixwhite.pdf&section=SECT_MINI_SITE&title=VIX+White+Paper

    '''
    def get_avg(itm, otm):
        avg_vol = 0
        count = 0
        for _, option1 in itm.iterrows():
            for _, option2 in otm.iterrows():
                if option1['daysToExpiration'] == option2['daysToExpiration'] and option1['strikePrice'] == option2['strikePrice']:
                    avg_vol += mid_val(option1['volatility'], option2['volatility'])
                    count += 1
        return avg_vol / count

    try:
        df = td_client.optionsDF(symbol=ticker, fromDate=twenty_three_days, toDate=thirty_seven_days, strikeCount=2)
    except KeyError as e:
        raise td.exceptions.NotFound("Could not find options contracts between 23-37 days")
    
    df_calls = df.loc[df['putCall'] == 'CALL']
    df_calls_itm = df_calls.loc[df['inTheMoney'] == True]
    df_calls_otm = df_calls.loc[df['inTheMoney'] == False]

    df_puts = df.loc[df['putCall'] == 'PUT']
    df_puts_otm = df_puts.loc[df['inTheMoney'] == False]
    df_puts_itm = df_puts.loc[df['inTheMoney'] == True]

    return mid_val(get_avg(df_calls_itm, df_puts_otm), get_avg(df_puts_itm, df_calls_otm))/100

    
def std_dev(ticker, days_to_exp, iv = None):
    '''
    1 std dev = stock price * volatility * sqrt of days to exp/252 (252 is # of trading days)
    '''
    df = td_client.quoteDF(ticker)
    mid_price = mid_val(df.at[0, 'askPrice'], df.at[0, 'bidPrice'])
    if iv == None:
        iv = impl_vol(ticker)
    
    sqrt_days_to_exp = math.sqrt(days_to_exp/365)
    return mid_price * iv * sqrt_days_to_exp


def risk_amt(ticker, days_to_exp, curr_price, put_strike, call_strike, iv = None):
    '''
    Calculated using the risk associated with a 2 std dev movement in the stock price
    '''
    std = std_dev(ticker, days_to_exp, iv)
    upside_risk = max(curr_price + std*2 - call_strike, 0)*100
    downside_risk = max(put_strike - (curr_price - std*2), 0)*100
    return max(upside_risk, downside_risk)


def find_strangle(ticker):
    current_price = mid_val(td_client.quoteDF(ticker).at[0,'askPrice'], td_client.quoteDF(ticker).at[0,'bidPrice'])
    iv = impl_vol(ticker)

    print("------------------------------------------------------------------------------------------")
    print("IV calculated for %s: %.2f" % (ticker, iv))

    df = td_client.optionsDF(symbol=ticker, includeQuotes=True, fromDate=twenty_five_days, toDate=fifty_days, strikeCount=100)
    df = df.loc[df['inTheMoney'] == False] # OTM options
#     df = df.loc[df['openInterest'] >= 0] # Open interest >= 0
    df = df.loc[df['totalVolume'] > 100] # Volume > 100
    df['midPrice'] = mid_val(df.ask, df.bid)
    df_calls = df.loc[df['delta'].between(0.1, 0.4)] # All calls in correct delta range
    df_puts = df.loc[df['delta'].between(-0.4, -0.1)] # All puts in correct delta range


    for _, call in df_calls.iterrows():
        for _, put in df_puts.iterrows():
            if call['expirationDate'] == put['expirationDate'] and abs(call['delta'] + put['delta']) < 0.05:
                premium = (call['midPrice'] + put['midPrice'])*100
                risk = risk_amt(ticker, call['daysToExpiration'], current_price, put['strikePrice'], call['strikePrice'], iv)
                reward_risk = premium / risk
                avg_delta = mid_val(call['delta'], -put['delta'])
                
                if reward_risk > avg_delta:
                    print("----------")
                    print("%s @ $%.2f %.0f Delta" % (call['description'], call['midPrice'], call['delta'] * 100))
                    print("%s @ $%.2f %.0f Delta" % (put['description'], put['midPrice'], -put['delta'] * 100))
                    print("Premium (Reward):%.2f Risk:%.2f Reward/Risk:%.2f (Reward/Risk-Avg. Delta):%.2f" % (premium, risk, reward_risk, reward_risk - avg_delta))


def find_strangles(csv_reader):
    '''
    Finds good strangle trades on all financial instruments passed in (NYSE, NASDAQ, AMEX).
    Pre-screening:
    Financial instrument must have a market cap over $3B (no small/micro-caps)
    
    Put and call side must be on the same expiration date
    OTM options only
    Volume above 100
    
    Expiration of contracts must be 25-50 days out (little bit larger than ideal 30-45 days).
    Deltas between 10 and 40 -- inclusive (little bit larger than ideal 10-15)
    
    Check:
    Reward/risk (premium / (BP effect or 2 std. dev change in stock)) > delta (avg of put and call side)
    
    '''
    global retry
    
    for row in csv_reader:
        if 'B' in row[3] and (len(row[3]) > 6 or int(row[3][1]) > 3): # > 3Billion (mid-cap and up)
            while True:
                try:
                    find_strangle(row[0])
                    break
                except td.exceptions.NotFound as e:
                    print("Not found error %s" % (e))
                    retry.append(row[0])
                    break
                except td.exceptions.TooManyRequests as e:
                    print("Too many requests: 429. Pausing for 30 seconds.")
                    sleep(30)
                except Exception as e:
                    print("ERROR: Could not find strangles for %s--%s" % (row[0], e))
                    retry.append(row[0])
                    break


def retry_find_strangles():
    '''
    Find strangles but with retries instead of the original csv readers.

    Handles errors the same. Only removes if the ticker works.
    '''
    global retry
    
    for ticker in retry[:]:
        while True:
                try:
                    find_strangle(ticker)
                    retry.remove(ticker)
                    break
                except td.exceptions.NotFound as e:
                    print("Not found error %s" % (e))
                    break
                except td.exceptions.TooManyRequests as e:
                    print("Too many requests: 429. Pausing for 30 seconds.")
                    sleep(30)
                except Exception as e:
                    print("ERROR: Could not find strangles for %s--%s" % (ticker, e))
                    break


def main():
    global retry

    with open('amex.csv', 'r') as csv_file:
        next(csv_file)
        csv_reader = csv.reader(csv_file, delimiter=',')
        find_strangles(csv_reader)

    with open('nasdaq.csv', 'r') as csv_file:
        next(csv_file)
        csv_reader = csv.reader(csv_file, delimiter=',')
        find_strangles(csv_reader)

    with open('nyse.csv', 'r') as csv_file:
        next(csv_file)
        csv_reader = csv.reader(csv_file, delimiter=',')
        find_strangles(csv_reader)

    while len(retry) != 0:
        print("--------------------------------------------------------------")
        print("--------------------------------------------------------------")
        print("Retrying: ",  retry)
        print("--------------------------------------------------------------")
        print("--------------------------------------------------------------")

        retry_find_strangles()

if __name__ == '__main__':
    main()