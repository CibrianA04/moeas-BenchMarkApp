from base_visualization import *

class BubbleChart(BaseVisualization):
    def __init__(self, output_file, data=None, input_file=None, title=None, subtitle=None, title_size=None, subtitle_size=None,
                 min_values=None, max_values=None, label_size=None, ticks_size=None,
                 label_pad=None, major_grid_line_width=None, minor_grid_line_width=None, ticks_pad=None,
                 scatter_size=None, figure_size=None, color=None, cmap=None, input_values=None):
        """
        Initialize the BubbleChart class, which is a subclass of BaseVisualization.
        
        Parameters:
        - input_file: Specifies the input file used for the visualization.
        - output_file: Specifies the output file where the visualization will be saved.
        - data: Specifies the data to be visualized.
        - title: Specifies the title of the visualization.
        - subtitle: Specifies the subtitle of the visualization.
        - title_size: Specifies the font size of the title.
        - subtitle_size: Specifies the font size of the subtitle.
        - min_values: Specifies the minimum values used in the visualization.
        - max_values: Specifies the maximum values used in the visualization.
        - label_size: Specifies the font size of the labels.
        - ticks_size: Specifies the size of the ticks in the visualization.
        - label_pad: Specifies the padding between labels and the visualization.
        - major_grid_line_width: Specifies the line width of major grid lines.
        - minor_grid_line_width: Specifies the line width of minor grid lines.
        - ticks_pad: Specifies the padding between ticks and the visualization.
        - scatter_size: Specifies the size of scatter plot markers.
        - figure_size: Specifies the size of the figure or plot.
        - color: Specifies the color used in the visualization.
        - cmap: Specifies the colormap used in the visualization.
        - input_values: Specifies the input values used in the visualization.
        """

        super().__init__(data=data, input_file=input_file, output_file=output_file, title=title, subtitle=subtitle, min_values=min_values,
                         max_values=max_values, title_size=title_size, subtitle_size=subtitle_size, label_size=label_size,
                         ticks_size=ticks_size, label_pad=label_pad, major_grid_line_width=major_grid_line_width,
                         minor_grid_line_width=minor_grid_line_width, ticks_pad=ticks_pad, scatter_size=scatter_size, 
                         figure_size=figure_size, input_values=input_values)

        
        self.color = color
        self.cmap = cmap

    def set_values(self):
        """
        Set default values for visualization attributes if not provided.
        """
        if self.color is None:
            if self.dim > 3:
                self.color = self.data[3]
            else:
                self.color = 'darkblue'
        
        if self.cmap is None:
            self.cmap = plt.get_cmap('gist_rainbow_r')

        if self.dim > 4:
            self.scatter_size = self.data[4] * 1000

    def set_color(self, color):
        """
        Set the color attribute of the visualization.

        Parameters:
        - color: The color to be set.
        """
        self.color = color

    def get_color(self):
        """
        Gets the color attribute of the visualization.
        """
        return self.color

    def set_cmap(self, cmap):
        """
        Set the cmap attribute of the visualization.

        Parameters:
        - cmap: The colormap to be set.
        """
        self.cmap = cmap

    def get_cmap(self):
        """
        Gets the cmap attribute of the visualization.
        """
        return self.cmap

    def plot(self): 
        """
        Plot a bubble chart based on the specified parameters.
        """
        # Sets all the values necessaries for formatting the specific chart
        self.set_data()
        self.set_summary()
        self.set_min_max_values()
        self.set_dim()
        self.set_values()

        # Sets the label pad and ticks size for this specific chart
        if self.label_pad is None:
            self.set_label_pad(self.font_size * 2)
        if self.ticks_size is None:
            self.set_ticks_size(self.font_size / 4 * 3)

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
        fig = plt.figure(figsize=(10, 10))

        # Adjusts the subplot to 3d and the figure size
        ax = fig.add_subplot(projection="3d")
        ax.get_figure().set_size_inches(self.figure_size)

        # Obtains the labels for the ticks
        x_labels = [str(val) for val in xticks]
        y_labels = [str(val) for val in yticks]
        z_labels = [str(val) for val in zticks]

        # Sets the scatter with the parameters set
        scatter = ax.scatter(self.data[0], self.data[1], self.data[2], s=self.scatter_size,
                             alpha=1, c=self.color, cmap=self.cmap)
        
        # If the dimension is greater than 3, it adds the colorbar
        if self.dim > 3:
            colorbar = plt.colorbar(scatter, location='right',
                                    pad=0.05)
            plt.subplots_adjust(right=0.9)
            colorbar.ax.set_position([0.87, 0.2, 0.03, 0.6])
            colorticks = np.linspace(self.color.min(), self.color.max(), 10)
            colorlabels = [f"{x:.2f}" for x in colorticks]
            colorbar.set_ticks(colorticks)
            colorbar.set_ticklabels(colorlabels)
            colorbar.ax.tick_params(labelsize=self.label_size*0.75)
            colorbar.set_label('$f_4$', rotation=0, labelpad=self.label_pad * 0.5,
                               fontsize=self.label_size)
        
        # Plots the ticks and labels in the 3 dimensions
        plt.xticks(xticks, labels=x_labels)
        plt.yticks(yticks, labels=y_labels)
        ax.set_zticks(zticks, minor=False)
        ax.set_zticklabels(z_labels)

        # Sets the limits for the axes
        xlims = [self.min_values[0],
                 self.max_values[0] + (self.max_values[0] * 0.01)]
        ax.set_xlim(xlims)

        ylims = [self.min_values[1], self.max_values[1] +
                 (self.max_values[1] * 0.01)]
        ax.set_ylim(ylims)

        zlims = [self.min_values[2], self.max_values[2] +
                 (self.max_values[1] * 0.01)]
        ax.set_zlim(zlims)

        # Sets the padding and size for the ticks in both axes
        ax.tick_params(axis='both', which='major',
                       labelsize=self.ticks_size, pad=self.ticks_pad)

        # Sets the color and width of the major grid line
        ax.grid(which='major',
                linewidth=self.major_grid_line_width,
                color='black',
                zorder=0)
        
        # Sets the format for the title
        plt.suptitle(self.title,
                     fontsize=self.title_size,
                    fontweight='bold',
                    family='monospace',
                    y=0.97)
        
        # Adds the formatted subtitle if needed
        if self.subtitle:
            ax.set_title(
                self.subtitle, fontsize=self.subtitle_size, style='italic')

        
        # Sets the label for the axes
        plt.xlabel("$f_1$", fontsize=self.label_size, labelpad=self.label_pad)
        plt.ylabel("$f_2$", fontsize=self.label_size, labelpad=self.label_pad)
        ax.set_zlabel("$f_3$", fontsize=self.label_size,
                      rotation=0, labelpad=self.label_pad)

        # Disables automatic rotation of labels
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
