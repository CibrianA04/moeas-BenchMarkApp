from animation import Animation

file_list = ['data/SLD_02D_36.pof',
             'data/SLD_05D_85.pof']

param = {
    'major_grid_line_width': 10
}

ab = Animation()
ab.plot_to_animate(file_list, param, 'parallel')
ab.animate(output_file="fronts_all/animation1.gif")

