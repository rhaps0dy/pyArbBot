import time
import btceapi
import httplib
from logger import *
import os, os.path

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
	#average ticker getting time is about 4.5s
	rRatesTime = 5
	#fees seldom change, so one refresh every three hours is reasonable
	rFeesTime = 3600*3
	#our balance changes every time, but we calculate it so a check every hour is enough
	rBalTime = 3600

	rates = None
	fees = None
	connection = None 
	balance = None

	def __init__(self, logger=None):
		#the last time we refreshed was Jan 1 1970!
		self.lRatesTime = 0
		self.lFeesTime = 0
		self.lBalTime = 0

		if logger==None:
			self.lgr = Logger("APIWrapper")
		else:
			self.lgr = logger

		self.lgr.log(INFO, "Initialising APIWrapper...")
		keyfile = os.environ['HOME']+"/.btce_keys"
		if not os.path.exists(keyfile):
			self.lgr.log(ERROR, "Please create a key file on %s"%keyfile)
		handler = btceapi.KeyHandler(keyfile, resaveOnDeletion=True)

		key = handler.getKeys()[0]
		self.lgr.log(INFO, "Creating trader for key %s from %s"%(key, keyfile))
		self.trader = btceapi.TradeAPI(key, handler)


		self.lgr.log(DEBUG, "Initialising global data containers...")
		self.rates = dict.fromkeys(self.logPairs, [0, 0])
		self.fees = dict.fromkeys(self.logPairs, 0)
		self.balance = dict.fromkeys(self.currencies, 0)
		self.connection = btceapi.BTCEConnection()
		self.lgr.log(DEBUG, "Initialised global data containers")

		self.lgr.log(DEBUG, "Filling global data containers...")
		self.getRates()
		self.getFees()

		#disable warnings for getting first balance
		self.lgr.log(INFO, "The following warnings will tell you your current balance")
		self.getBalance()

		self.lgr.log(DEBUG, "Global data containers full")

	"""
	Helper function for caching and retrieving of transaction fees.
	Always call it to get the current fees.
	"""
	def getFees(self):
		try:
			dt = time.time()-self.lFeesTime
			if dt > self.rFeesTime:
				for pair in self.logPairs:
					self.fees[pair] = btceapi.getTradeFee(pair, self.connection)
				self.lgr.log(DEBUG, "Retrieved new fees from btc-e")
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
			if dt > self.rRatesTime:
				for pair in self.logPairs:
					ticker = btceapi.getTicker(pair, self.connection)
					self.rates[pair][0] = getattr(ticker, 'buy')
					self.rates[pair][1] = getattr(ticker, 'sell')
				self.lgr.log(DEBUG, "Retrieved new exchange rates from btc-e")
				self.lRatesTime = time.time()
			return self.rates
		except httplib.BadStatusLine:
			self.refreshConnection()
			return self.getRates()

	"""
	Refreshes the connection to btc-e. Used to force a refresh in
	case there's a connection exception
	"""
	def refreshConnection(self):
		try:
			self.connection.close()
		except:
			pass
		self.connection = btceapi.BTCEConnection()
		self.lgr.log(DEBUG, "Reset connection to btc-e")

	"""
	Caches and refreshes when necessary the current balance. When it refreshes it
	checks if there were errors updating it and the cached balance differs from the
	one in btc-e
	"""
	def getBalance(self):
		try:
			dt = time.time()-self.lBalTime
			if dt > self.rBalTime:
				#refresh the balance
				r = self.trader.getInfo(self.connection)
				self.lgr.log(DEBUG, "Retrieved balance from btc-e")
				#check correctness
				for cur in self.currencies:
					bal = getattr(r, 'balance_'+cur)
					if bal!=self.balance[cur]:
						self.lgr.log(WARNING, "Calculated %s balance (%f) differs from real (%f)"%(cur.upper(), self.balance[cur], bal))
					self.balance[cur] = bal
				self.lBalTime = time.time()
			return self.balance
		except httplib.BadStatusLine:
			self.refreshConnection()
			return self.getBalance()

	"""
	Get the btc-e trade pair which contains the two specified currencies
	"""
	def getPair(self, cur1, cur2):
		for pair in self.logPairs:
			if (cur1 in pair) and (cur1 in pair):
				return pair
		self.lgr.log(ERROR, "No pair exists with currencies %s and %s"%(cur1, cur2))

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
