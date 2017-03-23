from ROOT import *
from array import array
import os	

from time import sleep
from datetime import date, datetime

import subprocess
import sys

import sqlite3

sys.path.insert(0, '../../AcceptanceTests/hcal_teststand_scripts')
from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *
from checkLinks import *
from DAC import *

gROOT.SetBatch(kTRUE)

dacNum = '01'

orbitDelay = 38
GTXreset = 1
CDRreset = 1

transitionScanRange = {0 : range(420,520,2),
		       1 : range(3650,4150,20),
		       2 : range(29000, 32500,100),
		       }

# transitionScanRange = {0 : range(460,530,20),
# 		       1 : range(3650,3950,200),
# 		       2 : range(15000,16500,1000),
# 		       }


simpleMap = {0:5,
	     1:6,
	     2:1,
	     3:2,
	     # 4:4,
	     # 5:3,
	     # 6:1,
	     # 7:1,
	     }


def check_qie_status(ts, crate, slot):
	commands = []
	commands.append("get HF{0}-{1}-QIE[1-24]_FixRange".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_RangeSet".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_CalMode".format(crate,slot))
	raw_output = ngfec.send_commands_parsed(ts, cmds=commands,script=True)['output']	

	results = {}
	goodValues = True
	problems = []
	for val in raw_output:
		for setting in ['RangeSet','FixRange','CalMode']:
			if setting in val['cmd']:
				results[val['cmd']] = val['result']
			values = [float(x) for x in val['result'].split()]
			if not std(values)==0:
				goodValues = False
				problems.append([val['cmd'],val['result']])
	
	return goodValues, results, problems


def getGoodQIESetting(ts,fe_crates, qie_slots, qieRange=0, useFixRange= False, useCalibrationMode = False):

	cmds = []
	for i_crate in fe_crates:
		for i_slot in qie_slots:
			print 'Set Fixed Range and Calibration mode Crate %i Slot %i' %(i_crate,i_slot)
			cmds += ['put HF%i-%i-QIE[1-24]_FixRange 24*%i'%(int(i_crate),int(i_slot),int(useFixRange)),
				 'put HF%i-%i-QIE[1-24]_RangeSet 24*%i'%(int(i_crate),int(i_slot),int(qieRange)),
				 'put HF%i-%i-QIE[1-24]_CalMode 24*%i'%(int(i_crate),int(i_slot),int(useCalibrationMode))
				 ]
			raw_output = ngfec.send_commands(ts, cmds=cmds, script=True)
			sleep(1)
# def getGoodQIESetting(ts,fe_crates, qie_slots, qieRange=0, useFixRange= False, useCalibrationMode = False):

# 	for i_crate in fe_crates:
# 		for i_slot in qie_slots:
# 			print 'Set Fixed Range and Calibration mode Crate %i Slot %i' %(i_crate,i_slot)
# 			set_fix_range_all(ts, i_crate, i_slot, useFixRange, int(qieRange))
# 			set_cal_mode_all(ts, i_crate, i_slot, useCalibrationMode)
# 	goodStatus = True
# 	problemSlots = []
# 	sleep(3)
# 	for i_crate in fe_crates:
# 		for i_slot in qie_slots:
# 			qieGood, result, problems = check_qie_status(ts, i_crate, i_slot)
# 			if not qieGood:
# 				goodStatus = False
# 				problemSlots.append( (i_crate, i_slot) )
# 				print problems
# 	attempts = 0
# 	while not goodStatus and attempts < 10:
# 		goodStatus = True
# 		newProblemSlots = []
# 		for i_crate, i_slot in problemSlots:
# 			print 'Retry Set Fixed Range and Calibration mode Crate %i Slot %i' %(i_crate,i_slot)
# 			set_fix_range_all(ts, i_crate, i_slot, useFixRange, int(qieRange))
# 			set_cal_mode_all(ts, i_crate, i_slot, useCalibrationMode)
# 			sleep(3)
# 			qieGood, result,problems = check_qie_status(ts, i_crate, i_slot)
# 			if not qieGood:
# 				goodStatus = False
# 				newProblemSlots.append( (i_crate, i_slot) )
# 				print problems
# 			else:
# 				for reg in result:
# 					print reg, result[reg]
			
# 		attempts += 1
# 		problemSlots = newProblemSlots

# 	if not goodStatus:
# 		print "Can't get good QIE status"
# 		print "Exiting"
# 		sys.exit()


def get_transitionErrors(file_in = "", lowrange = 0):
	tf = TFile(file_in,"READ")
	transitionError = []
	offset = lowrange*64

	for ih in range(96):
		hist = tf.Get("h{0}".format(ih))

		integral_Tot = max(hist.Integral(-1,-1),1.)
		integral_type1 = hist.Integral(offset+1,offset+2)
		integral_type2 = hist.Integral(offset+3,offset+55)
		integral_type3 = hist.Integral(1,2)

		transitionError.append([integral_type1/integral_Tot, integral_type2/integral_Tot, integral_type3/integral_Tot])

	return transitionError

def transitionScan(qieRange, outputDirectory = '', runScan = True, orbitDelay=orbitDelay):

	scanRange = transitionScanRange[qieRange]
	
	if not os.path.exists(outputDirectory+"/TransitionScan_%i/"%(qieRange)):
		os.system("mkdir -p "+outputDirectory+"/TransitionScan_%i/"%(qieRange))

	ts = teststand("904cal",f="/nfshome0/dnoonan/AcceptanceTests/hcal_teststand_scripts/configuration/teststands.txt")


	if runScan:
		
		getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], int(0), useFixRange=False, useCalibrationMode=True)

		# for i_crate in ts.fe_crates:
		# 	for i_slot in ts.qie_slots[0]:
		# 		set_cal_mode_all(ts, i_crate, i_slot, True)
		# 		set_fix_range_all(ts, i_crate, i_slot, False)
		getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset)

	errorRate = {}
    
	for lsb in scanRange:
		print 'LSB', lsb
		histName = "Transition_LSB_{0}.root".format( lsb )
		if runScan:
			setDAC(lsb)
			getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset)
			fName = uhtr.get_histo(ts,crate=ts.be_crates[0],uhtr_slot=ts.uhtr_slots[0], n_orbits=10000, sepCapID=0, file_out=outputDirectory+"/TransitionScan_%i/"%(qieRange)+histName)
		else:
			fName = outputDirectory+"/TransitionScan_%i/"%(qieRange)+histName
		errorRate[lsb] = get_transitionErrors(fName, qieRange)

	if runScan: 
		setDAC(0)
		getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], int(0), useFixRange=False, useCalibrationMode=False)

		# for i_crate in ts.fe_crates:
		# 	for i_slot in ts.qie_slots[0]:
		# 		set_cal_mode_all(ts, i_crate, i_slot, False)
				
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

def runTransitionErrorScans(outDir, transitionRanges = [0,1,2], runScan = True, mapping = simpleMap, orbitDelay=orbitDelay):
	if not os.path.exists(outDir):
		os.system("mkdir -p "+outDir)

	outFile = TFile(outDir+'/ErrorRateHists.root','recreate')

	dacNum = getDACNumber()

	histoList = []
	print mapping
	for i in mapping.keys():
		for j in range(12):
			histoList.append(i*12+j)
	histoList.sort()
	print histoList

	errorRateLists = {}
	
	for qieRange in transitionRanges:
		errorRate = transitionScan(qieRange,outDir, runScan, orbitDelay=orbitDelay)
		hists = getErrorHists(errorRate, qieRange = qieRange, histRange=histoList, mapping = mapping, dac=dacNum)

		rootDir = "Transitions_%iTo%i"%(qieRange, qieRange+1)
		outFile.mkdir(rootDir)
		outFile.cd(rootDir)
		for ih in hists:
			hists[ih]['charge'][0].Write()
			hists[ih]['lsb'][0].Write()

			hists[ih]['charge'][1].Write()

			hists[ih]['lsb'][1].Write()

			hists[ih]['charge'][2].Write()

			hists[ih]['lsb'][2].Write()

		errorRateListsRange = {}
		for ih in hists:
			errorRateListsRange[ih] = {}
			errorRateListsRange[ih][1] = [hists[ih]['charge'][0].GetMaximum(), hists[ih]['charge'][0].GetBinCenter(hists[ih]['charge'][0].GetMaximumBin())]
			errorRateListsRange[ih][2] = [hists[ih]['charge'][1].GetMaximum(), hists[ih]['charge'][1].GetBinCenter(hists[ih]['charge'][1].GetMaximumBin())]
			errorRateListsRange[ih][3] = [hists[ih]['charge'][2].GetMaximum(), hists[ih]['charge'][2].GetBinCenter(hists[ih]['charge'][2].GetMaximumBin())]
		errorRateLists[qieRange]= errorRateListsRange

		

	binMult = sqrt(sqrt(10))
	bins = [1e-6]
	for i in range(20):
		bins.append(bins[-1]*binMult)
	from array import array
	bins_x = array('d',bins)
	
	r0t1_max = [TH1F("range0type1errors1","range0type1errors1",20,bins_x),TH1F("range0type1errors2","range0type1errors2",20,bins_x),TH1F("range0type1errors3","range0type1errors3",20,bins_x),TH1F("range0type1errors4","range0type1errors4",20,bins_x)]
	r0t2_max = [TH1F("range0type2errors1","range0type2errors1",20,bins_x),TH1F("range0type2errors2","range0type2errors2",20,bins_x),TH1F("range0type2errors3","range0type2errors3",20,bins_x),TH1F("range0type2errors4","range0type2errors4",20,bins_x)]
	r1t1_max = [TH1F("range1type1errors1","range1type1errors1",20,bins_x),TH1F("range1type1errors2","range1type1errors2",20,bins_x),TH1F("range1type1errors3","range1type1errors3",20,bins_x),TH1F("range1type1errors4","range1type1errors4",20,bins_x)]
	r1t2_max = [TH1F("range1type2errors1","range1type2errors1",20,bins_x),TH1F("range1type2errors2","range1type2errors2",20,bins_x),TH1F("range1type2errors3","range1type2errors3",20,bins_x),TH1F("range1type2errors4","range1type2errors4",20,bins_x)]
	r1t3_max = [TH1F("range1type3errors1","range1type3errors1",20,bins_x),TH1F("range1type3errors2","range1type3errors2",20,bins_x),TH1F("range1type3errors3","range1type3errors3",20,bins_x),TH1F("range1type3errors4","range1type3errors4",20,bins_x)]
	r2t1_max = [TH1F("range2type1errors1","range2type1errors1",20,bins_x),TH1F("range2type1errors2","range2type1errors2",20,bins_x),TH1F("range2type1errors3","range2type1errors3",20,bins_x),TH1F("range2type1errors4","range2type1errors4",20,bins_x)]
	r2t2_max = [TH1F("range2type2errors1","range2type2errors1",20,bins_x),TH1F("range2type2errors2","range2type2errors2",20,bins_x),TH1F("range2type2errors3","range2type2errors3",20,bins_x),TH1F("range2type2errors4","range2type2errors4",20,bins_x)]

	for ih in errorRateLists[0]:
		r0t1_max[int(ih/24)].Fill(errorRateLists[0][ih][1][0])
		r0t2_max[int(ih/24)].Fill(errorRateLists[0][ih][2][0])
	for ih in errorRateLists[0]:
		r1t1_max[int(ih/24)].Fill(errorRateLists[1][ih][1][0])
		r1t2_max[int(ih/24)].Fill(errorRateLists[1][ih][2][0])
		r1t3_max[int(ih/24)].Fill(errorRateLists[1][ih][3][0])
	for ih in errorRateLists[0]:
		r2t1_max[int(ih/24)].Fill(errorRateLists[2][ih][1][0])
		r2t2_max[int(ih/24)].Fill(errorRateLists[2][ih][2][0])


	outFile.cd('/')
	for i in range(4):
		r0t1_max[i].Write()
		r0t2_max[i].Write()
		r1t1_max[i].Write()
		r1t2_max[i].Write()
		r1t3_max[i].Write()
		r2t1_max[i].Write()
		r2t2_max[i].Write()

	return errorRateLists


if __name__=="__main__":
	from optparse import OptionParser

	parser = OptionParser()

	parser.add_option('-s','--skip','--skipscan',action="store_false",dest='runScan', default=True , help="skip running of scan, and use previously obtained data")
	parser.add_option('-r','--range',dest='range', default=-1 , type='int',help="selects which range transition to look at (value is for the lower range in transition, ex: 0 looks at 0->1 transition)")
	parser.add_option('-d','--dir',dest='directory', default='testDir',help='Output Directory Name')
	
	(options, args) = parser.parse_args()

	if int(options.range)==-1:
		transitionRanges = [0,1,2]
	else:
		transitionRanges = [int(options.range)]

	print options.range
	print type(options.range)
	print transitionRanges
	output = runTransitionErrorScans(outDir = options.directory, transitionRanges = transitionRanges, runScan = options.runScan, mapping = simpleMap)
		
