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
from checkLinks import *
from DAC import *

from numpy import mean

gROOT.SetBatch(kTRUE)

scanValues = range(10000,18000,400)

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

    
    for i_crate in ts.fe_crates:
        for i_slot in ts.qie_slots[0]:
            print 'Set Calibration Mode'
            set_cal_mode_all(ts, i_crate, i_slot, True)
    
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
