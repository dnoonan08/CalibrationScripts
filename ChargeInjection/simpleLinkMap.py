from ngccmCommands import *
from checkLinks import *
from read_histo import *

def getSimpleLinkMap(ts, outputDirectory = ""):

	print 'Start Get Mapping'
	linkMap = {}

	print_links(ts)

        getGoodLinks(ts, forceInit=True)

 	for rbx in ts.fe_crates:
		for rm in ts.qie_slots[0]:
			print 'RBX number:', rbx, 'RM number', rm
                        for slot in range(1,5):
                                uniqueID = getUniqueID(ts, rbx, rm, slot)
                                print 'Looking at slot %i, id: %s'%(slot, uniqueID)

                                setFixRangeModeOnTop(ts, [rbx],[rm],[slot],3)
                                fName = uhtr.get_histos(ts,n_orbits=10, sepCapID=0, file_out_base = outputDirectory+"mappingHist")

                                vals = read_histo(fName,False)
                                for i in range(0,144,4):
                                        link = int(i/6)
                                        
                                        if vals[i]['mean'] > 100:
                                                linkMap[link] = {'unique_ID':uniqueID, 
                                                                 'rbx':rbx, 
                                                                 'rm':rm, 
                                                                 'slot':slot,
                                                                 'side':'Top',
                                                                 }

                                setFixRangeModeOff(ts, [rbx], [rm], [slot])

                                setFixRangeModeOnBottom(ts, [rbx],[rm],[slot],3)
                                fName = uhtr.get_histos(ts,n_orbits=10, sepCapID=0, file_out_base = outputDirectory+"mappingHist")
                                vals = read_histo(fName,False)
                                for i in range(0,144,4):
                                        link = int(i/6)
                                        
                                        if vals[i]['mean'] > 100:
                                                linkMap[link] = {'unique_ID':uniqueID, 
                                                                 'rbx':rbx, 
                                                                 'rm':rm, 
                                                                 'slot':slot,
                                                                 'side':'Bottom',
                                                                 }
                                setFixRangeModeOff(ts, [rbx], [rm], [slot])


	print 'Done with Getting Mapping'
	return linkMap
