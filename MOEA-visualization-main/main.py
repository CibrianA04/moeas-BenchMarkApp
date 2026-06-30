import numpy as np
import pandas as pd
from plot2D import Plot2D
from plot3D import Plot3D
from parallel_coord import ParallelCoordinates
from radar import RadarChart
from heatmap import HeatMap
from bubble import BubbleChart

dicc = {2: 36, 3: 36, 4: 84, 5: 85, 6: 147, 7: 168, 8: 156, 9: 174, 10: 230}
sf = np.arange(0.1, 1, 0.1)
types = ["SLD", "INV_SLD"]
types2 = ["IMOP", "DTLZ"]
labels_geom = {"SLD": "Linear", "INV_SLD": "Inverted Linear"}
 
# Loop that uses the example data from the 'data' folder 
num = 0
for method in types:
    for dim in dicc:
        N = dicc[dim]
        for factor in sf:
            # Sets the input file and output file for each file
            input_file = "data/%s_%.2dD_%d_sf_%.3f.pof" % (
                method, dim, N, factor)
            output_file = "fronts_all/%s_%.2dD_%d_sf_%.3f" % (
                method, dim, N, factor)
            # Title that uses 
            title = "%s %.2dD" % (method, dim)
            subtitle = "Scaling = %.1f" % (factor)
            if dim == 3 :
                pl = Plot3D(input_file, output_file + "_plot3D.png", title, subtitle=subtitle)
                pl.plot()

            if dim == 2 :
                pl = Plot2D(input_file, output_file + "_plot2D.png", title)
                pl.plot()
            
            if dim != 2 and dim != 3:
                ppl = ParallelCoordinates(input_file, output_file + "_parallel.png")
                ppl.plot()
                bchart = BubbleChart(input_file, output_file + "_bubble.png")
                bchart.plot()
                radar = RadarChart(input_file, output_file + "_radar.png")
                radar.plot()
                heat = HeatMap(input_file, output_file + "_heat.png")
                heat.plot() 


lst = [ "DTLZ7", "WFG3", "WFG2","DTLZ1",  "WFG1", "LINEAR",
         "DTLZ5", "DTLZ7", "DTLZ2"]

for ty in lst:
    for i in range(3,11):
        dim = i
        if i < 10:
            i = "0" + str(i)        
        input_file = "data/%s_%sD.pof" % (ty, i)
        output_file = "fronts_all/%s_%sD_fig" % (ty, i)
        ppl = ParallelCoordinates(input_file, output_file + "_parallel.png")
        ppl.plot()
        bchart = BubbleChart(input_file, output_file + "_bubble.png")
        bchart.plot()
        radar = RadarChart(input_file, output_file + "_radar.png")
        radar.plot()
        heat = HeatMap(input_file, output_file + "_heat.png")
        heat.plot()
  