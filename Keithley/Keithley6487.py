import time
import numpy
import visa

class Keithley:
    ''' Class to control a Keithley picoammeter '''

    def __init__(self,resource='GPIB0::23::INSTR'):
        self.resource = resource
        self.rm = visa.ResourceManager()
        
        self.keithley = self.rm.open_resource(self.resource)
        #except:
        #    print "ERROR. GPIB device not found or wrong resource name. Check connection or resource name. The following are the resources found:"
        #    print( self.rm.list_resources() )

        self.number_of_readings = 20
        self.time_delay = 10
        self.mean = 0.
        self.std = 0.
        self.min = 0.
        self.max = 0.

    def print_instrument(self):
        ''' Print instrument name '''
        #rm = visa.ResourceManager()
        print "List of Resources:"
        print( self.rm.list_resources() )
        #keithley = rm.open_resource(self.resource)        
        print "Instrument:"
        print( self.keithley.query('*IDN?'))

    def read(self, verbose=True):
        ''' Read data from instrument '''
        #number_of_readings = 20

        # restoring facatory defaults: *rst
        # to recall saved setup: *rcl
        # how about voltage offset corrections?

        self.keithley.write('*RST')          # restore GPIB defaults
        self.keithley.write('SYST:ZCH ON')   # enable zero check
        self.keithley.write('RANG 2e-9')     # select the 2nA range
        self.keithley.write('DAMP ON')       # enable damping to reduce noise from high capacitance

        self.keithley.write('INIT ')         # Trigger reading to be used as zero correction.
        time.sleep(3)
        self.keithley.write('SYST:ZCOR:ACQ') # Use last reading taken as zero correct value.
        self.keithley.write('SYST:ZCOR ON')  # Perform zero correction.
        self.keithley.write('RANG:AUTO ON')  # Enable auto range.
        
        self.keithley.write('SYST:ZCH OFF')  # Disable zero check.
        self.keithley.write('*CLS') # Clear status model.

        #store readings
        #self.keithley.write('FORM:ELEM READ, UNIT') # 
        self.keithley.write('FORM:ELEM READ')
        #self.keithley.write('TRIG:DEL 2')
        self.keithley.write('TRIG:COUN %d' % self.number_of_readings) # Set trigger model to take to 10 readings.
        self.keithley.write('TRAC:POIN %d' % self.number_of_readings) # Set buffer size to 10.
        self.keithley.write('TRAC:CLE ') # Clear buffer.
        self.keithley.write('TRAC:FEED SENS ') # Store raw input readings.
        self.keithley.write('TRAC:FEED:CONT NEXT ') # Start storing readings.

        self.keithley.write('INIT') # trigger readings
        time.sleep(self.time_delay)

        currents_raw = self.keithley.query('TRAC:DATA?') # Request all stored readings.
        currents_raw = currents_raw.split(',')

        currents = []
        for i in currents_raw:
    
            currents.append(float(i.encode('ascii','ignore')))
        
        self.mean = numpy.mean(currents)
        self.std = numpy.std(currents)
        self.min = min(currents)
        self.max = max(currents)
        self.currents = currents
        if verbose:
            print 'Mean: {}'.format(self.mean) 
            print 'STD : {}'.format(self.std)
            print 'Min : {}'.format(self.min)
            print 'Max : {}'.format(self.max)


