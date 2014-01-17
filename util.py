#import requests, urllib
import hashlib, hmac
import codecs
import time

# Pairs to log
logPairs = ["btc_usd", "btc_rur", "btc_eur", "ltc_btc", "ltc_usd", "ltc_rur", "ltc_eur", "nmc_btc", "nmc_usd", "nvc_btc",
        "nvc_usd", "usd_rur", "eur_usd", "trc_btc", "ppc_btc", "ppc_usd", "ftc_btc", "xpm_btc"]
currencies = ['btc', 'ltc', 'nmc', 'nvc', 'trc', 'ppc', 'ftc', 'xpm', 'usd', 'rur', 'eur']

def readFile(filename):
    f = open(filename, 'r');
    a=[]
    for line in f.readlines():
        try:
            a.append(float(line)) 
        except Exception:
            pass
    f.close()
    return a

def writeFile(filename, array):
    f = open(filename, 'w')
    for value in array:
        f.write(str(value))
        f.write("\n")
    f.close()

def getRate(prices, fromCur, toCur):
    rate = 0
    for pair in logPairs:
        if (fromCur in pair) and (toCur in pair):
        #check the order of currencies
            if pair[:3] == fromCur:
                #take the sell one
                rate = prices[pair][1]
            else:
                rate = 1/prices[pair][0]
            return rate

def calcTransaction(prices, fromCur, toCur, amount):
    fee=0.002
    if((fromCur=='usd' and toCur=='rur') or (fromCur=='rur' and toCur=='usd')):
        fee = 0.005
    amount *= getRate(prices, fromCur, toCur) * (1-fee) 
    return amount

def apiQuery(method, req={}):
    # API settings
    key = b'PK4H55RO-MECL20XF-I0FURDJG-56Y70ZPF-46OYJ1ZO'
    secret = b'cd4c2d5d9ac49a4541af1752587ffc0833b7f6e01b2540a208b6f1dd527c75a3'

    req['method'] = method;
    req['nonce'] = time.time()

    message = codecs.encode(urllib.parse.urlencode(req), 'ascii')
    H = hmac.new(secret, msg=message, digestmod=hashlib.sha512)
    sign = H.hexdigest()
    headers = {'Sign':sign, 'Key':key}
   # r = requests.post('https://www.cryptsy.com/api', data=req, headers=headers)
   # return r.json();
