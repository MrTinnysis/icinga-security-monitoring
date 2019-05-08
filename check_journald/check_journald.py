#!/bin/python

import re, sys, argparse
from monitoringplugin.JournalReader import JournalReader

# define period
def period(string):
    if not re.search("^[1-9]{1,2}[m,h,d]$", string):
        msg = "%r is not a valid period" % string
        raise argparse.ArgumentTypeError(msg)
    return string

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
		'-v', '--verbose', default=False,
		help='verbose output')
	argumentParser.add_argument(
		'-w', '--warning', metavar='RANGE', default='',
		help='return warning if count of found logs is outside RANGE')
	argumentParser.add_argument(
		'-c', '--critical', metavar='RANGE', default='',
		help='return critical if count of found logs is outside RANGE')
	argumentParser.add_argument(
		'--hostname', metavar='HOST', default='localhost',
		help='host with systemd journal gateway or localhost for direct access (default "localhost")')
	argumentParser.add_argument(
		'--port', metavar='NUMBER', default='19531',
		help='the gateway port (default "19531")')
	argumentParser.add_argument(
		'--path',
		help='path to journal log folder')
	argumentParser.add_argument(
		'--matches', nargs='+',
		help='matches for logparse')
	argumentParser.add_argument(
		'--period', metavar='NUMBER', default='1h', type=period,
		help='check log of last period (default: "1h", format 1-99 m/h/d)')

	arguments = argumentParser.parse_args()

	print(arguments)

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