from ROOT import *
from array import array
import os	

import subprocess
import sys

import sqlite3

sys.path.insert(0, '../../hcal_teststand_scripts')
from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *
from checkLinks_Old import *
from DAC import *

from numpy import mean

gROOT.SetBatch(kTRUE)

TDC_Scan_Values = range(10000,18000,400)

def check_qie_status(ts, crate, slot):
	commands = []
	commands.append("get HF{0}-{1}-QIE[1-24]_FixRange".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_RangeSet".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_CalMode".format(crate,slot))
	raw_output = ngccm.send_commands_parsed(ts, commands)['output']	

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

	for i_crate in fe_crates:
		for i_slot in qie_slots:
			print 'Set Fixed Range and Calibration mode Crate %i Slot %i' %(i_crate,i_slot)
			set_fix_range_all(ts, i_crate, i_slot, useFixRange, int(qieRange))
			set_cal_mode_all(ts, i_crate, i_slot, useCalibrationMode)
	goodStatus = True
	problemSlots = []
	sleep(3)
	for i_crate in fe_crates:
		for i_slot in qie_slots:
			qieGood, result, problems = check_qie_status(ts, i_crate, i_slot)
			if not qieGood:
				goodStatus = False
				problemSlots.append( (i_crate, i_slot) )
				print problems
	attempts = 0
	while not goodStatus and attempts < 10:
		goodStatus = True
		newProblemSlots = []
		for i_crate, i_slot in problemSlots:
			print 'Retry Set Fixed Range and Calibration mode Crate %i Slot %i' %(i_crate,i_slot)
			set_fix_range_all(ts, i_crate, i_slot, useFixRange, int(qieRange))
			set_cal_mode_all(ts, i_crate, i_slot, useCalibrationMode)
			sleep(3)
			qieGood, result,problems = check_qie_status(ts, i_crate, i_slot)
			if not qieGood:
				goodStatus = False
				newProblemSlots.append( (i_crate, i_slot) )
				print problems
			else:
				for reg in result:
					print reg, result[reg]
			
		attempts += 1
		problemSlots = newProblemSlots

	if not goodStatus:
		print "Can't get good QIE status"
		print "Exiting"
		sys.exit()



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
    
    return charge, current

def runTDCScan(mapping, dac, orbitDelay, outputDir = 'testDir'):

    if not os.path.exists(outputDir):
        os.system("mkdir -pv "+outputDir)

    ts = teststand("904")

    outputFile = TFile(outputDir+"/TDC_output.root",'recreate')

    
    getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], int(0), useFixRange=False, useCalibrationMode=True)
    # for i_crate in ts.fe_crates:
    #     for i_slot in ts.qie_slots[0]:
    #         print 'Set Calibration Mode'
    #         set_cal_mode_all(ts, i_crate, i_slot, True)
    
    tdc_start = [0]*96

    linkList = []
    histoList = []
    tdcHist = {}
    tdcHist['mean']={}
    tdcHist['mode']={}
    tdcHist['full']={}

    
    qlow, lowCurrent = getCharge(0, TDC_Scan_Values[0], mapping, dac)
    qhigh, highCurrent = getCharge(0, TDC_Scan_Values[-1], mapping, dac)

    lowCurrent *= -1.
    highCurrent *= -1.

    stepSize = (highCurrent - lowCurrent)/(len(TDC_Scan_Values)-1)
    lowCurrent -= stepSize/2.
    highCurrent += stepSize/2.

    tdcCurrents = TH1F("tdc_turnon_current","tdc_turnon_current",len(TDC_Scan_Values),lowCurrent, highCurrent)

    for i in mapping:
        for j in range(3):
            linkList += [i*3+j]
        for j in range(12):
            histoList += [i*12+j]
            tdcHist['mean'][i*12+j] = TH1F("tdcMeanVal_vs_lsb_h%i"%(i*12+j),"tdcMeanVal_vs_lsb_h%i"%(i*12+j),len(TDC_Scan_Values),lowCurrent, highCurrent)
            tdcHist['mode'][i*12+j] = TH1F("tdcModeVal_vs_lsb_h%i"%(i*12+j),"tdcModeVal_vs_lsb_h%i"%(i*12+j),len(TDC_Scan_Values),lowCurrent, highCurrent)
            tdcHist['full'][i*12+j] = TH2F("tdcVal_vs_lsb_h%i"%(i*12+j),"tdcVal_vs_lsb_h%i"%(i*12+j),        len(TDC_Scan_Values),lowCurrent, highCurrent, 64,0,64)

    print linkList
    print histoList
    for lsb in TDC_Scan_Values:
        setDAC(lsb)
        getGoodLinks(ts,orbitDelay, GTXreset = 1, CDRreset = 1)
        for i_link in linkList:
            tdc_le =  uhtr.get_data_parsed(ts,7,300,i_link)['tdc_le']
            for i_fiber in range(4):
                qieNum = i_link*4+i_fiber
                tdc_vals = [x[i_fiber] for x in tdc_le]
                charge, current = getCharge(qieNum, lsb, mapping, dac)
                tdcHist['mean'][qieNum].Fill(current*-1,mean(tdc_vals))
                tdcHist['mode'][qieNum].Fill(current*-1,max(set(tdc_vals), key=tdc_vals.count))
                for i_tdc in tdc_vals:
                    tdcHist['full'][qieNum].Fill(current*-1,i_tdc)
                if not tdc_start[qieNum] == 0: continue
                if tdc_vals.count(63) < len(tdc_vals)/2.:
                    tdc_start[qieNum] = current
                    tdcCurrents.Fill(current*-1.)
                    print qieNum                    
                    histoList.remove(qieNum)
        print histoList
#        if len(histoList)==0: break


    outputFile.cd()
    tdcCurrents.Write()
    for ih in tdcHist['mean']:
        tdcHist['mean'][ih].Write()
        tdcHist['mode'][ih].Write()
        tdcHist['full'][ih].Write()

    outputFile.Close()
    setDAC(0)

    getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], int(0), useFixRange=False, useCalibrationMode=False)

    return tdc_start

if __name__=="__main__":

    simpleMap = {0:5,
		 1:6,
                 2:1,
                 3:2,
		 # 2:1,
		 # 3:1,
		 # 4:4,
		 # 5:3,
		 # 6:1,
		 # 7:1,
		 }

    tdc_start = runTDCScan(simpleMap, '02', orbitDelay=38)

    print tdc_start
