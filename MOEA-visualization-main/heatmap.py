from base_visualization import *

class HeatMap(BaseVisualization):
    def __init__(self, output_file, data=None, input_file=None,  title=None, subtitle=None, min_value=None,
                 max_value=None, title_size=None, subtitle_size=None, label_size=None, ticks_size=None,
                 label_pad=None, major_grid_line_width=None, minor_grid_line_width=None, ticks_pad=None,
                 scatter_size=None, figure_size=None, input_values=None, normalized=True):
        """
        Initialize the HeatMap class, inheriting from BaseVisualization.
        
        Parameters:
        - input_file: Specifies the input file used for the heatmap.
        - output_file: Specifies the output file where the heatmap will be saved.
        - data: Specifies the data to be visualized.
        - title: Specifies the title of the heatmap.
        - subtitle: Specifies the subtitle of the heatmap.
        - min_value: Specifies the minimum value for the heatmap color scale.
        - max_value: Specifies the maximum value for the heatmap color scale.
        - title_size: Specifies the font size of the title.
        - subtitle_size: Specifies the font size of the subtitle.
        - label_size: Specifies the font size of the labels.
        - ticks_size: Specifies the size of the ticks in the heatmap.
        - label_pad: Specifies the padding between labels and the heatmap.
        - major_grid_line_width: Specifies the line width of major grid lines.
        - minor_grid_line_width: Specifies the line width of minor grid lines.
        - ticks_pad: Specifies the padding between ticks and the heatmap.
        - scatter_size: Specifies the size of scatter plot markers.
        - figure_size: Specifies the size of the figure or plot.
        - input_values: Specifies the input values used in the heatmap.
        - normalized: Specifies whether the input data should be normalized before generating the heatmap (default: True).
        """
        super().__init__(data=data, input_file=input_file, output_file=output_file, title=title, subtitle=subtitle,
                         title_size=title_size, subtitle_size=subtitle_size, label_size=label_size,
                         ticks_size=ticks_size, label_pad=label_pad, major_grid_line_width=major_grid_line_width,
                         minor_grid_line_width=minor_grid_line_width, ticks_pad=ticks_pad, scatter_size=scatter_size,
                         figure_size=figure_size, input_values=input_values)

        self.min_value = min_value
        self.max_value = max_value
        self.normalized = normalized

    def set_values(self):
        """
        Set default values for visualization attributes if not provided.
        """
        if self.min_value is None:
            self.min_value = min(self.min_values)

        if self.max_value is None:
            self.max_value = max(self.max_values)

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

    def normalize_value(self, value):
        """
        Normalize a given value based on the minimum and maximum values.

        Parameters:
        - value: The value to be normalized.

        Returns:
        - new_value: The normalized value.
        """
        range = self.max_value - self.min_value
        new_value = (value - self.min_value) / range
        return new_value

    def normalize_data(self):
        """
        Normalize the values in the data columns and return a new DataFrame with normalized values.
        """
        # Create a copy of the original DataFrame
        normalized_data = self.data.copy()  

        # Applies the normalize function to each value of each column of the frame
        for column in normalized_data.columns:
            normalized_data[column] = self.data[column].apply(
                self.normalize_value)

        return normalized_data

    def set_normalize_data(self):
        """
        Normalize the data if it is not already normalized.
        """

        #If the values are normalized, it sets the new the summary and min and max values
        if self.normalized:
            new_data = self.normalize_data()
            self.set_data(new_data)

            self.set_summary()

            self.set_min_value(min(self.get_values('min')))

            self.set_max_value(max(self.get_values('max')))

    def plot(self):
        """
        Plot a heat map based on the specified parameters.
        """
        # Sets all the values necessaries for formatting the specific chart
        self.set_data()
        self.set_summary()
        self.set_min_max_values()
        self.set_dim()
        self.set_values()
        
        # Normalizes the data if needed
        self.set_normalize_data()

        # Sets the default values if needed
        self.set_default_values()

        # Set the figure size of the figure based on the min and max values
        self.input_values = [self.min_value, self.max_value]
        self.set_figure_size()

        # Sets the normalize colors to the colorbar
        cmap = plt.cm.get_cmap('Blues')
        norm = colors.Normalize(vmin=self.min_value, vmax=self.max_value)

        # Creates the figure size
        fig, ax = plt.subplots(figsize=(60, 60))

        #Creates the heatmap
        heatmap = ax.matshow(self.data, cmap=cmap, norm=norm)
        
        # Sets the label for the axis
        xlabels = [f'$f_{i+1}$' for i in range(self.dim)]

        # Sets the ticks for the axis
        ax.set_xticks(np.arange(self.dim))
        ax.set_yticks([])

        # Sets the labels of the ticks
        ax.set_xticklabels(xlabels, rotation=45, ha='right',
                           fontsize=self.label_size * 0.75)
        ax.set_yticklabels([])

        # Creates the color bar for heatmap
        colorbar = fig.colorbar(heatmap)

        # Adds the ticks for the color bar
        colorbar.ax.tick_params(labelsize=self.label_size*0.75)

        # Sets the format for the title
        plt.suptitle(self.title,
                     fontsize=self.title_size * 0.75,
                     fontweight='bold',
                     family='monospace',
                     y=0.98)

        # Adds the formatted subtitle if needed
        if self.subtitle:
            suptitle_pos = fig._suptitle.get_position()
            fig.text(0.5, suptitle_pos[1] - 0.05, self.subtitle,
                     ha='center', fontsize=self.subtitle_size * 0.65, style='italic')

        # Sets the aspect to auto (fills the rectangle of data)
        ax.set_aspect('auto')

        # Saves the figure as a file
        plt.savefig(self.output_file)

        # Closes the image
        plt.close()
