from base_visualization import *

class ParallelCoordinates(BaseVisualization):
    def __init__(self, output_file, data=None, input_file=None, title=None, subtitle=None, min_value=None,
                 max_value=None, title_size=None, subtitle_size=None, label_size=None, ticks_size=None,
                 label_pad=None, major_grid_line_width=None, minor_grid_line_width=None, ticks_pad=None,
                 scatter_size=None, figure_size=None, line_width=None, input_values=None):
        """
        Initialize the ParallelCoordinates class, a subclass of BaseVisualization.
        
        Parameters:
        - input_file: Specifies an input file that may be used for the visualization.
        - output_file: Specifies the output file where the visualization will be saved.
        - data: Specifies the data to be visualized.
        - title: Specifies the title of the visualization.
        - subtitle: Specifies the subtitle of the visualization.
        - min_value: Specifies the minimum value used in the visualization.
        - max_value: Specifies the maximum value used in the visualization.
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
        - line_width: Specifies the line width of the parallel coordinates lines.
        - input_values: Specifies the input values used in the visualization.
        """
        super().__init__(data=data, input_file=input_file, output_file=output_file, title=title, subtitle=subtitle,
                         title_size=title_size, subtitle_size=subtitle_size, label_size=label_size,
                         ticks_size=ticks_size, label_pad=label_pad, major_grid_line_width=major_grid_line_width,
                         minor_grid_line_width=minor_grid_line_width, ticks_pad=ticks_pad, scatter_size=scatter_size,
                         figure_size=figure_size, input_values=input_values)

        self.min_value = min_value
        self.max_value = max_value
        self.line_width = line_width

    def set_values(self):
        """
        Set default values for the visualization parameters if they are not provided.
        """
        if self.min_value is None:
            self.min_value = min(self.min_values)

        if self.max_value is None:
            self.max_value = max(self.max_values)

        if self.line_width is None:
            self.line_width = self.font_size*0.02

    def set_min_value(self, value):
        """
        Set the minimum value attribute.

        Parameters:
        - value: The value to be set as the minimum value.
        """
        self.min_value = value

    def get_min_value(self):
        """
        Get the minimum value attribute.
        """
        return self.min_value

    def set_max_value(self, value):
        """
        Set the maximum value attribute.

        Parameters:
        - value: The value to be set as the maximum value.
        """
        self.max_value = value

    def get_max_value(self):
        """
        Get the maximum value attribute.
        """
        return self.max_value

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
        Plot a parallel coordinates plot based on the specified parameters.
        """
        # Sets all the values necessaries for formatting the specific chart
        self.set_data()
        self.set_summary()
        self.set_min_max_values()
        self.set_dim()
        self.set_values()

        # Sets the subtitle size and label padding for this specific chart
        if self.subtitle_size is None:
            self.set_subtitle_size(self.font_size + 10)
        if self.label_pad is None:
            self.set_label_pad(self.font_size * 0.00003)

        # Sets the default values if needed
        self.set_default_values()

        # Set the figure size of the figure based on the min and max values
        self.input_values = [self.min_value, self.max_value]
        self.set_figure_size()

        # Creates the figure for the subplot and the number of columns
        fig, axes = plt.subplots(1, self.dim - 1, sharey=False)

        #If the dimension is one, it turns the axes into a list of axes
        if self.dim > 2:
            fig, axes = plt.subplots(1, self.dim - 1, sharey=False)
        else:
            fig, axes = plt.subplots(1, 1, sharey=False)
            axes = [axes]
            
        # Sets the figure size
        plt.rcParams["figure.figsize"] = [13, 9]

        # Creates a the list of ticks for the x axis
        x = np.arange(1, self.dim + 1)

        # Calculates the ticks locations for the axes
        ranges = self.calculate_tick_locations(self.min_value, self.max_value)

        # Set the figure size of the figure based on the min and max values
        axes[0].get_figure().set_size_inches(self.figure_size)

        # Configures the major tick locations for the x-axis of several plot axes based on the values in the x list.
        for axx, xx in zip(axes, x[:-1]):
            axx.xaxis.set_major_locator(ticker.FixedLocator([xx]))
        axes[self.dim -
             2].xaxis.set_major_locator(ticker.FixedLocator([x[-2], x[-1]]))

        
        for i in range(self.dim - 1):
            lims = [self.min_value, self.max_value]

            # Sets the y limits to the global min and max values and the ticks to the calculates ranges
            axes[i].set_ylim(lims)
            axes[i].set_yticks(ranges)

            # Formats the ticks of both axes 
            axes[i].tick_params(
                axis='x', labelsize=self.label_size, pad=self.ticks_pad)
            axes[i].tick_params(
                axis='y', labelsize=self.label_size, pad=self.ticks_pad)
            
            # Adds the major and minor grid line width
            axes[i].minorticks_on()
            axes[i].grid(which='major',
                         linewidth=self.major_grid_line_width,
                         color='black',
                         zorder=0)
            axes[i].grid(which='minor',
                         linewidth=self.minor_grid_line_width,
                         color='black',
                         zorder=0)

            # Removes the left label of each axes except the last one
            if i != 0:
                axes[i].tick_params(labelleft=False)

            # for each row in the data, plots the value and formats the x limits and x ticks
            for row in range(self.data.shape[0]):
                axes[i].plot(x, self.data.iloc[row], color='darkblue',
                             linewidth=self.line_width)
                axes[i].set_xlim([x[i], x[i+1]])
                axes[i].set_xticks(np.arange(x[i], x[i] + 2, 1))

        # Adds the second tick and label for each axis 
        for tick in axes[self.dim - 2].yaxis.get_major_ticks():
            tick.label2On = True
            tick.label2.set_visible(True)

        # Adjust the line width of the right spine of the graph
        axes[self.dim - 2].spines['right'].set_linewidth(self.line_width)

        # Adjust the space of the subplot
        plt.subplots_adjust(wspace=0)

        # Sets the format for the title
        plt.suptitle(self.title,
                     fontsize=self.title_size,
                     fontweight='bold',
                     family='monospace',
                     y=0.97)

        # Adds the formatted subtitle if needed
        if self.subtitle:
            suptitle_pos = fig._suptitle.get_position()
            fig.text(0.5, suptitle_pos[1] - 0.07, self.subtitle,
                     ha='center', fontsize=self.subtitle_size, style='italic')

        # Obtains the labels and ticks of the axis
        ylbl = axes[0].yaxis.get_label()
        left_ticks_pos = ylbl.get_position()
        xlbl = axes[0].xaxis.get_label()
        bottom_ticks_pos = xlbl.get_position()

        # Adjusts the superior x label based on the ticks 
        fig.supxlabel("Objectives", fontsize=self.label_size,
                      x=bottom_ticks_pos[0], y=bottom_ticks_pos[1] + self.label_pad)

        # Adjusts the superior y label based on the ticks
        fig.supylabel("Objective values", fontsize=self.label_size,
                      x=left_ticks_pos[0] + self.label_pad, y=left_ticks_pos[1])
        
        # Saves the figure as a file
        plt.savefig(self.output_file)

        # Closes the image
        plt.close()
