minval_range = [0,
                175.5,
                1579.5,
                12811.5]

minMult_range = [0,3,6,9]

def linADC(adc, adc_rms = 0):
    if adc > 255: adc = 255
    irange = int(adc) >> 6

    minval = minval_range[irange]
    mult = minMult_range[irange]

    offset=64*irange

    x = adc-offset

    if x < 15.5:        
        lin_ADC     = minval + (x)*2**(mult)
        lin_ADC_rms = adc_rms*2**(mult)
    elif x < 35.5:
        lin_ADC     = minval + 15.5*2**(mult) + (x-15.5)*2**(mult+1)            
        lin_ADC_rms = adc_rms*2**(mult+1)
    elif x < 56.5:
        lin_ADC     = minval + 15.5*2**(mult) + (20)*2**(mult+1)+(x-35.5)*2**(mult+2)
        lin_ADC_rms = adc_rms*2**(mult+2)
    else:
        lin_ADC     = minval + 15.5*2**(mult) + (20)*2**(mult+1)+(21)*2**(mult+2)+(x-56.5)*2**(mult+3)
        lin_ADC_rms = adc_rms*2**(mult+3)
        

    return lin_ADC, lin_ADC_rms





def delinADC(linADC):
    if type(linADC)==type(tuple()): linADC = linADC[0]

    if linADC<172: _range = 0
    elif linADC < 1548: _range = 1
    elif linADC < 12556: _range = 2
    else: _range = 3

    subrangeMax = [[-0.5,15.5,55.5,139.5, 172],
                   [171.5,299.5,619.5,1291.5, 1548],
                   [1548-0.5,2571.5,5131.5,10507.5,12556],
                   [12556-0.5,20747.5,41227.5,84235.5,110859.5],
                   ]

#     subrangeMax = [[0,16,56,140, 172],
#                    [172,300,620,1292, 1548],
#                    [1548,2572,5132,10508,12556],
#                    [12556,20748,41228,84236,112908],
#                    ]

    binMult = [[1,2,4,8],
               [8,16,32,64],
               [64,128,256,512],
               [512,1024,2048,4096],
               ]

    start = [[-0.5, 15.5, 35.5, 56.5],
             [-0.5, 15.5, 35.5, 56.5],
             [-0.5, 15.5, 35.5, 56.5],
             [-0.5, 15.5, 35.5, 56.5],
             ]

    for i in range(1,5):
        _max = subrangeMax[_range][i]
        if linADC>_max:
            continue
        else:
            adc = start[_range][i-1]+_range*64
            binStart = subrangeMax[_range][i-1]+binMult[_range][i-1]
            while binStart < linADC:
                adc += 1
                binStart += binMult[_range][i-1]
            adc += 1-(binStart-linADC)*1./binMult[_range][i-1]
            return adc    
