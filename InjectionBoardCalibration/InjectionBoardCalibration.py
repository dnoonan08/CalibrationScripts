import subprocess
import time
import sys
import os
from optparse import OptionParser

from DACjumps import *

parser = OptionParser()
parser.add_option("-d", "--dac", dest="dac",
                default="",
                help="The dac being used (default is -1)", metavar="STR")
parser.add_option("-c", "--card", dest="card",
                default="",
                help="The card being used (default is -1)", metavar="STR")
parser.add_option("-p", "--pigtail", dest="pigtail",
                default="",
                help="The pigtail being used (default is -1)", metavar="STR")
parser.add_option("-v", "--version", dest="version",
                default="",
                help="The pigtail being used (default is -1)", metavar="STR")
parser.add_option("-o","--overwrite",action="store_false", dest="doCheck",default = True)

(options, args) = parser.parse_args()

pigtail = options.pigtail
card = options.card
dac = options.dac
version = options.version
doCheck = options.doCheck

if not version == "":
	version = "_v"+version

outTextFileName = "/afs/cern.ch/user/d/dnoonan/HCAL_Testing/CalibrationScripts/InjectionBoardCalibration/NewCard_calibration_output/calibration_output_card_%s_dac_%s_pigtail_%s%s.txt"%(card,dac,pigtail,version)


if doCheck:
	if os.path.exists(outTextFileName):
		print 'File', outTextFileName, 'exists already'
		print 'To replace this file, use the options -o or --overwrite'
		sys.exit()


#hostname = '128.141.168.19'
hostname = 'dnoonan@pb-d-128-141-168-96.cern.ch'
filename_dac_exe  = '/afs/cern.ch/user/d/dnoonan/HCAL_Testing/mcc-libhid/dacQinjector'
filename_keithley = '/Users/dnoonan/Work/CMS/HCAL/CalibrationScripts/Keithley/run_Keithley.py'

def calibration_saveToTextFile(range,outFileName = 'calibration_output.txt'):
	outFile = open(outFileName,'w')

	for i in range:
    		command = '{0} -o {1}'.format(filename_dac_exe, i )
    		subprocess.call([command], shell=True)
    		time.sleep(5)
		outFail = 1
    		command = 'ssh {0} python {1} {2}'.format(hostname, filename_keithley, i)
		while outFail != 0:
			outFail = subprocess.call(command.split(), stdout=outFile)

DACchannel = PigtailToDAC[int(pigtail)]

print scanRanges[dac][DACchannel]

#calibration_saveToTextFile(scanRange[dac][DACchannel],outTextFileName)

# command = '{0} -o {1}'.format(filename_dac_exe, 0 )
# subprocess.call([command], shell=True)

