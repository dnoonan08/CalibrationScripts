# Import tools
from ROOT import *
from math import sqrt
import sys
import re
from array import array 
import os
import string
import sqlite3 as lite
import csv

#from linearADC import *

gROOT.SetBatch(kTRUE)

nominalMapping = { 1 : 4,
                   2 : 4,
                   3 : 4,
                   4 : 4,
                   5 : 1,
                   6 : 2,
                   7 : 4,
                   8 : 4,
                   }

def makeADCvsfCgraph(lsbList, values, histo_list = range(0,96), cardMap = nominalMapping, dac='01',qieRange = 0):


    # Temprorary database made with nominal values, can switch over to real charge injector calibration later
#    conSlopes = lite.connect("../InjectionBoardCalibration/TestSlopesOffsets.db")

    conSlopes = lite.connect("../InjectionBoardCalibration/SlopesOffsets.db")


    if qieRange > 0:
        highCurrent = True
    else:
        highCurrent = False

    print highCurrent
    graphs = {}
    for ih in histo_list:
        QIE_values = []

        # Get channel from histogram
        print ih

        channel = (ih % 12 + 1)
        card = cardMap[int(ih/12)]

        # Get calibration for channel
        cur_Slopes = conSlopes.cursor()

        for i_lsb in lsbList:
            print int(highCurrent)
            query = ( channel, card, dac[0], int(highCurrent), i_lsb, i_lsb)
            cur_Slopes.execute('SELECT offset, slope FROM CARDCAL WHERE channel=? AND card=? AND dac=? AND highcurrent=? AND rangehigh>=? AND rangelow<=?', query )

            result_t = cur_Slopes.fetchone()

            offset = result_t[0]
            slope = result_t[1]

            current = i_lsb*slope + offset
            charge = current*25e6
            
            mean = values[i_lsb][ih]['mean']
            rms = values[i_lsb][ih]['rms']
            QIE_values.append([i_lsb,-1*charge,mean,rms])

        QIE_values.sort()

        fc_array = array('d',[b[1] for b in QIE_values])
        adc_array = array('d',[b[2] for b in QIE_values])
        adcerr_array = array('d',[b[3] for b in QIE_values])
        fCerror_array = array('d',[0]*len(fc_array))

        ADCvsfC =  TGraphErrors(len(fc_array),adc_array , fc_array,adcerr_array,fCerror_array)
        ADCvsfC.SetNameTitle("ADCvsfC_"+str(ih),"ADCvsfC_"+str(ih))

        graphs[ih]=ADCvsfC

    return graphs


def makeADCvsfCgraphSepCapID(lsbList, values, histo_list = range(0,96), cardMap = nominalMapping, dac='01', qieRange = 0):
#    conCardMap = createDB_HFcard(True)

    # Temprorary database made with nominal values, can switch over to real charge injector calibration later
    # conSlopes = lite.connect("../InjectionBoardCalibration/TempSlopesOffsets.db")

    conSlopes = lite.connect("../InjectionBoardCalibration/TestSlopesOffsets.db")
    print conSlopes

    if qieRange > 0:
        highCurrent = True
    else:
        highCurrent = False


    graphs = {}
    for ih in histo_list:
        QIE_values = []

        # Get channel from histogram

        print ih

        channel = (ih % 12 + 1)

        if int(ih/12) not in cardMap.keys(): continue

        card = cardMap[int(ih/12)]

        
        # Get calibration for channel
        cur_Slopes = conSlopes.cursor()

        for i_lsb in lsbList:
        

            query = ( channel, card, int(dac), int(highCurrent), i_lsb, i_lsb)
            cur_Slopes.execute('SELECT offset, slope FROM CARDCAL WHERE channel=? AND card=? AND dac=? AND highcurrent=? AND rangehigh>=? AND rangelow<=?', query )
            print highCurrent
            print query
            result_t = cur_Slopes.fetchone()
            print result_t
            offset = result_t[0]
            slope = result_t[1]

            current = i_lsb*slope + offset
            charge = current*25e6

            mean_ = []
            rms_ = []
            for i_capID in range(4):
                mean_.append(values[i_lsb][ih]['mean'][i_capID])
                rms_.append(values[i_lsb][ih]['rms'][i_capID])
            QIE_values.append([i_lsb,-1*charge,mean_,rms_])

        QIE_values.sort()

        graphs[ih] = []
        for i_capID in range(4):
            fc_array = array('d',[b[1] for b in QIE_values])
            fCerror_array = array('d',[0]*len(fc_array))

            lADC = []
            lADCerr = []

            for b in QIE_values:
#                lADC_, lADCerr_ = linADC(b[2][i_capID], b[3][i_capID])
                lADC_, lADCerr_ = 0,0
                lADC.append(lADC_)
                lADCerr.append(lADCerr_)

            adc_array = array('d',lADC)
            adcerr_array = array('d',lADCerr)

            ADCvsfC =  TGraphErrors(len(fc_array),adc_array , fc_array,adcerr_array,fCerror_array)
            ADCvsfC.SetNameTitle("LinADCvsfC_%i_capID_%i"%(ih,i_capID),"LinADCvsfC_%i_capID_%i"%(ih,i_capID))

            graphs[ih].append(ADCvsfC)

    return graphs

    
