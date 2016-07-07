DACscan_range0_5k = range(20,130,2) + range(130,550,5)
#DACscan_range1_1k = range(350,700, 10)+ range(700,1500,20) + range(1500,4300,40)
DACscan_range2_1k = range(3400,6100, 75)+range(6100,12300,150) + range(12300,35000,300)
DACscan_range3_1k = range(28000,48000,500)

# DACscan_range0_5k = [50,150,400,550]#range(20,550,50)#[60,300]
# DACscan_range1_1k = [500,1000,1500,2000,3250]
# DACscan_range2_1k = [4000,6000,8000,10000,15000]
# DACscan_range3_1k = [35000,48000]
DACscan_range1_1k = range(75,120,5)+range(125,411,5)+range(420,741,10)
DACscan_range2_1k = range(700,1201,20)+range(1250,2011,40)+range(2050,3001,60)+range(3050,6021,80)
DACscan_range3_1k = range(5500,8000,200)+range(8000,20251,300)+range(25000,35001,400)+range(38000,48000,500)
scanValues = { 0 : DACscan_range0_5k ,
               1 : DACscan_range1_1k ,
               2 : DACscan_range2_1k ,
               3 : DACscan_range3_1k ,
               }
	   
