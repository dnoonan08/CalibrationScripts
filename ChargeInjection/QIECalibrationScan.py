from time import sleep
from datetime import date
import os
from optparse import OptionParser
import subprocess
import sys

from scans import *
from adcTofC import *
from fitGraphs import *
from ROOT import *

sys.path.insert(0, '../../hcal_teststand_scripts')

from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *

import sqlite3 as lite


def setDAC( dacLSB = 0, dacChannel = -1):
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib; ~/../tiroy/mcc-libhid/dacQinjector  -o {0} -c {1}".format(dacLSB, dacChannel) )


def initLinks(ts):
	cmds = [
		'0',
		'link',
		'init',
		'1',
		'92',
		'0',
		'0',
		'0',
		'quit',
		'exit',
		'-1'
		]
	output = uhtr.send_commands_script(ts, ts.uhtr_slots[0], cmds)
#	print output['output']
	sleep(2)
#	for line in output['output']:
#		print line
#		print line['cmd'], line['result']


def read_histo(file_in="", sepCapID=True, qierange = 0):
	result = []
	tf = TFile(file_in, "READ")
	tc = TCanvas("tc", "tc", 500, 500)
	if sepCapID:
		for i_link in range(24):
			for i_ch in range(4):
				th = tf.Get("h{0}".format(4*i_link + i_ch))
				th.SetBinContent(1,0)
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = []
				info["rms"] = []
				for i_capID in range(4):
					offset = 64*(i_capID)
					th.GetXaxis().SetRangeUser(offset, offset+63)
					info["mean"].append(th.GetMean()-offset)
					info["rms"].append(th.GetRMS())
				result.append(info)
		
	else:
		for i_link in range(24):
			for i_ch in range(4):
				th = tf.Get("h{0}".format(4*i_link + i_ch))
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = th.GetMean()
				info["rms"] = th.GetRMS()
				result.append(info)
	return result
		
																																						


def doScan(ts, injCardNumber = 1, dacNumber = 1, scanRange = range(30), qieRange=0, useFixRange=True, useCalibrationMode=True, saveHistograms = True, sepCapID = True, SkipScan = False):

	print 'SepCap', sepCapID

	if saveHistograms and not SkipScan:
		outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode/{3}/".format(injCardNumber, dacNumber, qieRange, str(date.today() ) )
		if not os.path.exists(outputDirectory):
			os.system( "mkdir -pv "+outputDirectory )

	if SkipScan:
		outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode/".format( injCardNumber, dacNumber, qieRange )
		dirs = os.listdir(outputDirectory)
		dirs.sort()
		outputDirectory += dirs[-1]+'/'
		print outputDirectory

	if useFixRange:
		set_fix_range_all(ts, 1, 2, True, int(qieRange))
	if useCalibrationMode:
		set_cal_mode_all(ts, 1, 2, True)

	if not SkipScan:
		initLinks(ts)

	results = {}
	for i in scanRange:

		histName = ""
		if saveHistograms: histName = "Calibration_LSB_{0}.root".format( i )
		if not SkipScan:
			print 'LSB', i
			setDAC(i)
			sleep(5)
			if sepCapID:
				fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=1, file_out=outputDirectory+histName)
			else:
				fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=0, file_out=outputDirectory+histName)
		else:
			fName = outputDirectory+histName
		vals = read_histo(fName,sepCapID,int(qieRange))
		results[i] = vals
		
	if not SkipScan:
		setDAC(0)
		set_fix_range_all(ts, 1, 2, False, int(qieRange))
		set_cal_mode_all(ts, 1, 2, False)
	
	return results


def main(options):
	ts = teststand("904")

	qieParams = lite.connect("qieParameters.db")
	cursor = qieParams.cursor()

	cursor.execute("create table if not exists qieparams(id STRING, qie INT, capID INT, range INT, slope REAL, offset REAL)")
		

	sepCapID = options.sepCapID
	print sepCapID

	if not options.SkipScan:
		print ts.fe_crates
		print ts.qie_slots
		uniqueID = {}
		for i_crate in ts.fe_crates:
			uniqueID[i_crate] = {}
			for i_slot in ts.qie_slots[0]:
				uniqueID[i_crate][i_slot] = get_unique_id(ts, i_crate, i_slot)
				print i_crate, i_slot, get_unique_id(ts, i_crate, i_slot)

#### Find which injection board is hooked up to which range of QIE's

	qieCardID = ['0x8d000000', '0xaa24da70']

	for qieRange in range(3):
	
		scanRange = scans[qieRange]

		print scanRange


		results = doScan(ts, options.cardnumber, options.dacnumber, scanRange, options.range, options.useFixRange, options.useCalibrationMode, options.saveHistograms,sepCapID=sepCapID, SkipScan=options.SkipScan)

		histoList = range(96)


		print qieCardID
		qieID = "%s %s" %(qieCardID[0], qieCardID[1])

	        #Will need to find a way of updating the mapping between injection boards and qie boards

		if sepCapID:
			graphs = makeADCvsfCgraphSepCapID(scanRange,results, histoList)

			for ih in histoList:
				for i_capID in range(4):
					graph = graphs[ih][i_capID]
					print ih, i_capID
					print graph
					qieNum = ih%24 + 1
					params = doFit(graph,int(options.range), True, qieNum, qieID.replace(' ', '_'),i_capID)
					
					values = (qieID, qieNum, i_capID, options.range, params[0], params[1])
					
					cursor.execute("insert or replace into qieparams values (?, ?, ?, ?, ?, ?)",values)
				
		else:
			capID = -1
			graphs = makeADCvsfCgraph(scanRange,results, histoList, sepCapID)

			for ih in histoList:
				graph = graphs[ih]
				print ih
				qieNum = ih%24 + 1
				
				params = doFit(graph,int(options.range), True, qieNum, qieID.replace(' ', '_'))
				
				cursor.execute("remove from qieparams where qieID=? and qieNum=? and i_capID=? and range=?",(qieID, qieNum, i_capID, options.range))
				
				values = (qieID, qieNum, i_capID, options.range, params[0], params[1])
				
				cursor.execute("insert into qieparams values (?, ?, ?, ?, ?, ?)",values)

	cursor.close()
	qieParams.commit()
	qieParams.close()

		
if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--dac", dest="dacnumber", default="2" ,
			  help="DAC used" )
	parser.add_option("--nofixed", action="store_false", dest="useFixRange", default=True ,
			  help="do not use fixed range mode")
	parser.add_option("--nocalmode", action="store_false", dest="useCalibrationMode", default=True ,
			  help="do not use calibration mode" )
	parser.add_option("--NoSepCapID", action="store_false",dest="sepCapID",default=True,
			  help="don't separate the different capID histograms")
	parser.add_option("--SkipScan", action="store_true",dest="SkipScan",default=False,
			  help="Skip the scan, using presaved scan")

	(options, args) = parser.parse_args()
	
	main(options)
