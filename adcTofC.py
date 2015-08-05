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

def main( argv ):
    print "hello"
    print argv

    # Create DBs in memory
    conCardMap = createDB_HFcard(True)
#    conSlopes = createDB_fromCSV("InjectionBoardCalibration/SlopesOffsets_card1.csv", True)
    conSlopes = lite.connect("InjectionBoardCalibration/SlopesOffsets.db")
    con = createDB_QIE()

    # array
    con.row_factory = lite.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM QIE10")
    rows = cur.fetchall()
    x_axis_R = {}
    x_axis_all = []

    for irange in range(0,4):
        x_axis_R[irange] = []
        for irow in range(0,4):
            row = rows[irow]
        
            if irow == 0: x_axis_R[irange].append ( row["low_input_charge"] )
            for iadc in range( 1, row["high_ADC"] - row["low_ADC"] +2):
                x_axis_R[irange].append ( row["low_input_charge"] + row["sensitivity"]*iadc )


    roo_outfile = TFile( "new.root", "RECREATE")


    histo_list = [20, 21, 22 ]
    QIE_ADC_list = {}
    QIE_LSB_list = {}
    QIE_fC_list = {}
    for ih in histo_list:
        QIE_ADC_list[ih] = []
        QIE_LSB_list[ih] = []
        QIE_fC_list[ih] = []

    print 
    for fileName in argv:
        # Get LSB from filename
        print fileName
        aLSB = fileName.strip('.root').split('_')[2]
        aLSB = int(aLSB)
        print "LSB: " + str(aLSB)
    
        # Open root file
        roo_infile = TFile( fileName ) 
        
        histo_map = {}
    
        for ih in histo_list:
    
            histo_name = "h"+str(ih)
            horg = roo_infile.Get(histo_name)
            histo_map[histo_name] = horg
            x_maximum = horg.GetXaxis().GetBinCenter(horg.GetMaximumBin())
            print "Got histogram with name: " + horg.GetName() +", mean: "+str(horg.GetMean())+", rms: "+str(horg.GetRMS())+", Maximum@: "+str(x_maximum)+"\n"
    
            # Get channel,pigtial from histogram
            cur_CardMap = conCardMap.cursor()
            query = ( ih, )
            cur_CardMap.execute('SELECT pigtail, channel FROM HFcard WHERE histo=?', query )
            channel_t = cur_CardMap.fetchone()
            pigtail = channel_t[0]
            channel = channel_t[1]
            print "Pigtail: "+str(pigtail)
            print "Channel: "+str(channel)
    
            # Get calibration for channel
            cur_Slopes = conSlopes.cursor()
            query = ( pigtail, aLSB, aLSB)
            cur_Slopes.execute('SELECT offset, slope FROM CARDCAL WHERE pigtail=? AND rangehigh>=? AND rangelow<=?', query )
            result_t = cur_Slopes.fetchone()
            print result_t
            offset = result_t[0]
            slope = result_t[1]
            print "Slope = "+str(slope) + " Offset= "+str(offset)
    
            current = aLSB*slope+offset
            charge = current * -25e6
            print "Charge =",charge,"fC"
    
            QIE_ADC_list[ih].append(x_maximum)
            QIE_LSB_list[ih].append(aLSB)
            QIE_fC_list[ih].append(charge)
    
    # new histogram
    roo_outfile.cd()
    for ih in histo_list:
        lsb_array = array('d',QIE_LSB_list[ih])
        adc_array = array('d',QIE_ADC_list[ih])
        fc_array = array('d',QIE_fC_list[ih])

        print lsb_array
        print adc_array
        print fc_array
        # LSBvsADC = TGraph('fCvsADC_'+str(ih),len(lsb_array),lsb_array,adc_array)
        # fCvsADC = TGraph('fCvsADC_'+str(ih),len(fC_array),fC_array,adc_array)

        LSBvsADC = TGraph(len(lsb_array),lsb_array,adc_array)
        fCvsADC =  TGraph(len(fc_array),fc_array,adc_array)
        LSBvsADC.SetNameTitle("LSBvsADC_"+str(ih),"LSBvsADC_"+str(ih))
        fCvsADC.SetNameTitle("fCvsADC_"+str(ih),"fCvsADC_"+str(ih))

        LSBvsADC.Write()
        fCvsADC.Write()
    print "done"

if __name__ == '__main__':
    main( sys.argv[1:] )
    
