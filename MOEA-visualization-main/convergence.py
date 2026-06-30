from base_visualization import *

class ConvergenceDiagram(BaseVisualization):
    def __init__(self,  output_file, data=None, input_file=None, dim=None, title=None, subtitle=None, min_values=None,
                 max_values=None, title_size=None, subtitle_size=None, label_size=None, ticks_size=None,
                 label_pad=None, major_grid_line_width=None, minor_grid_line_width=None, ticks_pad=None,
                 scatter_size=None, figure_size=None, line_width=None, logarithmic=False):
        """
        Initialize the ConvergenceDiagram class, inheriting from BaseVisualization.
        
        Parameters:
        - data: Panda frame with the values.
        - x_values : Values of x values.
        - y_values : Values of y values.
        - output_file: Specifies the output file where the visualization will be saved.
        - input_file: Specifies an input file that may be used for the visualization.
        - data: Specifies the data to be visualized.
        - dim: Number of columns in the array
        - title: Specifies the title of the visualization.
        - subtitle: Specifies the subtitle of the visualization.
        - min_values: Specifies the minimum values used in the visualization.
        - max_values: Specifies the maximum values used in the visualization.
        - title_size: Specifies the font size of the title.
        - subtitle_size: Specifies the font size of the subtitle.
        - label_size: Specifies the font size of the labels.
        - ticks_size: Specifies the size of the ticks in the visualization.
        - label_pad: Specifies the padding between labels and the visualization.
        - major_grid_line_width: Specifies the line width of major grid lines.
        - minor_grid_line_width: Specifies the line width of minor grid lines.
        - ticks_pad: Specifies the padding between ticks and the visualization.
        - scatter_size: Specifies the size of scatter plot markers.
        - figure_size: Specifies the size of the figure or plot.
        """

        super().__init__(output_file=output_file, data=data, title=title, dim=dim, input_file=input_file, subtitle=subtitle, min_values=min_values, max_values=max_values,
                         title_size=title_size, subtitle_size=subtitle_size, label_size=label_size, ticks_size=ticks_size,
                         label_pad=label_pad, major_grid_line_width=major_grid_line_width,
                         minor_grid_line_width=minor_grid_line_width, ticks_pad=ticks_pad,
                         scatter_size=scatter_size, figure_size=figure_size)
        self.line_width = line_width
        self.logarithmic = logarithmic
        self.x_values = None
        self.y_values = None

    def set_values(self):
        """
        Set default values for visualization attributes if not provided.
        """

        if self.min_values is None:
            self.min_values = [min(self.x_values), min(self.data[0])]

        if self.max_values is None:
            self.max_values = [max(self.x_values), max(self.data[0])]

        if self.line_width is None:
            self.line_width = self.font_size * 0.10

    def set_x_values(self):
        """
        Set default values for the x axis. If provided within the pandas frame, 
        it sets the second column. If not provided, the x values will be the size of the 
        only column in the data frame.
        """
        if self.dim > 1:
            self.x_values = self.data[1]
        else:
            size = self.data.shape[0]
            self.x_values = list(range(1, size+1))

    def set_line_width(self, value):
        """
        Set the line width for the visualization.
        
        Parameters:
        - value: The value of the line width to be set.
        """
        self.line_width = value

    def get_line_width(self):
        """
        Get the line width attribute.
        """
        return self.line_width

    def plot(self):
        """
        Plot a convergence diagram based on the specified parameters.
        """
        
        # Sets the default values necessary for formatting 
        self.set_data()
        self.set_summary()
        self.set_dim()
        self.set_x_values()
        self.set_values()
        self.set_default_values()
        self.input_values = self.min_values + self.max_values
        self.set_figure_size()

        # Obtains the list of ticks based on the min and max values
        xticks = self.calculate_tick_locations(
            self.min_values[0], self.max_values[0])

        yticks = self.calculate_tick_locations(
            self.min_values[1], self.max_values[1])

        fig, ax = plt.subplots()
        
        # Sets the size of the figure
        ax.get_figure().set_size_inches(self.figure_size)
        
        # Sets the padding and size for the ticks in both axes
        ax.tick_params(axis='both', which='major',
                       labelsize=self.ticks_size, pad=self.ticks_pad)

        # Plots the ticks in the 2 dimensions
        plt.xticks(xticks)
        plt.yticks(yticks)

        # Sets the format for the title
        plt.suptitle(self.title,
                     fontsize=self.title_size,
                     fontweight='bold',
                     family='monospace',
                     y=0.97)

        # Adds the formatted subtitle if needed
        if self.subtitle:
            ax.text(x=0.48,
                    y=1.03,
                    s=self.subtitle,
                    transform=ax.transAxes,
                    ha="center",
                    fontsize=self.subtitle_size,
                    style='italic')

        # Sets the label for the axes
        plt.xlabel("$t$", fontsize=self.label_size, labelpad=self.label_pad)
        plt.ylabel("$Value$", fontsize=self.label_size,
                   labelpad=self.label_pad)
        
        # Sets the font size of the ticks 
        plt.xticks(fontsize=self.ticks_size)
        plt.yticks(fontsize=self.ticks_size)

        # Sets the sytle and width of the major grid line
        plt.grid(linestyle='--', linewidth=self.major_grid_line_width)

        # Sets the logarithmic visualization if indicated
        if self.logarithmic:
            plt.yscale('log')

        # Plots the chart, sets the color and adds the marker
        plt.plot(self.x_values, self.data[0],
                 color='darkred', linewidth=self.line_width, marker='.', markersize=150)
        
        # To manage large sizes of files
        plt.rcParams['agg.path.chunksize'] = 1000
        plt.rcParams['path.simplify_threshold'] = 1.0

        # Saves the image on a file
        plt.savefig(self.output_file)
        
        # Closes the image
        plt.close()
