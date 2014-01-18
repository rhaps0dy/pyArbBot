import time
import btceapi
import httplib
from logger import *

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
	#1000 sample average ticker getting time is 4.84s
	#1000 sample average depth getting time is 5.43s
	rRatesTime = 30
	#fees seldom change, so one refresh every day is reasonable
	rFeesTime = 3600*24
	#our balance changes every time, but we calculate it so a check every hour is enough
	rBalTime = 3600

	rates = None
	fees = None
	connection = None 
	balance = None

	def __init__(self,  keyfile, logger=None):
		#the last time we refreshed was Jan 1 1970!
		self.lRatesTime = 0
		self.lFeesTime = 0
		self.lBalTime = 0

		if logger==None:
			self.lgr = Logger("APIWrapper")
		else:
			self.lgr = logger

		self.lgr.log(INFO, "Initialising APIWrapper...")
		handler = btceapi.KeyHandler(keyfile, resaveOnDeletion=True)

		key = handler.getKeys()[0]
		self.lgr.log(INFO, "Creating trader for key [...]-%s from %s..."%(key[-8:], keyfile))
		self.trader = btceapi.TradeAPI(key, handler)


		self.lgr.log(DEBUG, "Initialising global data containers...")
		self.rates = dict.fromkeys(self.logPairs, None)
		for key in self.logPairs:
			self.rates[key] = [None, None]
		self.fees = dict.fromkeys(self.logPairs, None)
		self.balance = dict.fromkeys(self.currencies, 0)
		self.connection = btceapi.BTCEConnection()
		self.lgr.log(DEBUG, "Initialised global data containers")

		self.lgr.log(DEBUG, "Filling global data containers...")
		self.refreshRates()
		self.refreshFees()

		#disable warnings for getting first balance
		self.lgr.log(INFO, "The following warnings will tell you your current balance")
		self.refreshBalance()

		self.lgr.log(DEBUG, "Global data containers full")
		self.lgr.log(INFO, "APIWrapper fully initialised")

	"""
	Get the latest trading fees
	"""
	def refreshFees(self):
		for pair in self.logPairs:
			try:
				self.fees[pair] = btceapi.getTradeFee(pair, self.connection)
			except:
				self.refreshConnection()
				return self.refreshFees()
			#btce gives fees in %, we want per one
			self.fees[pair]/=100
		self.lgr.log(DEBUG, "Retrieved new fees from btc-e")
		self.lFeesTime = time.time()

	"""
	Get the latest exchange rates
	"""
	def refreshRates(self):
		for pair in self.logPairs:
			r = None
			try:
				r = self.connection.makeJSONRequest("/api/2/%s/ticker" % pair)
			except:
				self.refreshConnection()
				return self.refreshRates()
			self.rates[pair][0] = r['ticker']['buy']
			self.rates[pair][1] = r['ticker']['sell']
		self.lgr.log(DEBUG, "Retrieved new exchange rates from btc-e")
		self.lRatesTime = time.time()

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
	Refreshes the balance, checks if there were errors updating it and
	whether the cached balance differs from the one in btc-e
	"""
	def refreshBalance(self):
		try:
			r = self.trader.getInfo(self.connection)
			self.lgr.log(debug, "retrieved balance from btc-e")
			#check correctness
			for cur in self.currencies:
				bal = getattr(r, 'balance_'+cur)
				if bal!=self.balance[cur]:
					self.lgr.log(warning, "calculated %s balance (%f) differs from real (%f)"%(cur.upper(), self.balance[cur], bal))
				self.balance[cur] = bal
			self.lBalTime = time.time()
		except:
			self.refreshConnection()
			return self.refreshBalance()

	"""
	Get the btc-e trade pair which contains the two specified currencies
	"""
	def getPair(self, cur1, cur2):
		for pair in self.logPairs:
			if (cur1 in pair) and (cur2 in pair):
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
			rate = self.rates[pair][1]
		else:
			rate = 1/self.rates[pair][0]
		return rate

	"""
	Calculate the result of a transaction from currency 'fromCur' to
	currency 'toCur', with amount of the original currency 'amount'
	"""
	def calcTransaction(self, fromCur, toCur, amount):
		fee = self.fees[self.getPair(fromCur, toCur)]
		amount *= self.getRate(fromCur, toCur) * (1-fee) 
		return amount

	#def performImmediateTransaction(self, fromCur, toCur, amount):
	#	self.trader.trad

	"""
	Refresh global variables if necessary
	"""
	def checkStale(self, rates=True, balance=True, fees=True):
		t = time.time()
		if rates and t-self.lRatesTime>self.rRatesTime:
			self.refreshRates()
		if balance and t-self.lBalTime>self.rBalTime:
			self.refreshBalance()
		if fees and t-self.lFeesTime>self.rFeesTime:
			self.refreshFees()
