from base_visualization import *

class Plot2D(BaseVisualization):
    def __init__(self, output_file, data=None, input_file=None, title=None, subtitle=None, min_values=None,
                 max_values=None, title_size=None, subtitle_size=None, label_size=None, ticks_size=None,
                 label_pad=None, major_grid_line_width=None, minor_grid_line_width=None, ticks_pad=None,
                 scatter_size=None, figure_size=None, input_values=None):
        """
        Initialize the Plot2D class, inheriting from BaseVisualization.

        Parameters:
        - input_file: Specifies an input file that may be used for the visualization.
        - output_file: Specifies the output file where the visualization will be saved.
        - data: Specifies the data to be visualized.
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
        - input_values: Specifies the input values used in the visualization.
        """
        super().__init__(data=data, input_file=input_file, output_file=output_file, title=title, subtitle=subtitle, min_values=min_values,
                         max_values=max_values, title_size=title_size, subtitle_size=subtitle_size, label_size=label_size,
                         ticks_size=ticks_size, label_pad=label_pad, major_grid_line_width=major_grid_line_width,
                         minor_grid_line_width=minor_grid_line_width, ticks_pad=ticks_pad, scatter_size=scatter_size,
                         figure_size=figure_size, input_values=input_values)

    def plot(self):
        """
        Plot a 2D scatter plot based on the specified parameters.
        """
        # Sets all the values necessaries for formatting the specific chart
        self.set_data()
        self.set_summary()
        self.set_min_max_values()

        # Sets the default values if needed
        self.set_default_values()

        # Set the figure size of the figure based on the min and max values
        self.input_values = self.min_values + self.max_values
        self.set_figure_size()

        # Obtains the list of ticks based on the min and max values
        xticks = self.calculate_tick_locations(
            self.min_values[0], self.max_values[0])
        yticks = self.calculate_tick_locations(
            self.min_values[1], self.max_values[1])
        
        # Creates the figure
        fig, ax = plt.subplots()

        # Set the figure size of the figure based on the min and max values
        ax.get_figure().set_size_inches(self.figure_size)

        # Plots the ticks in the 2 dimensions
        plt.xticks(xticks)
        plt.yticks(yticks)

        # Sets the locations of the ticks for both axes
        ax.xaxis.set_major_locator(ticker.MaxNLocator(len(xticks)))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(len(yticks)))

        # Turns on the minor ticks 
        ax.minorticks_on()

        # Formats the major and minor grid lines width
        ax.grid(which='major',
                linestyle='--',
                linewidth=self.major_grid_line_width,
                color='black',
                zorder=0)
        ax.grid(which='minor',
                linestyle=':',
                linewidth=self.minor_grid_line_width,
                color='gray',
                zorder=1)
        
        # Formats the tick params of both axes
        ax.tick_params(axis='y',
                       pad=self.ticks_pad,
                       labelsize=0.3)
        ax.tick_params(axis='x',
                       pad=self.ticks_pad,
                       labelsize=0.3)

        # Sets the limits of both axes
        xlims = [self.min_values[0], self.max_values[0] +
                 (self.max_values[0] * 0.01)]
        ax.set_xlim(xlims)

        ylims = [self.min_values[1], self.max_values[1] +
                 (self.max_values[1] * 0.01)]
        ax.set_ylim(ylims)

        # Formats the scatter dots
        plt.scatter(self.data[0],
                    self.data[1],
                    s=self.scatter_size,
                    alpha=1,
                    color='darkblue')

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

        # Formats the font size of the ticks
        plt.xticks(fontsize=self.ticks_size)
        plt.yticks(fontsize=self.ticks_size)

        # Sets the label and format for both axes
        plt.xlabel("$f_1$",
                   fontsize=self.label_size,
                   labelpad=self.label_pad)
        plt.ylabel("$f_2$",
                   fontsize=self.label_size,
                   labelpad=self.label_pad)

        # Saves the figure as a file
        plt.savefig(self.output_file)

        # Closes the image
        plt.close()
