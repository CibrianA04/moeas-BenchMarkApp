from base_visualization import *

class RadarChart(BaseVisualization):
    def __init__(self, output_file, data=None, input_file=None, title=None, subtitle=None, min_value=None,
                 max_value=None, title_size=None, subtitle_size=None, label_size=None, ticks_size=None,
                 label_pad=None, major_grid_line_width=None, minor_grid_line_width=None, ticks_pad=None,
                 scatter_size=None, figure_size=None, minor=False, line_width=None, input_values=None):
        """
        Initialize the RadarChart class, inheriting from BaseVisualization.
        
        Parameters:
        - input_file: Specifies the input file that may be used for the visualization.
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
        - minor: Specifies whether to use minor grid lines.
        - line_width: Specifies the line width of the radar chart.
        - input_values: Specifies the input values used in the visualization.
        """
        super().__init__(data=data, input_file=input_file, output_file=output_file, title=title, subtitle=subtitle,
                         title_size=title_size, subtitle_size=subtitle_size, label_size=label_size,
                         ticks_size=ticks_size, label_pad=label_pad, major_grid_line_width=major_grid_line_width,
                         minor_grid_line_width=minor_grid_line_width, ticks_pad=ticks_pad, scatter_size=scatter_size,
                         figure_size=figure_size, input_values=input_values)

        self.minor = minor
        self.line_width = line_width
        self.min_value = min_value
        self.max_value = max_value

    def set_values(self):
        """
        Set default values for visualization attributes if not provided.
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
        Plot a radar chart based on the specified parameters.
        """
        # Sets all the values necessaries for formatting the specific chart
        self.set_data()
        self.set_summary()
        self.set_min_max_values()
        self.set_dim()
        self.set_values()

        # Sets the subtitle size, label padding and ticks size for this specific chart
        if self.subtitle_size is None:
            self.set_subtitle_size(self.font_size + 10)
        if self.label_pad is None:
            self.set_label_pad(self.font_size)
        if self.ticks_size is None:
            self.set_ticks_size(self.font_size * 0.75)
        
        # Sets the default values if needed
        self.set_default_values()

        # Set the figure size of the figure based on the min and max values
        self.input_values = [self.min_value, self.max_value]
        self.set_figure_size()

        # Obtains the list of ticks based on the min and max values
        ranges = self.calculate_tick_locations(self.min_value, self.max_value)

        # Formats the angles for each objective
        angles = np.linspace(0, 2 * np.pi, self.dim, endpoint=False).tolist()

        # Adds the last angle at the end to close the circle
        angles += [angles[0]]

        # Creates the figure
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={
            'polar': True})

        # For each row in the data it creates a line and adjusts the figure size
        for i in range(len(self.data)):
            values = self.data.iloc[i].values.tolist()
            line_values = values + [values[0]]
            ax.plot(angles, line_values, color='darkred',
                    linewidth=self.line_width)
            ax.get_figure().set_size_inches(self.figure_size)

        # Sets the color and width of the major grid line
        ax.grid(which='major',
                linewidth=self.major_grid_line_width,
                color='gray',
                zorder=0)

        # If indicated, it turns on the minor grid line and formats it
        if self.minor:
            ax.minorticks_on()
            ax.grid(which='minor',
                    linestyle='--',
                    linewidth=self.major_grid_line_width,
                    color='gray',
                    zorder=0)

        # Sets the limits and the ticks for the x axis
        xlabels = [f'$f_{i+1}$' for i in range(self.dim)]
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(xlabels, fontsize=self.label_size)
        ax.tick_params(axis='x', pad=self.label_pad)

        # Sets the limits for the y axis
        lims = [self.min_value, self.max_value]
        ax.set_ylim(lims)

        # Sets the position for the polar label
        ax.set_rlabel_position(0)

        # Adjusts the labels for the y ticks
        y_labels = [str(tick) for tick in ranges]
        ax.set_yticks(ranges)

        # Formats the label of the y axis
        ax.set_yticklabels(y_labels, fontsize=self.ticks_size,
                           position=(0, 0), verticalalignment='center')

        # Adjusts the rotation of the label
        ax.tick_params(axis='y', labelrotation=270)

        # Adjusts the space between plots
        plt.subplots_adjust(wspace=0)

        # Sets the format for the title
        plt.suptitle(self.title,
                     fontsize=self.title_size,
                     fontweight='bold',
                     family='monospace',
                     y=0.98)

        # Adds the formatted subtitle if needed
        if self.subtitle:
            # Adjusts the figure width and height to make space for the subtitle
            fig_width = fig.get_figwidth()
            fig_height = fig.get_figheight()

            fig.set_figwidth(fig_width * 1.5)
            fig.set_figheight(fig_height * 1.5)
            suptitle_pos = fig._suptitle.get_position()
            fig.text(0.5, suptitle_pos[1] - 0.05, self.subtitle,
                     ha='center', fontsize=self.subtitle_size, style='italic')

        # Saves the figure as a file
        plt.savefig(self.output_file)

        # Closes the image
        plt.close()
