import APIWrapper
from logger import *
import signal
import time
import argparse
import os, os.path

class ArbBot:
	#cycles that pass for 'usd', and therefore can be used as arbitrage points
	arbCycles = [('usd', 'ppc', 'btc'), ('usd', 'nvc', 'btc'), ('usd', 'nmc', 'btc'), ('usd', 'btc', 'ltc'),
				('usd', 'btc', 'rur'), ('usd', 'btc', 'eur'), ('usd', 'ltc', 'eur'), ('usd', 'ltc', 'rur')] 
	msgPref = ""

	def __init__(self, logger, keyfile):
		self.lgr = logger
		self.api = APIWrapper.APIWrapper(keyfile, self.lgr)

		self.lgr.log(INFO, "Starting ArbBot")

	def getMostProfitableCycle(self):
		resCycle = None
		resProfit = 0.0
		for cycle in self.arbCycles:
			amount = 1
			for i in range(3):
				amount = self.api.calcTransaction(cycle[i%3], cycle[(i+1)%3], amount)
			if amount>resProfit:
				resCycle = cycle
				resProfit = amount
			amount = 1
			for i in range(0, -3, -1):
				amount = self.api.calcTransaction(cycle[i%3], cycle[(i-1)%3], amount)
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
			self.api.refreshRates()
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

	def trade(self):
		self.msgPref = "Trade: "
		self.log(INFO, "Starting ArbBot trading...")

		self.cont = True
		def stopLoop(signum, frame):
			self.log(INFO, "Interrupt received, exiting, have patience...")
			self.cont = False

		signal.signal(signal.SIGINT, stopLoop)

		#List arbitrage
		t = time.time()
		while self.cont:
			self.api.refreshRates()
			cycle, profit = self.getMostProfitableCycle()

			#### TRADE HERE #####

			msg = ""
			for cur in cycle[:-1]:
				msg+=cur.upper()+' -> '
			msg+=cycle[-1].upper()
			msg+=" gave %f profit, total"%profit
			self.log(INFO, msg)
			if time.time()-t >= self.api.rBalTime:
				self.api.checkStale(rates=False)

if __name__=='__main__':
	parser = argparse.ArgumentParser(description="Arbitrage-based BTC-E trading bot", epilog="Key file syntax is three lines, one with API key, one with private key and one with nonce")
	parser.add_argument('-d', '--debug', action='store_true', required=False, help='log debug messages')
	parser.add_argument('-q', '--quiet', action='store_true', required=False, help="don't print log to screen")
	parser.add_argument('-k', '--key-file', action='store', type=str, required=False, help="path of the key file. Default is ~/.btce_keys")
	subparsers = parser.add_subparsers(help='action to do')
	parser_analyse = subparsers.add_parser('analyse', help='analyse the current state of btc-e')
	parser_analyse.set_defaults(action=0)
	parser_trade = subparsers.add_parser('trade', help='AI trade')
	parser_trade.set_defaults(action=1)

	args = parser.parse_args()

	#use arguments
	lvl = INFO
	if args.debug:
		lvl = DEBUG

	show = not args.quiet

	keyfile = ""
	if args.key_file==None:
		keyfile = os.environ['HOME']+"/.btce_keys"
	elif args.key_file[0]=='~':
		keyfile = os.environ['HOME']+args.key_file[1:]
	else:
		keyfile = args.key_file

	logger = Logger("ArbBot", level=lvl, show=show, color=True)
	if not os.path.exists(keyfile):
		logger.log(ERROR, "Please create a key file on %s or specify the correct path"%keyfile)

	a = ArbBot(logger, keyfile)
	if args.action==0:
		a.analyse()
	elif args.action==1:
		a.trade()
