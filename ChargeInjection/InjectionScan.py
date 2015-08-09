from time import sleep
from datetime import date
import os
from optparse import OptionParser
import subprocess
import sys


sys.path.insert(0, '../../hcal_teststand_scripts')
sys.path.insert(0, '../../ChargeInjectionScripts')

from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *

from scans import *



# ldlibrarypath = subprocess.Popen('echo $LD_LIBRARY_PATH',stdout=PIPE,shell=True).communicate()[0]
# hasUsrLocalLib = '/usr/local/lib' in ldlibrarypath
# hasNGFEC = '/nfshome0/hcalpro/ngFEC' in ldlibrarypath

# if not hasUsrLocalLib and not hasNGFEC:
# 	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/nfshome0/hcalpro/ngFEC")
# elif hasNGFEC and not hasUsrLocalLib:
# 	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib")
# elif not hasNGFEC and hasUsrLocalLib:
# 	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/nfshome0/hcalpro/ngFEC")

# ldlibrarypath = subprocess.Popen('echo $LD_LIBRARY_PATH',stdout=PIPE,shell=True).communicate()[0]
# print ldlibrarypath


# path = subprocess.Popen('echo $PATH',stdout=PIPE,shell=True).communicate()[0]
# print path
# if not '/nfshome0/hcalpro/ngFEC' in path:
# 	os.system("export PATH=$PATH:/nfshome0/hcalpro/ngFEC")
# path = subprocess.Popen('echo $PATH',stdout=PIPE,shell=True).communicate()[0]
# print path

def setup(ts, range=0, useFixRange=True, useCalibrationMode=True):
	commands = [
		"get HF1-bkp_pwr_bad",
		"put HF1-bkp_reset 1",
		"put HF1-bkp_reset 0",
		"get HF1-adc56_f",
		"put HF1-2-QIE[1-24]_RangeSet 24*x",
		"get HF1-2-QIE[1-24]_RangeSet",
		"put HF1-2-QIE[1-24]_FixRange 24*1",
		"get HF1-2-QIE[1-24]_FixRange",
		"put HF1-2-QIE[1-24]_CalMode 24*1",
		"get HF1-2-QIE[1-24]_CalMode",
		"get HF1-2-iBot_StatusReg_QieDLLNoLock",
		"get HF1-2-iBot_StatusReg_PLL320MHzLock",
		"quit",
		]
	
	commands[4] = commands[4].replace('x',str(range))
	if not useFixRange:
		commands[6] = commands[6].replace('24*1','24*0')
	if not useCalibrationMode:
		commands[8] = commands[8].replace('24*1','24*0')

	output = ngccm.send_commands_parsed(ts, commands)
	for line in output['output']:
		print line['cmd'], line['result']

def setDAC( dacLSB = 0, dacChannel = -1):
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib; ~/../tiroy/mcc-libhid/dacQinjector  -o {0} -c {1}".format(dacLSB, dacChannel) )

def initLinks(ts):
	cmds = [
		'0',
		'link',
		'init',
		'1',
		'92',
		'0',
		'0',
		'0',
		'quit',
		'quit',
		'exit',
		'exit'
		]
	output = send_commands_script(ts, ts.uhtr_slots[0], cmds)
	for line in output['output']:
		print line['cmd'], line['result']


def doScan(ts, injCardNumber = 1, dacNumber = 1, scanRange = range(30), qieRange=0, useFixRange=True, useCalibrationMode=True, saveHistograms = True):



	if saveHistograms:
		outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode/{3}/".format(injCardNumber, dacNumber, qieRange, str(date.today() ) )
		os.system( "mkdir -pv "+outputDirectory )

	setup(ts,"{0}".format(qieRange))

	initLinks(ts)

	results = {}
	for i in scanRange:
		print i
		setDAC( i)
		# setup("{0}".format(options.scan))
		sleep(5)
		histName = ""
		if saveHistograms: histName = "Calibration_qiecard_{0}_LSB_{1}.root".format( cardNumber, i )
		fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=0, file_out=outputDirectory+histName)
		vals = uhtr.read_histo(fName)
		results[i] = vals
	
	setDAC(0)
	setup("{0}".format(qieRange))            


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-c", "--card", dest="cardnumber", default="2" ,
			  help="qie card number" )
	parser.add_option("-d", "--dac", dest="dacnumber", default="2" ,
			  help="DAC used" )
	parser.add_option("-r", "--range", dest="range",default=0 ,
			  help="choose which range you would like to scan: 0, 1, 2, 3, custom" )
	parser.add_option("-s", "--scan", dest="scan", default=[] ,
			  help="set a custom DAC range you want to scan over" )
	parser.add_option("--nofixed", action="store_false", dest="useFixedRange", default=True ,
			  help="do not use fixed range mode")
	parser.add_option("--nocalmode", action="store_false", dest="useCalibrationMode", default=True ,
			  help="do not use calibration mode" )
	parser.add_option("--save","--savehistos",action="store_true",dest="saveHistograms", default=False,
			  help="save the histogram output files")
	
	(options, args) = parser.parse_args()
	
	ts = teststand("904")

