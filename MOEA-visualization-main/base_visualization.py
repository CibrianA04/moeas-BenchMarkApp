import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as colors
import matplotlib.animation as animation
import decimal
import os
from abc import ABC, abstractmethod
class BaseVisualization(ABC):

    def __init__(self, output_file, input_file=None, data=None, title=None, dim=None, subtitle=None, min_values=None,
                 max_values=None, title_size=None, subtitle_size=None, label_size=None, ticks_size=None,
                 label_pad=None, major_grid_line_width=None, minor_grid_line_width=None, ticks_pad=None,
                 scatter_size=None, figure_size=None, input_values=None):
        """
        Initialize the BaseVisualization class.
        
        Parameters:
        - output_file: Specifies the output file where the visualization will be saved.
        - input_file: Specifies an input file that may be used for the visualization.
        - data: Specifies the data to be visualized.
        - title: Specifies the title of the visualization.
        - dim: Specifies the dimensions of the visualization.
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
        self.input_file = input_file
        self.data = data
        self.output_file = output_file
        self.title = title
        self.subtitle = subtitle
        self.min_values = min_values
        self.max_values = max_values
        self.title_size = title_size
        self.subtitle_size = subtitle_size
        self.label_size = label_size
        self.ticks_size = ticks_size
        self.label_pad = label_pad
        self.major_grid_line_width = major_grid_line_width
        self.minor_grid_line_width = minor_grid_line_width
        self.ticks_pad = ticks_pad
        self.scatter_size = scatter_size
        self.figure_size = figure_size
        self.dim = dim
        input_values = input_values
        self.font_size = 275 / 2
        self.summary = None

    def set_summary(self):
        """
        Set the summary statistics of the data.
        """
        summary = self.data.describe()
        self.summary = summary

    def get_summary(self):
        """
        Gets the summary attribute.
        """
        return self.summary

    def set_data(self, new_data=None):
        """
        Set the data for the visualization.

        This function checks if the data is not already provided but an input_file is specified. 
        If so, it reads the data from the input_file and assigns it to the data attribute of the object.
        It raises and exception, when none is provided.
        """
        if self.data is None and self.input_file is not None:
            self.data = pd.read_csv(
                self.input_file, delimiter=" ", header=None, skiprows=1)
        if self.data is not None and new_data is not None:
            self.data = new_data
        if self.data is None and self.input_file is None:
            raise Exception("You must provide the data or the input_file")

    def get_data(self):
        """
        Gets the data attribute.
        """
        return self.data

    def set_dim(self):
        """
        Set the dimension (number of columns) of the visualization.

        If the dimension (self.dim) is not provided, it is set based on the number of columns in the summary data.
        """
        if self.dim is None:
            self.dim = self.summary.shape[1]

    def get_dim(self):
        """
        Gets the dimension attribute.
        """
        return self.dim

    def set_min_max_values(self):
        """
        Set default values for attributes if they are not provided.
        """

        if self.min_values is None:
            self.min_values = self.get_values('min')

        if self.max_values is None:
            self.max_values = self.get_values('max')

    def get_min_values(self):
        """
        Gets the min values attribute.
        """
        return self.min_values

    def get_max_values(self):
        """
        Gets the max values attribute.
        """
        return self.max_values

    def set_figure_size(self):
        """
        Set the figure size based on the provided input values.

        This method assigns the figure size based on the value specified in the input_values parameter.
        """
        self.figure_size = self.set_size(self.figure_size, self.input_values)

    def get_figure_size(self):
        """
        Gets the figure size attribute.
        """
        return self.figure_size

    def set_title_size(self, size):
        """
        Set the font size of the title.
        
        Parameters:
        - size: Font size to be set for the title.
        """
        self.title_size = size

    def get_title_size(self):
        """
        Gets the font size of the title.
        """
        return self.title_size

    def set_subtitle_size(self, size):
        """
        Set the font size of the subtitle.
        
        Parameters:
        - size: Font size to be set for the subtitle.
        """
        self.subtitle_size = size

    def get_subtitle_size(self):
        """
        Gets the font size of the subtitle.
        """
        return self.subtitle_size

    def set_label_size(self, size):
        """
        Set the font size of the label.
        
        Parameters:
        - size: Font size to be set for the label.
        """
        self.label_size = size

    def get_label_size(self):
        """
        Gets the font size of the label.
        """
        return self.label_size

    def set_ticks_size(self, size):
        """
        Set the font size of the ticks.
        
        Parameters:
        - size: Font size to be set for the ticks.
        """
        self.ticks_size = size

    def get_ticks_size(self):
        """
        Gets the font size of the ticks.
        """
        return self.ticks_size

    def set_label_pad(self, size):
        """
        Set the size of the label padding.
        
        Parameters:
        - size: Size to be set for the label padding.
        """
        self.label_pad = size

    def get_label_pad(self):
        """
        Gets the size of the label padding.
        """
        return self.label_pad

    def set_major_grid_line_width(self, size):
        """
        Set the size of the major grid line.
        
        Parameters:
        - size: Size to be set for the major grid line.
        """
        self.major_grid_line_width = size

    def get_major_grid_line_width(self):
        """
        Gets the size of the major grid line.
        """
        return self.major_grid_line_width

    def set_minor_grid_line_width(self, size):
        """
        Set the size of the minor grid line.
        
        Parameters:
        - size: Size to be set for the minor grid line.
        """
        self.minor_grid_line_width = size

    def get_minor_grid_line_width(self):
        """
        Gets the size of the minor grid line.
        """
        return self.minor_grid_line_width

    def set_ticks_pad(self, size):
        """
        Set the size of the ticks padding.
        
        Parameters:
        - size: Size to be set for the ticks padding.
        """
        self.ticks_pad = size

    def get_ticks_pad(self):
        """
        Gets the size of the ticks padding.
        """
        return self.ticks_pad

    def set_scatter_size(self, size):
        """
        Set the size of the scatter dot.
        
        Parameters:
        - size: Size to be set for the scatter dot.
        """
        self.scatter_size = size

    def get_scatter_size(self):
        """
        Gets the size of the scatter dot.
        """
        return self.scatter_size

    def set_input_values(self, value):
        """
        Set the values of the input values.
        
        Parameters:
        - size: Size to be set for the input values.
        """
        self.input_values = value

    def get_input_values(self):
        """
        Gets the input values attribute.
        """
        return self.input_values

    def set_default_values(self):
        """
        Set default values for attributes if they are not provided.
        """
        if self.title is None:
            self.title = self.extract_filename(self.output_file)

        if self.title_size is None:
            self.title_size = self.font_size + 20

        if self.subtitle_size is None:
            self.subtitle_size = self.font_size

        if self.label_size is None:
            self.label_size = self.font_size + 20

        if self.ticks_size is None:
            self.ticks_size = self.font_size

        if self.label_pad is None:
            self.label_pad = self.font_size/2

        if self.major_grid_line_width is None:
            self.major_grid_line_width = self.font_size / 15

        if self.minor_grid_line_width is None:
            self.minor_grid_line_width = self.font_size / 30

        if self.ticks_pad is None:
            self.ticks_pad = self.font_size / 2

        if self.scatter_size is None:
            self.scatter_size = self.font_size * 10

        if self.figure_size is None:
            self.figure_size = (60, 60)

    def extract_filename(self, path):
        """
        Extracts the filename from a given path.
        
        Parameters:
        - path: The path from which to extract the filename.
        
        Returns:
        - The extracted filename without the file extension.
        """
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        return name.split('/')[-1]

    def get_values(self, type):
        """
        Get rounded values of a specified type from the summary.

        Parameters:
        - type: Specifies the type of value to retrieve. Should be 'min' or 'max'.

        Returns:
        - values: A list of rounded values corresponding to the specified type.
        """

        rounding = {'min': self.round_down, 'max': self.round_up}

        num_columns = self.summary.shape[1]
        values = []

        #For each columns format the min o max values to 2 decimals
        for col in range(num_columns):
            value = self.summary[col].loc[type]
            value_formatted = float(decimal.Decimal(str(value)).quantize(
                decimal.Decimal('.01')))
            value_rounded = rounding[type](value_formatted)
            values.append(value_rounded)

        return values

    def set_size(self, base_size, input_values):
        """
        Set the size of the visualization based on the input values.

        Parameters:
        - base_size: Tuple specifying the base size of the visualization.
        - input_values: List of input values used to determine the size.

        Returns:
        - size: Tuple specifying the calculated size of the visualization.
        """
        formatted_values = ["{:.2f}".format(val) for val in input_values]
        max_len_str = max(formatted_values, key=len)

        if len(max_len_str) > 3:
            size = (np.around(base_size[0] * (1 + (0.17 * (len(max_len_str) - 3)))),
                    np.around(base_size[1] * (1 + (0.17 * (len(max_len_str) - 3)))))
        return size

    def round_down(self, num):
        """
        Round down a number to the nearest specified decimal value.
        
        Parameters:
        - num: The number to be rounded down.
        
        Returns:
        The rounded down number.
        """

        integer, decimal = divmod(num, 1)
        round_dict = {0.1: 0, 0.251: 0.25, 0.51: 0.5, 0.751: 0.75}
        return integer + round_dict.get(max(filter(lambda x: x <= decimal, round_dict.keys()), default=0), 0)

    def round_up(self, num):
        """
        Rounds up a given number to the nearest predefined values.
        
        Parameters:
        - num: The number to be rounded up.
        
        Returns:
        - The rounded-up number.
        """
        integer, decimal = divmod(num, 1)
        round_dict = {0: 0, 0.1: 0.25, 0.25: 0.25, 0.26: 0.5,
                      0.5: 0.5, 0.51: 0.75, 0.75: 0.75, 0.76: 1}
        return integer + round_dict.get(min(round_dict.keys(), key=lambda x: abs(x-decimal)), 0)

    def round_to_base(self, x, base):
        """
        Round a number `x` to the nearest multiple of `base` and return the result with two decimal places.
        
        Parameters:
        - x: The number to be rounded.
        - base: The base value to round to (nearest multiple).
        
        Returns:
        The rounded number to the nearest multiple of `base` with two decimal places.
        """
        if base == 0:
            return 0
        try:
            result = round(base * round(float(x) / base), 2)
        except ZeroDivisionError:
            result = 0
        except OverflowError:
            result = float('inf')
        return result

    def get_tick_step(self, diff):
        """
        Determine the appropriate tick step based on the difference value.
        
        Parameters:
        - diff: The difference value used to determine the tick step.
        
        Returns:
        - The tick step value.
        """

        if diff <= 0.05:
            return 0.01
        elif diff <= 0.25:
            return 0.05
        elif diff <= 0.5:
            return 0.1
        else:
            n_ticks = 10
            step = self.round_to_base(diff / n_ticks, 0.5)
            if step < 0.05:
                step = 0.05
            return step

    def calculate_tick_locations(self, min_val, max_val):
        """
        Calculate the tick locations based on the minimum and maximum values.

        Parameters:
        - min_val: The minimum value of the data range.
        - max_val: The maximum value of the data range.

        Returns:
        - tick_locations: A list of tick locations for the visualization.
        """

        range_val = max_val - min_val

        step_size = self.get_tick_step(range_val)

        if np.isnan(step_size) or not np.isfinite(step_size) or step_size == 0:
            return []

        num_ticks = int(round(range_val / step_size)) + 1

        if num_ticks < 5:
            step_size = range_val / 4
            num_ticks = 5

        tick_locations = [self.round_to_base(
            min_val + i * step_size, step_size) for i in range(num_ticks)]

        while len(tick_locations) > 10:
            tick_locations = [tick_locations[i]
                              for i in range(0, len(tick_locations), 2)]

        return tick_locations

    @abstractmethod
    def plot(self):
        """
        Abstract method to be implemented in child classes
        """
        pass
