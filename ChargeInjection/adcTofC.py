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


def createDB_HFcard(verbose=False):

    # card, pigtail, channel, histo
    injectorMap = (
        (1, 2,  1,  60),
        (1, 4,  2,  61),
        (1, 6,  3,  62),
        (1, 8,  4,  63),
        (1, 10, 5,  64),
        (1, 12, 6,  65),
        (1, 14, 7,  66),
        (1, 16, 8,  67),
        (1, 18, 9,  68),
        (1, 20, 10, 69),
        (1, 22, 11, 70),
        (1, 24, 12, 71),
        )
    con = lite.connect(":memory:")

    with con:

        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS HFcard")
        cur.execute("CREATE TABLE HFcard(card INT, pigtail INT, channel INT, histo INT)")
        cur.executemany("INSERT INTO HFcard VALUES(?, ?, ?, ?)", injectorMap)

        if verbose:
            #
            cur.execute("SELECT * FROM HFcard")
            header = ''
            for f in cur.description:
                header += f[0]+ "  "
            print header

            rows = cur.fetchall()
            for row in rows:
                print row

    return con


def createDB_fromCSV( filename, verbose=False ):
    """Create a sqlite DB from a CSV file"""
    con = lite.connect(":memory:")
    cur = con.cursor()
    cur.execute("CREATE TABLE CARDCAL (card INT, pigtail INT, rangelow REAL, rangehigh REAL, offset REAL, slope REAL);")
    reader = csv.reader(open(filename, 'r'), delimiter=',')
    for row in reader:
        to_db = [unicode(row[0], "utf8"), unicode(row[1], "utf8"), unicode(row[2], "utf8"), unicode(row[3], "utf8"), unicode(row[4], "utf8"), unicode(row[5], "utf8")]
        cur.execute("INSERT INTO CARDCAL (card, pigtail, rangelow, rangehigh, offset, slope) VALUES (?, ?, ?, ?, ?, ?);", to_db)
    con.commit()    
    if verbose:
        cur.execute("SELECT * FROM CARDCAL")
        header = ''
        for f in cur.description:
            header += f[0]+ "  "
        print header
        rows = cur.fetchall()
        for row in rows:
            print row
    return con

def createDB_QIE(verbose=False):
    """Create a table with the QIE10 specs"""
    qie10 = (
        (0, -15.6,   34,  0, 15,   3.1 ),
        (0,    34,  158, 16, 35,   6.2 ),
        (0,   158,  419, 36, 56,  12.4 ),
        (0,   419,  592, 57, 63,  24.8 )
        ) 

    #con = lite.connect('QIE10specs.db')
    con = lite.connect(":memory:")

    with con:
    
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS QIE10")
        cur.execute("CREATE TABLE QIE10(range INT, low_input_charge INT, high_input_charge INT, low_ADC INT, high_ADC INT, sensitivity REAL)")
        cur.executemany("INSERT INTO QIE10 VALUES(?, ?, ?, ?, ?, ?)", qie10)

        if verbose:
            print "QIE10 Table created."
            cur.execute("SELECT * FROM QIE10")
            header = ''
            for f in cur.description:
                header += f[0]+ "  "
            print header

            rows = cur.fetchall()
            for row in rows:
                print row

    return con

def makeADCvsfCgraph(lsbList, values, histo_list = range(0,96)):
    conCardMap = createDB_HFcard(True)
#    conSlopes = createDB_fromCSV("InjectionBoardCalibration/SlopesOffsets_card1.csv", True)
    conSlopes = lite.connect("../InjectionBoardCalibration/SlopesOffsets.db")
#    con = createDB_QIE()
#    QIE_values = {}
    graphs = {}
    for ih in histo_list:
        QIE_values = []

        # Get channel,pigtial from histogram
        print ih
        cur_CardMap = conCardMap.cursor()
        query = ( ih, )
        cur_CardMap.execute('SELECT card, pigtail, channel FROM HFcard WHERE histo=?', query )
        channel_t = cur_CardMap.fetchone()
#        print channel_t
        card    = channel_t[0]
        pigtail = channel_t[1]
        channel = channel_t[2]
#        print "Card:    "+str(card)
#        print "Pigtail: "+str(pigtail)
#        print "Channel: "+str(channel)
        
        # Get calibration for channel
        cur_Slopes = conSlopes.cursor()

        for i_lsb in lsbList:
        

            query = ( pigtail, card, i_lsb, i_lsb)
            cur_Slopes.execute('SELECT offset, slope FROM CARDCAL WHERE pigtail=? AND card=? AND rangehigh>=? AND rangelow<=?', query )
            result_t = cur_Slopes.fetchone()
            print query
            print result_t
            offset = result_t[0]
            slope = result_t[1]
            print "Slope = "+str(slope) + " Offset= "+str(offset)

            current = i_lsb*slope + offset
            charge = current*25e6
            
#            print ih, values[i_lsb][ih]['link']*4 + values[i_lsb][ih]['channel']
            
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


def makeADCvsfCgraphSepCapID(lsbList, values, histo_list = range(0,96)):
    conCardMap = createDB_HFcard(True)

    conSlopes = lite.connect("../InjectionBoardCalibration/SlopesOffsets.db")

    graphs = {}
    for ih in histo_list:
        QIE_values = []

        # Get channel,pigtial from histogram
        print ih
        cur_CardMap = conCardMap.cursor()
        query = ( ih, )
        cur_CardMap.execute('SELECT card, pigtail, channel FROM HFcard WHERE histo=?', query )
        channel_t = cur_CardMap.fetchone()
#        print channel_t
        card    = channel_t[0]
        pigtail = channel_t[1]
        channel = channel_t[2]
        # print "Card:    "+str(card)
        # print "Pigtail: "+str(pigtail)
        # print "Channel: "+str(channel)
        
        # Get calibration for channel
        cur_Slopes = conSlopes.cursor()

        for i_lsb in lsbList:
        

            query = ( pigtail, card, i_lsb, i_lsb)
            cur_Slopes.execute('SELECT offset, slope FROM CARDCAL WHERE pigtail=? AND card=? AND rangehigh>=? AND rangelow<=?', query )
            result_t = cur_Slopes.fetchone()
            # print query
            # print result_t
            offset = result_t[0]
            slope = result_t[1]
            # print "Slope = "+str(slope) + " Offset= "+str(offset)

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

            ADCvsfC =  TGraphErrors(len(fc_array),adc_array , fc_array,adcerr_array,fCerror_array)
            ADCvsfC.SetNameTitle("ADCvsfC_%i_capID_%i"%(ih,i_capID),"ADCvsfC_%i_capID_%i"%(ih,i_capID))

            graphs[ih].append(ADCvsfC)

    return graphs

    
