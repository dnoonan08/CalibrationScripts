from ROOT import *
from array import array

import os	

from time import sleep
from datetime import date, datetime

import subprocess
import sys

import sqlite3

sys.path.insert(0, '../../hcal_teststand_scripts')
from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *
from checkLinks import *
from DAC import *

dacNum = '01'


transitionScanRange = {0 : range(420,520,2),
		       1 : range(3650,3950,20),
		       2 : range(31000, 35000, 500),
		       }

# transitionScanRange = {0 : range(460,500,20),
# 		       1 : range(3650,3950,200),
# 		       2 : range(15000,16500,1000),
# 		       }


simpleMap = {0:1,
	     1:2,
	     2:1,
	     3:1,
	     4:4,
	     5:3,
	     6:1,
	     7:1,
	     }

def get_transitionErrors(file_in = "", lowrange = 0):
	tf = TFile(file_in,"READ")
	transitionError = []
	offset = lowrange*64

	for ih in range(96):
		hist = tf.Get("h{0}".format(ih))

		integral_Tot = max(hist.Integral(-1,-1),1.)
		integral_type1 = hist.Integral(offset+1,offset+2)
		integral_type2 = hist.Integral(offset+3,offset+58)
		integral_type3 = hist.Integral(1,2)

		transitionError.append([integral_type1/integral_Tot, integral_type2/integral_Tot, integral_type3/integral_Tot])

	return transitionError

def transitionScan(qieRange, outputDirectory = '', runScan = True):

	scanRange = transitionScanRange[qieRange]
	
	if not os.path.exists(outputDirectory+"/TransitionScan_%i/"%(qieRange)):
		os.system("mkdir -p "+outputDirectory+"/TransitionScan_%i/"%(qieRange))

	ts = teststand("904")

	if runScan:
		getGoodLinks(ts)

	errorRate = {}
    
	for lsb in scanRange:
		print 'LSB', lsb
		histName = "Transition_LSB_{0}.root".format( lsb )
		if runScan:
			set_cal_mode_all(ts,1,2,False)		
			setDAC(lsb)
			fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0], n_orbits=10000, sepCapID=0, file_out=outputDirectory+"/TransitionScan_%i/"%(qieRange)+histName)
		else:
			fName = outputDirectory+"/TransitionScan_%i/"%(qieRange)+histName
		errorRate[lsb] = get_transitionErrors(fName, qieRange)

	if runScan: setDAC(0)

	return errorRate

def getCharge(ih, lsb, mapping, dac):
	pigtail = 2 * (ih % 12 + 1)
	card = mapping[int(ih/12)]
	conSlopes = sqlite3.connect("../InjectionBoardCalibration/SlopesOffsets.db")
	cur_Slopes = conSlopes.cursor()
	query = ( pigtail, card, dac, lsb, lsb)
	cur_Slopes.execute('SELECT offset, slope FROM CARDCAL WHERE pigtail=? AND card=? AND dac=? AND rangehigh>=? AND rangelow<=?', query )
	result_t = cur_Slopes.fetchone()
	offset = result_t[0]
	slope = result_t[1]
	current = lsb*slope + offset
	charge = current*-25e6

	return charge

def getErrorHists(errorRate, histRange = range(96), qieRange = 0, mapping = simpleMap, dac = '01'):
	keys = errorRate.keys()
	keys.sort()	

	hists = {}


	for ih in histRange:
		charge_min = getCharge(ih,keys[0],mapping, dac)-0.1
		charge_max = 2.*getCharge(ih,keys[-1], mapping, dac) - getCharge(ih,keys[-2], mapping, dac) - 0.1

		type1Errors_lsb = TH1F("Transition_%iTo%i_type1Errors_h%i_lsb"%(qieRange,qieRange+1,ih),"Transition_%iTo%i_type1Errors_h%i_lsb"%(qieRange,qieRange+1,ih),len(keys), keys[0], keys[-1] + (keys[-1]-keys[-2]))
		type2Errors_lsb = TH1F("Transition_%iTo%i_type2Errors_h%i_lsb"%(qieRange,qieRange+1,ih),"Transition_%iTo%i_type2Errors_h%i_lsb"%(qieRange,qieRange+1,ih),len(keys), keys[0], keys[-1] + (keys[-1]-keys[-2]))		
		type3Errors_lsb = TH1F("Transition_%iTo%i_type3Errors_h%i_lsb"%(qieRange,qieRange+1,ih),"Transition_%iTo%i_type3Errors_h%i_lsb"%(qieRange,qieRange+1,ih),len(keys), keys[0], keys[-1] + (keys[-1]-keys[-2]))

		type1Errors_charge = TH1F("Transition_%iTo%i_type1Errors_h%i_charge"%(qieRange,qieRange+1,ih),"Transition_%iTo%i_type1Errors_h%i_charge"%(qieRange,qieRange+1,ih),len(keys), charge_min, charge_max)
		type2Errors_charge = TH1F("Transition_%iTo%i_type2Errors_h%i_charge"%(qieRange,qieRange+1,ih),"Transition_%iTo%i_type2Errors_h%i_charge"%(qieRange,qieRange+1,ih),len(keys), charge_min, charge_max)
		type3Errors_charge = TH1F("Transition_%iTo%i_type3Errors_h%i_charge"%(qieRange,qieRange+1,ih),"Transition_%iTo%i_type3Errors_h%i_charge"%(qieRange,qieRange+1,ih),len(keys), charge_min, charge_max)



		for k in keys:
			charge = getCharge(ih,k,mapping, dac)
			type1Errors_lsb.Fill(k, errorRate[k][ih][0])
			type2Errors_lsb.Fill(k, errorRate[k][ih][1])
			type3Errors_lsb.Fill(k, errorRate[k][ih][2])
			type1Errors_charge.Fill(charge, errorRate[k][ih][0])
			type2Errors_charge.Fill(charge, errorRate[k][ih][1])
			type3Errors_charge.Fill(charge, errorRate[k][ih][2])
		
		hists[ih] = {'lsb':    [type1Errors_lsb, type2Errors_lsb, type3Errors_lsb],
			     'charge': [type1Errors_charge, type2Errors_charge, type3Errors_charge],
			     }
	return hists

def runTransitionErrorScans(outDir, transitionRanges = [0,1,2], runScan = True, mapping = simpleMap):
	if not os.path.exists(outDir):
		os.system("mkdir -p "+outDir)

	outFile = TFile(outDir+'/TransitionErrorHists.root','recreate')

	dacNum = getDACNumber()

	for qieRange in transitionRanges:
		errorRate = transitionScan(qieRange,outDir, runScan)
		hists = getErrorHists(errorRate, qieRange = qieRange, mapping = mapping, dac=dacNum)

		rootDir = "Transitions_%iTo%i"%(qieRange, qieRange+1)
		outFile.mkdir(rootDir)
		outFile.cd(rootDir)
		gDirectory.mkdir("type1_charge")
		gDirectory.mkdir("type2_charge")
		gDirectory.mkdir("type3_charge")
		gDirectory.mkdir("type1_lsb")
		gDirectory.mkdir("type2_lsb")
		gDirectory.mkdir("type3_lsb")

		outFile.cd()
		outFile.cd("/"+rootDir+"/type1_charge")
		for ih in hists:
			hists[ih]['charge'][0].Write()

		outFile.cd("/"+rootDir+"/type1_lsb")
		for ih in hists:
			hists[ih]['lsb'][0].Write()

		outFile.cd("/"+rootDir+"/type2_charge")
		for ih in hists:
			hists[ih]['charge'][1].Write()

		outFile.cd("/"+rootDir+"/type2_lsb")
		for ih in hists:
			hists[ih]['lsb'][1].Write()

		outFile.cd("/"+rootDir+"/type3_charge")
		for ih in hists:
			hists[ih]['charge'][2].Write()

		outFile.cd("/"+rootDir+"/type3_lsb")
		for ih in hists:
			hists[ih]['lsb'][2].Write()

if __name__=="__main__":
	from optparse import OptionParser

	parser = OptionParser()

	parser.add_option('-s','--skip','--skipscan',action="store_false",dest='runScan', default=True , help="skip running of scan, and use previously obtained data")
	parser.add_option('-r','--range',dest='range', default=-1 , type='int',help="selects which range transition to look at (value is for the lower range in transition, ex: 0 looks at 0->1 transition)")
	parser.add_option('-d','--dir',dest='directory', default='testDir',help='Output Directory Name')
	
	(options, args) = parser.parse_args()

	if int(options.range)==-1:
		transitionRanges = [0,1]
	else:
		transitionRanges = [int(options.range)]

	print options.range
	print type(options.range)
	print transitionRanges
	runTransitionErrorScans(outDir = options.directory, transitionRanges = transitionRanges, runScan = options.runScan, mapping = simpleMap)
		
