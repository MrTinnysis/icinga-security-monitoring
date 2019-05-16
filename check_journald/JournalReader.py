#!/bin/python

import re
from datetime import datetime, timedelta
from systemd import journal

class JournalReader(journal.Reader):
	
	def __init__(self, path=None):
		super(JournalReader, self).__init__(path=path)
		
	def add_matches(self, matches):
		for match in matches:
			self.add_match(match)
		
	def set_timeframe(self, timeframe):
		start_time = datetime.now()
		match = re.match('(\d{1,2})([dhm])', timeframe)
		
		if not match:
			raise InvalidTimeframeException()
		else:
			quantity = max(int(match.group(1)), 1)
			identifier = match.group(2)
			
			start_time -= self._timeDelta(quantity, identifier)
			
			
			print("Accessing log entries after: %s" % (start_time), end="\n")
			self.seek_realtime(start_time)
			
			
	def _timeDelta(self, quantity, identifier):
		if identifier == "d":
			return timedelta(days=quantity);
		elif identifier == "h":
			return timedelta(hours=quantity);
		elif identifier == "m":
			return timedelta(minutes=quantity);
		else:
			raise InvalidTimeframeException()
		
class InvalidTimeframeException(Exception):
	pass