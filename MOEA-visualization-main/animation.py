from plot2D import Plot2D
from plot3D import Plot3D
from parallel_coord import ParallelCoordinates
from radar import RadarChart
from heatmap import HeatMap
from bubble import BubbleChart
from base_visualization import *

class Animation():
    def __init__(self, files=None, output_file=None):
        self.files = files
        self.output_file = output_file
        self.images = []

        """
        Initialize the Animation class.
        
        Parameters:
        - files: The files to animate.
        - output_file: The output file to save the animation.
        - images: Images to animate.
        """

    def set_files(self, files):
        """
        Set the files to animate

        Parameters
        - files : The files to animate
        """
        self.files = files

    def get_files(self):
        """
        Get the files to animate
        """
        return self.files

    def set_default_values(self):
        """
        Set default values for visualization attributes if not provided.
        """
        if self.output_file is None:
            self.output_file = "animation.gif"

    def set_output_file(self, file):
        """
        Set the name of the output file if not provided.
        """
        self.output_file = file

    def get_output_file(self):
        """
        Get the name of the output file.
        """
        return self.output_file

    def set_image_files(self, images):
        """
        Set the list of the images to be animated
        """
        self.images = images

    def get_image_files(self):
        """
        Get the image files.
        """
        return self.images

    def plot_to_animate(self, file_list, parameter_dict, obj_type=['plot2d',
                                                                   'plot3d',
                                                                   'parallel',
                                                                   'bubble',
                                                                   'radar',
                                                                   'heatmap']):
        """
        Iterates over the file list to plot each file.

        Parameters:
            - file_list: List of strings of the files to plot
            - parameter_dict: Dictionary of the plot parameters
            - obj_type: String of the chart type to plot

        """
        self.files = []

        #Parameters that are shared among all classes
        common_params = {
            'data': None,
            'title': None,
            'subtitle': None,
            'title_size': None,
            'subtitle_size': None,
            'label_size': None,
            'ticks_size': None,
            'label_pad': None,
            'major_grid_line_width': None,
            'minor_grid_line_width': None,
            'ticks_pad': None,
            'scatter_size': None,
            'figure_size': None,
            'input_values': None
        }

        # Parameters that are specific for some classes
        plot2d_params = {
            'min_values': None,
            'max_values': None,
        }

        plot3d_params = {
            'min_values': None,
            'max_values': None,
        }

        parallel_params = {
            'min_value': None,
            'max_value': None,
        }

        bubble_params = {
            'min_values': None,
            'max_values': None,
            'color': None,
            'cmap': None,
        }

        radar_params = {
            'min_value': None,
            'max_value': None,
            'minor': False,
            'line_width': None,
        }

        heatmap_params = {
            'min_value': None,
            'max_value': None,
            'normalized': True,
        }

        charts = {
            'plot2d': (Plot2D, {**common_params, **plot2d_params}),
            'plot3d': (Plot3D, {**common_params, **plot3d_params}),
            'parallel': (ParallelCoordinates, {**common_params, **parallel_params}),
            'bubble': (BubbleChart, {**common_params, **bubble_params}),
            'radar': (RadarChart, {**common_params, **radar_params}),
            'heatmap': (HeatMap, {**common_params, **heatmap_params}),
        }
        
        idx = 0
        if obj_type in charts:
            # Iterates over the file list to plot each diagram
            for file in file_list:
                idx += 1
                # Obtains the object of the chart and the attributes for the chart
                obj_class, obj_params = charts[obj_type]
                # Updates the attributes for the chart
                obj_params.update({**parameter_dict, 'input_file': file}
                                  )
                # Sets output name of the image to png
                output_name = f"{file}_{idx}.png"
                # Initializes the object
                obj = obj_class(output_name, **obj_params)
                # Plots the chart and generates an image of it
                obj.plot()
                # Updates the file list to add the name of the image generated
                self.files.append(output_name)

        else:
            print(f"Unsupported chart type: {obj_type}")

    def read_files(self):
        """
        Iterates over the file list to read each image of the chart.
        """
        for image in self.files:
            # Reads the image
            img = plt.imread(image)
            # Generates an image object and appends it to the images list
            img_obj = plt.imshow(img, animated=True)
            self.images.append([img_obj])

    def animate(self, output_file=None):
        """
        Animates the list of the images.
        
        Parameters:
            - output_file = String of the output file
        """

        fig, ax = plt.subplots(figsize=(10, 10))
        
        self.read_files()
        self.set_output_file(output_file)

        # Generates the animation
        anim = animation.ArtistAnimation(
            fig, self.images, interval=500, blit=True)

        frame_height, frame_width, _ = self.images[0][0].get_array().shape

        # Sets the limits of the chart to the wight and height
        ax.set_xlim(0, frame_width)
        ax.set_ylim(0, frame_height)

        # Removes the ticks of the gif
        ax.set_xticks([])
        ax.set_yticks([])

        # Rotates the image
        ax.invert_yaxis()

        # Removes the spines of the gif
        spine_directions = ['top', 'bottom', 'left', 'right']
        for spine in spine_directions:
            ax.spines[spine].set_color('white')

        # Saves the gif as a file
        anim.save(self.output_file, writer='pillow')

        plt.close()
