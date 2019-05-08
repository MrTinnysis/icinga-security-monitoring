#!/bin/python

import sys, argparse
from monitoringplugin.JournalReader import JournalReader

def main():
	# monitoring plugin return codes
	OK = 0
	WARNING = 1
	CRITICAL = 2
	UNKNOWN = 3

	# defaults
	returnCode = UNKNOWN

	# parse arguments
	argumentParser = argparse.ArgumentParser()

	argumentParser.add_argument(
		'-h', '--hostname', default='localhost',
		help='host with systemd journal gateway (default "localhost")')
	argumentParser.add_argument(
		'-p', '--port', default='19531',
		help='the gateway port (default "19531")')

	arguments = argumentParser.parse_args()

	#setup journal reader
	journal = JournalReader(arguments.path)
	
	if arguments.matches:
		journal.add_matches(arguments.matches)
	
	journal.set_timeframe(arguments.period)
	
	#parse journal
	ctr = 0
	for entry in journal:
		ctr += 1
		if arguments.verbose:
			print(entry["MESSAGE"], end="\n")
			
	if arguments.verbose:
		print(ctr, end="\n")
	
	if ctr in arguments.warning:
		returnCode = WARNING
		
	if ctr in arguments.critical:
		returnCode = CRITICAL
	
	if returnCode == UNKNOWN:
		returnCode = OK
	
	sys.exit(returnCode)

if __name__=="__main__":
	main()