Description
===========
Arbitrage-based trading bot proof-of-concept

It doesn't really work because it takes at least 5
seconds to fetch all the prices from BTC-E, and unless
the arbitrage cycle stays on for long enough you can
get stuck in the middle of it and make the bot deadlock.

Running
=======
python2.7 arbitrage.py -h

And read the help
