from util import calcTransaction
import ticker_btce

arbCycles = [('usd', 'ppc', 'btc'), ('usd', 'nvc', 'btc'), ('usd', 'nmc', 'btc'), ('usd', 'btc', 'ltc'),
			('usd', 'btc', 'rur'), ('usd', 'btc', 'eur'), ('usd', 'ltc', 'eur'), ('usd', 'ltc', 'rur')] 

t = ticker_btce.TestFramework()

def getMostProfitableCycle(prices):
	resCycle = None
	resProfit = 0.0
	for cycle in arbCycles:
		amount = 1
		for i in range(3):
			amount = calcTransaction(prices, cycle[i%3], cycle[(i+1)%3], amount)
			# print(cycle[i%3], '->', cycle[(i+1)%3],)
			# print(amount)
		if amount>resProfit:
			resCycle = cycle
			resProfit = amount

		amount = 1
		for i in range(0, -3, -1):
			amount = calcTransaction(prices, cycle[i%3], cycle[(i-1)%3], amount)
			# print(cycle[i%3], '->', cycle[(i-1)%3],)
			# print(amount)
		if amount>resProfit:
			resCycle = (cycle[0], cycle[-1], cycle[-2])
			resProfit = amount
	return resCycle, resProfit

res=1
try:
	while True:
		a, b = getMostProfitableCycle(t.getPrices())
		if b>1:
			t.transaction(a[0], a[1])
		t.tick()
except Exception:
	pass
