from base_visualization import *

class Plot3D(BaseVisualization):
    def __init__(self, output_file, data=None, input_file=None, title=None, subtitle=None, min_values=None,
                 max_values=None, title_size=None, subtitle_size=None, label_size=None, ticks_size=None,
                 label_pad=None, major_grid_line_width=None, minor_grid_line_width=None, ticks_pad=None,
                 scatter_size=None, figure_size=None, input_values=None):
        """
        Initialize the Plot3D class, which is a subclass of BaseVisualization.

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
        Plot a 3D scatter plot based on the specified parameters.
        """
        
        # Sets all the values necessaries for formatting the specific chart
        self.set_data()
        self.set_summary()
        self.set_min_max_values()
        self.set_ticks_size(self.font_size / 4 * 3)
        self.set_label_pad(self.font_size * 2)

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
        zticks = self.calculate_tick_locations(
            self.min_values[2], self.max_values[2])

        # Creates the figure
        fig, ax = plt.subplots()
        fig = plt.figure(figsize=(10, 10))

        # Adjusts the subplot to 3d and the figure size
        ax = fig.add_subplot(projection="3d")
        ax.get_figure().set_size_inches(self.figure_size)

        # Obtains the labels for the ticks
        x_labels = [str(val) for val in xticks]
        y_labels = [str(val) for val in yticks]
        z_labels = [str(val) for val in zticks]

        # Sets the scatter with the parameters set
        ax.scatter(self.data[0], self.data[1],
                   self.data[2], s=self.scatter_size, alpha=1)
        
        # Plots the ticks and labels in the 3 dimensions
        plt.xticks(xticks, labels=x_labels)
        plt.yticks(yticks, labels=y_labels)
        ax.set_zticks(zticks, minor=False)
        ax.set_zticklabels(z_labels)

        # Sets the limits for the axes
        xlims = [self.min_values[0],
                 self.max_values[0] + (self.max_values[0] * 0.01)]
        ax.set_xlim(xlims)

        ylims = [self.min_values[1],
                 self.max_values[1] + (self.max_values[1] * 0.01)]
        ax.set_ylim(ylims)

        zlims = [self.min_values[2],
                 self.max_values[2] + (self.max_values[1] * 0.01)]
        ax.set_zlim(zlims)

        # Sets the padding and size for the ticks in both axes
        ax.tick_params(axis='both', which='major',
                       labelsize=self.ticks_size, pad=self.ticks_pad)

        # Adds the formatted subtitle if needed
        if self.subtitle:
            ax.set_title(
                self.subtitle, fontsize=self.subtitle_size, style='italic')
            
        # Sets the color and width of the major grid line
        ax.grid(which='major',
                linestyle='--',
                linewidth=self.major_grid_line_width,
                color='black',
                zorder=0)

        # Sets the format for the title
        plt.suptitle(self.title,
                     fontsize=self.title_size,
                     fontweight='bold',
                     family='monospace',
                     y=0.97)

        # Sets the label for the axes
        plt.xlabel("$f_1$", fontsize=self.label_size, labelpad=self.label_pad)
        plt.ylabel("$f_2$", fontsize=self.label_size, labelpad=self.label_pad)
        ax.set_zlabel("$f_3$", fontsize=self.label_size,
                      rotation=0, labelpad=self.label_pad)

        # Disables the automatic rotation
        ax.zaxis.set_rotate_label(False)  

        # Initializes the views for the resulting images
        views = [[30, 45], [45, -45],  [45, 135], [30, 30], [30, 60]]

        # For each view, it rotates the view and saves the images
        idx = 0
        for v in views:
            idx += 1
            ax.view_init(v[0], v[1])
            formatted_path = self.output_file[:-4] + \
                '_' + str(idx) + self.output_file[-4:]

            plt.savefig(formatted_path)

        # Closes the image
        plt.close()
