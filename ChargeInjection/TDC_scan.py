from ROOT import *
from array import array
import os	

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

from numpy import mean

gROOT.SetBatch(True)

scanValues = range(10000,18000,400)

def getTDC(ts, i_link):
    outFile = file("spy_cmds.txt",'w')
    cmds = ['link',
            'spy',
            '%i'%i_link,
            '0',
            '0',
            '32',
            'quit',
            'quit']
    for cmd in cmds:
        outFile.write(cmd+'\n')
    outFile.close()
    a = subprocess.Popen("uHTRtool.exe -c %i:%i < spy_cmds.txt"%(ts.be_crates[0],ts.uhtr_slots[0][0]),stdout=subprocess.PIPE,shell=True).communicate()[0]

    lines = a.split('\n')
    tdcs = []
    for i in range(len(lines)):
        line = lines[i]
        if 'LE-TDC' in line:
            vals = line.split()[-4:]
            vals.reverse()
            vals = [int(v) for v in vals]
            tdcs.append(vals)

    return tdcs

def getTDC_all(ts, links):
    print 'Get TDC'
    outFile = file("spy_cmds.txt",'w')
    cmds = ['link',]

    for i_link in links:
        cmds += ['THIS IS FIBER %i'%i_link,
                 'spy',
                 '%i'%i_link,
                 '0',
                 '0',
                 '200']
    cmds += ['quit',
             'quit']

    for cmd in cmds:
        outFile.write(cmd+'\n')
    outFile.close()
    a = subprocess.Popen("uHTRtool.exe -c %i:%i < spy_cmds.txt"%(ts.be_crates[0],ts.uhtr_slots[0][0]),stdout=subprocess.PIPE,shell=True).communicate()[0]

    lines = a.split('\n')
    tdcs = {}
    for i_link in links:
        tdcs[i_link] = []

    for i in range(len(lines)):
        line = lines[i]
        if '> THIS IS FIBER' in line:
            fiberNum = int(line.split()[-1])
        if 'LE-TDC' in line:
            vals = line.split()[-4:]
            vals.reverse()
            vals = [int(v) for v in vals]
            tdcs[fiberNum].append(vals)

    return tdcs


def check_qie_status(ts, crate, slot):
	commands = []
	commands.append("get HF{0}-{1}-QIE[1-24]_FixRange".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_RangeSet".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_CalMode".format(crate,slot))
	raw_output = ngfec.send_commands_parsed(ts,cmds= commands, script=True)['output']	

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

def runTDCScan(mapping, dac, orbitDelay, linkToUIDMap, outputDir = 'testDir'):

    if not os.path.exists(outputDir):
        os.system("mkdir -pv "+outputDir)

    ts = teststand("904cal",f="/nfshome0/dnoonan/AcceptanceTests/hcal_teststand_scripts/configuration/teststands.txt")



    
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

    
    qlow, lowCurrent = getCharge(0, scanValues[0], mapping, dac)
    qhigh, highCurrent = getCharge(0, scanValues[-1], mapping, dac)

    lowCurrent *= -1.
    highCurrent *= -1.

    stepSize = (highCurrent - lowCurrent)/(len(scanValues)-1)
    lowCurrent -= stepSize/2.
    highCurrent += stepSize/2.

    tdcCurrents = TH1F("tdc_turnon_current","tdc_turnon_current",len(scanValues),lowCurrent, highCurrent)

    for i in mapping:
        for j in range(3):
            linkList += [i*3+j]
        for j in range(12):
            histoList += [i*12+j]
            tdcHist['mean'][i*12+j] = TH1F("tdcMeanVal_vs_lsb_h%i"%(i*12+j),"tdcMeanVal_vs_lsb_h%i"%(i*12+j),len(scanValues),lowCurrent, highCurrent)
            tdcHist['mode'][i*12+j] = TH1F("tdcModeVal_vs_lsb_h%i"%(i*12+j),"tdcModeVal_vs_lsb_h%i"%(i*12+j),len(scanValues),lowCurrent, highCurrent)
            tdcHist['full'][i*12+j] = TH2F("tdcVal_vs_lsb_h%i"%(i*12+j),"tdcVal_vs_lsb_h%i"%(i*12+j),        len(scanValues),lowCurrent, highCurrent, 64,0,64)

    print linkList
    print histoList
    for lsb in scanValues:
        setDAC(lsb)
        getGoodLinks(ts,orbitDelay, GTXreset = 1, CDRreset = 1)
        tdc_list =  getTDC_all(ts, linkList)
        for i_link in linkList:
#            tdc_le =  getTDC(ts, i_link)
	    # tdc_le = uhtr.get_data_parsed(ts,ts.uhtr_slots[0],300,i_link)['tdc_le']
            tdc_le = tdc_list[i_link]
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
#                    tdcCurrents.Fill(current*-1.)
                    print qieNum                    
                    histoList.remove(qieNum)
        print histoList
#        if len(histoList)==0: break




    for ih in tdcHist['mean']:
        linkVal = (ih-ih%12)/4
        uID = linkToUIDMap[linkVal]
        outputFile = TFile("%s/fitResults_%s.root"%(outputDir, uID),"update")
        outputFile.cd("TDC")
        tdcHist['mean'][ih].Write()
        tdcHist['mode'][ih].Write()
        tdcHist['full'][ih].Write()
        outputFile.Close()
    setDAC(0)

    getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], int(0), useFixRange=False, useCalibrationMode=False)

    return tdc_start

if __name__=="__main__":

    simpleMap = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8}

    tdc_start = runTDCScan(simpleMap, '02', orbitDelay=27)

    print tdc_start
