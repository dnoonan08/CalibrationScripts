# import sys
# sys.path.insert(0, '../../hcal_teststand_scripts')

# from hcal_teststand.uhtr import *
# from hcal_teststand import *
# from hcal_teststand.hcal_teststand import *
# from hcal_teststand.qie import *

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
