import APIWrapper
from logger import *
import sys
import signal
import time

class ArbBot:
	#cycles that pass for 'usd', and therefore can be used as arbitrage points
	arbCycles = [('usd', 'ppc', 'btc'), ('usd', 'nvc', 'btc'), ('usd', 'nmc', 'btc'), ('usd', 'btc', 'ltc'),
				('usd', 'btc', 'rur'), ('usd', 'btc', 'eur'), ('usd', 'ltc', 'eur'), ('usd', 'ltc', 'rur')] 
	msgPref = ""

	def __init__(self):
		self.lgr = Logger("ArbBot", level=DEBUG, show=True, color=True)
		self.api = APIWrapper.APIWrapper(self.lgr)

	def getMostProfitableCycle(self):
		resCycle = None
		resProfit = 0.0
		for cycle in self.arbCycles:
			amount = 1
			for i in range(3):
				amount = self.api.calcTransaction(cycle[i%3], cycle[(i+1)%3], amount)
				# print(cycle[i%3], '->', cycle[(i+1)%3],)
				# print(amount)

			if amount>resProfit:
				resCycle = cycle
				resProfit = amount
			amount = 1
			for i in range(0, -3, -1):
				amount = self.api.calcTransaction(cycle[i%3], cycle[(i-1)%3], amount)
				# print(cycle[i%3], '->', cycle[(i-1)%3],)
				# print(amount)

			if amount>resProfit:
				resCycle = (cycle[0], cycle[-1], cycle[-2])
				resProfit = amount
		return resCycle, resProfit

	def log(self, t, m):
		self.lgr.log(t, self.msgPref+m)

	def analyse(self):
		self.msgPref = "Analyse: "
		self.log(INFO, "Starting ArbBot analysis...")

		self.cont = True
		def stopLoop(signum, frame):
			self.log(INFO, "Interrupt received, exiting, have patience...")
			self.cont = False

		signal.signal(signal.SIGINT, stopLoop)

		#List arbitrage
		while self.cont:
			begTime = time.time()
			self.api.forceRatesRefresh()
			anaTime = time.time()
			cycle, profit = self.getMostProfitableCycle()
			lvl = DEBUG
			if profit>1:
				lvl = INFO
			msg = ""
			for cur in cycle[:-1]:
				msg+=cur.upper()+' -> '
			msg+=cycle[-1].upper()
			msg+=" gives %f profit"%profit
			self.log(lvl, msg)
			self.log(DEBUG, "This round took %f+%f seconds"%(anaTime-begTime, time.time()-anaTime))


if __name__=='__main__':
	a = ArbBot()
	a.analyse()
