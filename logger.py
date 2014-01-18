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

	tError = '[ERROR] '
	tWarning = '[WARNING] '
	tInfo = '[INFO] '
	tDebug = '[DEBUG] '

	def __init__(self, name, level=DEBUG, show=True, color=True):
		self.show = show
		self.level = level
		syslog.openlog(name, syslog.LOG_PID, syslog.LOG_DAEMON)
		if color:
			self.enableColor()

	def enableColor(self):
		self.tError = '[\033[91mERROR\033[0m] '
		self.tWarning = '[\033[93mWARNING\033[0m] '
		self.tInfo = '[\033[92mINFO\033[0m] '
		self.tDebug = '[DEBUG] '

	def disableColor(self):
		self.tError = '[ERROR] '
		self.tWarning = '[WARNING] '
		self.tInfo = '[INFO] '
		self.tDebug = '[DEBUG] '

	"""
	Log message 'msg' at severity level 't'
	"""
	def log(self, t, msg):
		if t>self.level:
			return
		if t==ERROR:
			msg = self.tError+msg
			syslog.syslog(syslog.LOG_ERR, msg)
			#throw the error as python exception
			print msg
			raise Exception(msg)
		elif t==WARNING:
			msg = self.tWarning+msg
			syslog.syslog(syslog.LOG_WARNING, msg)
		elif t==INFO:
			msg = self.tInfo+msg
			syslog.syslog(syslog.LOG_INFO, msg)
		elif t==DEBUG:
			msg = self.tDebug+msg
			syslog.syslog(syslog.LOG_DEBUG, msg)
		if self.show:
			print msg
