#!/bin/python

import re
import time
from systemd.journal import Reader

class JournalReader(Reader):
	
	def __init__(self, path=None):
		super(JournalReader, self).__init__(path=path)
		
	def add_matches(self, matches):
		for match in matches:
			self.add_match(match)
		
	def set_timeframe(self, timeframe):
		start_time = time.time()
		match = re.match('(\d{1,2})([dhm])', timeframe)
		
		if !match:
			raise InvalidTimeframeException()
		else:
			quantity = min(match.group(0), 1)
			identifier = match.group(1)
			
			start_time -= quantity * self._toSeconds(identifier)
			
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