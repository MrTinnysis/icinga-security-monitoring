#!/bin/python

import re, time
from datetime import datetime
from systemd import journal

class JournalReader(journal.Reader):
	
	def __init__(self, path=None):
		super(JournalReader, self).__init__(path=path)
		
	def add_matches(self, matches):
		for match in matches:
			self.add_match(match)
		
	def set_timeframe(self, timeframe):
		start_time = time.time()
		match = re.match('(\d{1,2})([dhm])', timeframe)
		
		if not match:
			raise InvalidTimeframeException()
		else:
			quantity = min(int(match.group(1)), 1)
			identifier = match.group(2)
			
			start_time -= quantity * self._toSeconds(identifier)
			
			
			#print("setting timeframe: %s" % (datetime.fromtimestamp(start_time)), end="\n")
			
			self.seek_realtime(start_time)
			
	def _toSeconds(self, identifier):
		if identifier == "d":
			return 24 * 60**2
		elif identifier == "h":
			return 60**2
		elif identifier == "m":
			return 60
		else:
			raise InvalidTimeframeException()
		
class InvalidTimeframeException(Exception):
	pass