#!/bin/python

import re, sys, argparse, os
from JournalReader import JournalReader

# define period
def period(string):
    if not re.search("^[1-9]{1,2}[m,h,d]$", string):
        msg = "%r is not a valid period" % string
        raise argparse.ArgumentTypeError(msg)
    return string
	
def printPerformanceData(label, ctr, warn, crit):
	data = ["%s=%s" % (label, str(ctr)), str(warn), str(crit)]
	print(";".join(data))

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
		'-w', '--warning', metavar='RANGE', default=1,
		help='return warning if count of found logs is outside RANGE')
	argumentParser.add_argument(
		'-c', '--critical', metavar='RANGE', default=2,
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
		'-m', '--matches', nargs='+',
		help='matches for logparse')
	argumentParser.add_argument(
		'--period', metavar='NUMBER', default='1h', type=period,
		help='check log of last period (default: "1h", format 1-99 m/h/d)')
	argumentParser.add_argument(
		'-r', '--regex', help='Regular expression to match message content'
	)

	arguments = argumentParser.parse_args()

	print(arguments)
	print(os.getuid())
	
	if arguments.hostname == "localhost":
		#setup journal reader
		journal = JournalReader()
		
		if arguments.matches:
			journal.add_matches(arguments.matches)
		
		
		journal.set_timeframe(arguments.period)
		
		if arguments.regex:
			regex = re.compile(arguments.regex)
			print(regex)
			# filter journal by regex
			journal = [entry for entry in journal if regex.search(entry["MESSAGE"])]
			
			if regex.groups == 1:
				ctr = {}
			else:
				ctr = 0
		else:
			ctr = 0
		
		
		#parse journal
		for entry in journal:
			if arguments.verbose:
				print(str(entry["__REALTIME_TIMESTAMP"]) + ": " + entry["MESSAGE"], end="\n")
			
			if type(ctr) is dict:
				match = regex.search(entry["MESSAGE"])
				ctr.setdefault(match.group(1), 0)
				ctr[match.group(1)] += 1
			else:
				ctr += 1
		
		
		returnCode = OK
		
		if type(ctr) is dict:
			for key, val in ctr.items():
				if val in range(arguments.warning, arguments.critical-1):
					returnCode = WARNING
				
				if val >= arguments.critical:
					returnCode = CRITICAL
			
				printPerformanceData(key, val, arguments.warning, arguments.critical)
		else:
			if ctr in range(arguments.warning, arguments.critical-1):
				returnCode = WARNING
				
				
			if ctr >= arguments.critical:
				returnCode = CRITICAL
		
			printPerformanceData("count", ctr, arguments.warning, arguments.critical)
	else:
		#TODO: Call remote plugin
		pass
		
	
	sys.exit(returnCode)

if __name__=="__main__":
	main()