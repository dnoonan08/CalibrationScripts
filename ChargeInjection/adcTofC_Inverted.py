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



nominalMapping = { 1 : 4,
                   2 : 4,
                   3 : 4,
                   4 : 4,
                   5 : 1,
                   6 : 2,
                   7 : 4,
                   8 : 4,
                   }

def makeADCvsfCgraph(lsbList, values, histo_list = range(0,96), cardMap = nominalMapping, dac='01'):

    conSlopes = lite.connect("../InjectionBoardCalibration/SlopesOffsets.db")
    graphs = {}
    for ih in histo_list:
        QIE_values = []

        # Get channel,pigtial from histogram
        print ih

        pigtail = 2 * (ih % 12 + 1)
        card = cardMap[int(ih/12)]

        # Get calibration for channel
        cur_Slopes = conSlopes.cursor()

        for i_lsb in lsbList:

            query = ( pigtail, card, dac, i_lsb, i_lsb)
            cur_Slopes.execute('SELECT offset, slope, offsetErr, slopeErr FROM CARDCAL WHERE pigtail=? AND card=? AND dac=? AND rangehigh>=? AND rangelow<=?', query )
            result_t = cur_Slopes.fetchone()
            print query
            print result_t
            offset = result_t[0]
            slope = result_t[1]
            offsetErr = result_t[2]
            slopeErr = result_t[3]
            print "Slope = "+str(slope) + " Offset= "+str(offset)

            current = i_lsb*slope + offset
            charge = current*25e6

            chargeErr = 25e6((i_lsb*slopeErr)**2 + offsetErr**2)**0.5

#            print ih, values[i_lsb][ih]['link']*4 + values[i_lsb][ih]['channel']
            
            mean = values[i_lsb][ih]['mean']
            rms = values[i_lsb][ih]['rms']
            QIE_values.append([i_lsb,-1*charge,mean,rms,chargeErr])

        QIE_values.sort()

        fc_array = array('d',[b[1] for b in QIE_values])
        adc_array = array('d',[b[2] for b in QIE_values])
        adcerr_array = array('d',[b[3] for b in QIE_values])
        fCerror_array = array('d',[b[4] for b in QIE_values])

        ADCvsfC =  TGraphErrors(len(fc_array),adc_array , fc_array,adcerr_array,fCerror_array)
        ADCvsfC.SetNameTitle("ADCvsfC_"+str(ih),"ADCvsfC_"+str(ih))

        graphs[ih]=ADCvsfC

    return graphs


def makeADCvsfCgraphSepCapID(lsbList, values, histo_list = range(0,96), cardMap = nominalMapping, dac='01'):
    conSlopes = lite.connect("../InjectionBoardCalibration/SlopesOffsets.db")

    graphs = {}
    for ih in histo_list:
        QIE_values = []

        # Get channel,pigtial from histogram
        print ih

        pigtail = 2 * (ih % 12 + 1)

        if int(ih/12) not in cardMap.keys(): continue

        card = cardMap[int(ih/12)]

        # Get calibration for channel
        cur_Slopes = conSlopes.cursor()

        for i_lsb in lsbList:
        

            query = ( pigtail, card, dac, i_lsb, i_lsb)
            cur_Slopes.execute('SELECT offset, slope FROM CARDCAL WHERE pigtail=? AND card=? AND dac=? AND rangehigh>=? AND rangelow<=?', query )
            result_t = cur_Slopes.fetchone()
            offset = result_t[0]
            slope = result_t[1]

            current = i_lsb*slope + offset
            charge = current*25e6

            
            # print ih, values[i_lsb][ih]['link']*4 + values[i_lsb][ih]['channel']

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
            adc_array = array('d',[b[2][i_capID] for b in QIE_values])
            adcerr_array = array('d',[b[3][i_capID] for b in QIE_values])

            ADCvsfC =  TGraphErrors(len(fc_array), fc_array,adc_array,fCerror_array ,adcerr_array)
            ADCvsfC.SetNameTitle("ADCvsfC_%i_capID_%i"%(ih,i_capID),"ADCvsfC_%i_capID_%i"%(ih,i_capID))

            graphs[ih].append(ADCvsfC)

    return graphs

    
