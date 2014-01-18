import time
import btceapi
import httplib

"""
Wrapper for the btceapi Python module. Provides a tailored interface
for this project. Most important are the transaction calculations and
the ability to automatically cache data and refresh it every X time
"""
class APIWrapper:
	# We're really interested only in coins with cycles
	logPairs = ["btc_usd", "btc_rur", "btc_eur", "ltc_btc", "ltc_usd", "ltc_rur", "ltc_eur", "nmc_btc", "nmc_usd",
				"nvc_btc", "nvc_usd", "usd_rur", "eur_usd", "ppc_btc", "ppc_usd"]
	currencies = ['btc', 'ltc', 'nmc', 'nvc', 'trc', 'ppc', 'usd', 'rur', 'eur']

	#time to refresh data in seconds
	#average ticker getting time is 4.47741769552s
	rRatesTime = 5
	#fees seldom change, so one refresh every three hours is reasonable
	rFeesTime = 3600*3
	#connection when testing the rates time lasted more than 447s
	rConnTime = 400
	#our balance changes every time, but we calculate it so a check every hour is enough
	rBalTime = 3600

	rates = None
	fees = None
	connection = None 

	def __init__(self):
		#the last time we refreshed was Jan 1 1970!
		self.lRatesTime = 0
		self.lFeesTime = 0
		self.lConnTime = 0
		self.lBalTime = 0

		#init global data storage
		self.rates = dict.fromKeys(logPairs, [None, None])
		self.fees = dict.fromKeys(logPairs, None)
		self.balance = dict.fromKeys(currencies, None)
		self.connection = None

		#fill global data storage
		self.getConnection()
		self.getRates()
		self.getFees()
		self.getBalance()

"""
Helper function for caching and retrieving of transaction fees.
Always call it to get the current fees.
"""
	def getFees(self):
		try:
			dt = time.time()-self.lFeesTime
			if dt < self.rFeesTime:
				return self.fees
			#else refresh
			for pair in self.logPairs:
				self.fees[pair] = btceapi.getTradeFee(pair, self.getConnection())
			self.lFeesTime = time.time()
			return self.fees
		except httplib.BadStatusLine:
			self.refreshConnection()
			return self.getFees()

"""
Helper function for caching and retrieving of exchange rates.
Always call it to get the current exchange rates.
"""
	def getRates(self):
		try:
			dt = time.time()-self.lRatesTime
			if dt < self.rRatesTime:
				return self.rates
			for pair in self.logPairs:
				ticker = btceapi.getTicker(pair, self.getConnection())
				self.rates[pair][0] = getattr(ticker, 'buy')
				self.rates[pair][1] = getattr(ticker, 'sell')
			self.lRatesTime = time.time()
			return self.rates
		except httplib.badStatusLine:
			self.refreshConnection()
			return self.getRates()

"""
Caches and refreshes when necessary the connection to BTCE when necessary
"""
	def getConnection(self):
		dt = time.time()-self.lConnTime
		if dt < self.rConnTime:
			return self.connection
		self.refreshConnection()
		self.lConnTime = time.time()
		return self.connection

"""
Refreshes the connection to btc-e. Can be used to force a refresh in
case there's a connection exception
"""
	def refreshConnection(self):
		try:
			self.connection.close()
		except:
			pass
		self.connection = btceapi.BTCEConnection()

"""
Caches and refreshes when necessary the current balance. When it refreshes it
checks if there were errors updating it and the cached balance differs from the
one in btc-e
"""
	def getBalance(self):
		dt = time.time()-self.lBalTime
		if dt < self.rBalTime:
			return self.balance
		self.refreshBalance()

"""
Retrieves the balance from btc-e
"""


"""
Get the btc-e trade pair which contains the two specified currencies
"""
	def getPair(self, cur1, cur2):
		for pair in self.logPairs:
			if (cur1 in pair) and (cur1 in pair):
				return pair
		raise Exception("No pair exists with these currencies")

"""
Get the exchange rate between the two specified currencies
"""
	def getRate(self, fromCur, toCur):
		rate = 0
		pair = self.getPair(fromCur, toCur)
		#check the order of currencies
		if pair[:3] == fromCur:
			#take the sell one
			rate = self.getRates()[pair][1]
		else:
			rate = 1/self.getRates()[pair][0]
		return rate

"""
Calculate the result of a transaction from currency 'fromCur' to
currency 'toCur', with amount of the original currency 'amount'
"""
	def calcTransaction(self, fromCur, toCur, amount):
		fee = self.getFees[self.getPair(fromCur, toCur)]
		amount *= self.getRate(fromCur, toCur) * (1-fee) 
		return amount
