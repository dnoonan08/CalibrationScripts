from Keithley6487 import Keithley
import sys

t = Keithley()
#t.print_instrument()

t.read(False)

t.time_delay=10

if len(sys.argv)> 1:

    line= sys.argv[1]+', '+str(t.mean)+', '+str(t.std)+', '+str(t.min)+', '+str(t.max)
#    line2 = str(t.currents)
else:
    line = str(t.mean)+', '+str(t.std)+', '+str(t.min)+', '+str(t.max)
#    line2 = str(t.currents)

print line
