import syslog

DEBUG=3
INFO=2
WARNING=1
ERROR=0

"""
Helper class to log. Integrated with syslogd and Python exceptions
"""
class Logger:
	show=True
	level=DEBUG
	def __init__(self, name, level=DEBUG, show=True):
		self.show = show
		self.level = level
		syslog.openlog(name, syslog.LOG_PID, syslog.LOG_DAEMON)

	"""
	Log message 'msg' at severity level 't'
	"""
	def log(self, t, msg):
		if t>self.level:
			return

		if t==ERROR:
			msg = '[ERROR] '+msg
			syslog.syslog(syslog.LOG_ERR, msg)
			#throw the error as python exception
			raise Exception(msg)

		elif t==WARNING:
			msg = '[WARNING] '+msg
			syslog.syslog(syslog.LOG_WARNING, msg)
		elif t==INFO:
			msg = '[INFO] '+msg
			syslog.syslog(syslog.LOG_INFO, msg)
		elif t==DEBUG:
			msg = '[DEBUG] '+msg
			syslog.syslog(syslog.LOG_DEBUG, msg)

		if self.show:
			print msg

