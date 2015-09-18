from time import sleep
from datetime import date, datetime
import os

import subprocess
import sys

from ROOT import *


sys.path.insert(0, '../../hcal_teststand_scripts')

from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *

transitionScans = {0 : range(400,500,10),
                   1 : range(3650,3950,20),

                   }


def initLinks(ts, orbitDelay = 58):
	cmds = [
		'0',
		'link',
		'init',
		'1',
		str(orbitDelay),
		'0',
		'0',
		'0',
		'quit',
		'exit',
		'-1'
		]

	output_init = uhtr.send_commands_script(ts, ts.uhtr_slots[0], cmds)

	sleep(2)

	cmds = [
		'0',
		'link',
		'status',
		'quit',
		'exit',
		'-1'
		]
	output_status = uhtr.send_commands_script(ts, ts.uhtr_slots[0], cmds)

	return output_init, output_status

def get_transitionIntegral(file_in = ""):
	tf = TFile(fName,"READ")
	transitionIntegrals = []
	for ih in range(96):
		
		hist = tf.Get("h{0}".format(ih))

def setDAC( dacLSB = 0, dacChannel = -1):
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib; ~/../tiroy/mcc-libhid/dacQinjector  -o {0} -c {1}".format(dacLSB, dacChannel) )
	sleep(3)

def transitionScan(qieRange, outputDirectory = ''):

	scanRange = transitionScans[qieRange]
	
	if not os.path.exists(outputDirectory+"/TransitionScan_%i/"%(qieRange)):
		os.system("mkdir -p "+outputDirectory+"/TransitionScan_%i/"%(qieRange))

	ts = teststand("904")
	
	init, status = initLinks(ts,58)
	
	print status['output']
    
	for lsb in scanRange:
		set_cal_mode_all(ts,1,2,False)
		
		histName = "Transition_LSB_{0}.root".format( lsb )
		print 'LSB', lsb
		setDAC(lsb)
		fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0], n_orbits=4000, sepCapID=0, file_out=outputDirectory+"/TransitionScan_%i/"%(qieRange)+histName)

	setDAC(0)
		
if __name__=="__main__":
	
	transitionScan(0,'testDir')
