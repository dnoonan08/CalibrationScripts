
DACscan_range0 = range(160)
DACscan_range1 = range(100,240, 5)+ range(240,500,10) + range(500,1000,20) + range(1000,1600,50)
DACscan_range2 = range(1200,2100, 75)+range(2100,4200,150) + range(4200,9000,300) + range(9000,13000,500)
DACscan_range3 = range(12000,45000,1000)

DACscan_range0To1 = range(110,150)

scans = { "0" : DACscan_range0 ,
          "1" : DACscan_range1 ,
          "2" : DACscan_range2 ,
          "3" : DACscan_range3 ,
          "0to1": DACscan_range0To1 ,
	  }

DACscan_range0_5k = range(40) + range(40,130,2) + range(130,480,5)
DACscan_range1_5k = range(350,700, 10)+ range(700,1500,20) + range(1500,4300,40)
DACscan_range2_5k = range(3400,6100, 75)+range(6100,12300,150) + range(12300,35000,300)
DACscan_range3_5k = range(28000,45000,1000)

scans5k = { "0" : DACscan_range0_5k ,
	    "1" : DACscan_range1_5k ,
	    "2" : DACscan_range2_5k ,
	    "3" : DACscan_range3_5k ,
	    }
	   
