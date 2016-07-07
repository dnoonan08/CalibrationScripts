from ngccmEmulatorCommands import *
from checkLinks_Old import *
from read_histo import *
from time import sleep
import sys

def getSimpleLinkMap(ts, orbitDelay=28, outputDirectory = "", slotDict = {}):

	print 'Start Get Mapping'
	linkMap = {}

#	print_links(ts)

        getGoodLinks(ts, orbitDelay=orbitDelay, forceInit=True)


	
	setFixRangeModeOff(ts, slotDict)
	sleep(2)

 	for rbx in slotDict:
		print 'RBX number:', rbx
		for slot in slotDict[rbx]:
			uniqueID = getUniqueID(ts, rbx, slot)
			print 'Looking at slot %i, id: %s'%(slot, uniqueID)
			setFixRangeModeOff(ts, {rbx:[slot]})
			sleep(2)
			setFixRangeModeOnBottom(ts, {rbx:[slot]}, 3)
			sleep(2)
#			printDaisyChain(slot)
			fName = uhtr.get_histos(ts,n_orbits=10, sepCapID=0, file_out_base = outputDirectory+"mappingHist")
			vals = read_histo(fName,False)
			for i in range(0,144,6):
				link = int(i/6)
				#print link, vals[i]
				if vals[i]['mean'] > 100:
					print "Bottom: Link %i"%link
					linkMap[link] = {'unique_ID':uniqueID, 
							 'rbx':rbx, 
							 'slot':slot,
							 'side':'Bottom',
							 }

			setFixRangeModeOff(ts, {rbx:[slot]})
			sleep(2)
				
			setFixRangeModeOnTop(ts, {rbx:[slot]}, 3)
			sleep(2)
			#printDaisyChain(slot)
			fName = uhtr.get_histos(ts,n_orbits=10, sepCapID=0, file_out_base = outputDirectory+"mappingHist")
			vals = read_histo(fName,False)
			for i in range(0,144,6):
				link = int(i/6)
				#print link, vals[i]                                        
				if vals[i]['mean'] > 100:
					print "Top: Link %i"%link
					linkMap[link] = {'unique_ID':uniqueID, 
							 'rbx':rbx, 
							 'slot':slot,
							 'side':'Top',
							 }
			setFixRangeModeOff(ts, slotDict)
			sleep(2)
	print 'Done with Getting Mapping'
	return linkMap
