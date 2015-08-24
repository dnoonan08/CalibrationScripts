import subprocess
import time
import sys
import os
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-d", "--dac", dest="dac",
                default="",
                help="The dac being used (default is -1)", metavar="STR")
parser.add_option("-c", "--channel", dest="channel",
                default="",
                help="The dac channel being used (default is -1)", metavar="STR")
parser.add_option("-v", "--version", dest="version",
                default="",
                help="The pigtail being used (default is -1)", metavar="STR")
parser.add_option("-o","--overwrite",action="store_false", dest="doCheck",default = False)

(options, args) = parser.parse_args()

channel = options.channel
dac = options.dac
version = options.version
doCheck = options.doCheck

if not version == "":
	version = "_v"+version

outTextFileName = "/afs/cern.ch/user/d/dnoonan/HCAL_Testing/CalibrationScripts/InjectionBoardCalibration/calibration_output/calibration_dac_%s_channel_%s%s.txt"%(dac,channel,version)

if doCheck:
	if os.path.exists(outTextFileName):
		print 'File', outTextFileName, 'exists already'
		print 'To replace this file, use the options -o or --overwrite'
		sys.exit()


#hostname = '128.141.168.19'
hostname = 'dnoonan@pb-d-128-141-168-96.cern.ch'
filename_dac_exe  = '/afs/cern.ch/user/d/dnoonan/HCAL_Testing/mcc-libhid/dacQinjector'
filename_keithley = '/Users/dnoonan/Work/CMS/HCAL/CalibrationScripts/Keithley/run_Keithley.py'

def readPoint(i_LSB):
	command = '{0} -o {1}'.format(filename_dac_exe, i_LSB )
	subprocess.call([command], shell=True)
	time.sleep(5)
		
	command = 'ssh {0} \'python {1} {2}\''.format(hostname, filename_keithley, i_LSB)        
	output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()
	return output[0]

last_current = 0

print outTextFileName

outputFile = open(outTextFileName,'w')

jumps = []

expectedSlope = 0.054e-6
firstPoint = True

for i in range(0,301,5):
	outputLine = readPoint(i)
	print outputLine
	outputFile.write(outputLine)
	current = float(outputLine.split(',')[1])
	if not firstPoint:
		# print current-last_current
		# print abs(current-last_current)
		# print 4.5*expectedSlope
		if abs(current-last_current) < 4.5*expectedSlope:
			print "STEP?"
			oneStepLast = last_current
			for j in range(i-4,i+1):
				outputLine = readPoint(j)
				print outputLine
				outputFile.write(outputLine)
				current_2 = float(outputLine.split(',')[1])
				if abs(current_2-oneStepLast) < 0.5*expectedSlope:
					print "step between", j-1, 'and', j
					jumps.append(j)
				oneStepLast = current_2
	last_current = current
	firstPoint = False
command = '{0} -o {1}'.format(filename_dac_exe, 0 )
subprocess.call([command], shell=True)

outputFile.write(str(jumps))
print jumps
