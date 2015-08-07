from time import sleep
from datetime import date
import os
from optparse import OptionParser
import subprocess
import sys


sys.path.insert(0, 'hcal_teststand_scripts')
sys.path.insert(0, 'ChargeInjectionScripts')

from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *

from scans import *

#from scans import *

parser = OptionParser()
parser.add_option("-c", "--card", dest="cardnumber", default="2" ,
                  help="qie card number" )
parser.add_option("-d", "--dac", dest="dacnumber", default="2" ,
                  help="DAC used" )
parser.add_option("-s", "--scan", dest="scan", default="custom" ,
                  help="choose which range you would like to scan: 0, 1, 2, 3, custom" )

(options, args) = parser.parse_args()

fixRange = options.scan

ts = teststand("904")

print 'loaded ts'

ldlibrarypath = subprocess.Popen('echo $LD_LIBRARY_PATH',stdout=PIPE,shell=True).communicate()[0]
print ldlibrarypath
hasUsrLocalLib = '/usr/local/lib' in ldlibrarypath
hasNGFEC = '/nfshome0/hcalpro/ngFEC' in ldlibrarypath

if not hasUsrLocalLib and not hasNGFEC:
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/nfshome0/hcalpro/ngFEC")
elif hasNGFEC and not hasUsrLocalLib:
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib")
elif not hasNGFEC and hasUsrLocalLib:
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/nfshome0/hcalpro/ngFEC")

ldlibrarypath = subprocess.Popen('echo $LD_LIBRARY_PATH',stdout=PIPE,shell=True).communicate()[0]
print ldlibrarypath


path = subprocess.Popen('echo $PATH',stdout=PIPE,shell=True).communicate()[0]
print path
if not '/nfshome0/hcalpro/ngFEC' in path:
	os.system("export PATH=$PATH:/nfshome0/hcalpro/ngFEC")
path = subprocess.Popen('echo $PATH',stdout=PIPE,shell=True).communicate()[0]
print path

def setup(range=0):
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

	output = ngccm.send_commands_parsed(ts, commands)
	for line in output['output']:
		print line['cmd'], line['result']


# 	output = ngccm.send_commands_parsed(ts, commands[:4])
# 	for line in output['output']:
# 		print line['cmd'], line['result']

# 	output = ngccm.send_commands_parsed(ts, commands[4:8])
# 	for line in output['output']:
# 		print line['cmd'], line['result']

# 	output = ngccm.send_commands_parsed(ts, commands[8:])
# 	for line in output['output']:
# 		print line['cmd'], line['result']

def setDAC( dacLSB = 0, dacChannel = -1):
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib; ~/../tiroy/mcc-libhid/dacQinjector  -o {0} -c {1}".format(dacLSB, dacChannel) )

outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode/{3}/".format(options.cardnumber, options.dacnumber,options.scan, str(date.today() ) )
os.system( "mkdir -pv "+outputDirectory )

print 'start setup'

setup("{0}".format(options.scan))

print 'done setup'

scanRange = scans[options.scan]
scanRange = range(0,51,5)
scanRange = [100]
print scanRange

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
result = send_commands_script(ts, ts.uhtr_slots[0], cmds)

 
for i in scanRange:
	print i
	setDAC( i)
#        setup("{0}".format(options.scan))
	sleep(5)
	histName = "Calibration_qiecard_{0}_LSB_{1}.root".format( options.cardnumber, i )
	fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=0, file_out=outputDirectory+histName)
	vals = uhtr.read_histo(fName)
#	print vals
	#    saveHisto( outputDirectory+"Calibration_qiecard_{0}_LSB_{1}.root".format( options.cardnumber, i ) )
	
setDAC(0)
setup("{0}".format(options.scan))            
