"""Matplotlib extension class

Description:
------------

Wrapper functions around matplotlib subroutines are defined in this class.

"""

# Standard library imports
from datetime import datetime
from pathlib import PosixPath
from typing import Any, Dict, List, Tuple, Union

# External library imports
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np

# Midgard imports
from midgard.dev import log
from midgard.math.linear_regression import LinearRegression
from midgard.math.unit import Unit

# TODO: Distinguish between _get_statistic and _get_statistic_text

class MatPlotExt:
    """Class for plotting - Extension of matplotlib
    
    
    Following *options** can be selected:

    | Option             | Value            | Description                                                             |
    |--------------------|------------------|-------------------------------------------------------------------------|
    | colormap           | <type>           | Color map type for plotting either events or labels (e.g. viridis, jet, |
    |                    |                  | tab10, rainbow, hsv, plasma)                                            |
    | dpi                | <num>            | Resolution of file in dots per inch                                     |
    | figsize            | (num, num)       | Figure size given by (width, height) in inches                          |
    | fsize_subtitle     | <num>            | Fontsize of subplot title (statistical information)                     |
    | grid               | <True|False>     | Plot grid                                                               |
    | histogram          | <x, y>           | Plot x-axis histogram on top, y-axis histogram on right or for both     |
    |                    |                  | axis on scatter plot                                                    |
    | histogram_binwidth | <num>            | Histogram bin width                                                     |
    | histogram_size     | <num>            | Histogram y-axis size                                                   |
    | legend             | <True|False>     | Plot legend                                                             |
    | legend_location    | <right, bottom>  | Legend location                                                         |
    | legend_ncol        | <num>            | The number of legend columns                                            |
    | linestyle          | <style>          | Line style for plot type (e.g. 'solid', 'dashed')                       |
    | marker             | <'.'|'-'>        | Marker type                                                             |
    |                    |                  | if in one scatter subplot several plots should be plotted.              |
    | plot_to            | <console|file>   | Plot figure on console or file                                          |
    | plot_type          | <scatter|plot>   | Choose either "scatter" or "plot" type                                  |
    | projection         | <type>           | Projection type of plot (e.g. 'polar')                                  |
    | reg_line           | <True|False>     | Regression line flag                                                    |
    | statistic          | <rms, mean, ...> | Plot statistical information. Following function can be defined: 'max', |
    |                    |                  | 'mean', 'min', 'rms', 'std', 'percentile' (see function _get_statistic  |
    |                    |                  | for more information)                                                   |
    | tick_labelsize     | <(axis, size)>   | Change label size of x- and y-axis tick labels. This can be done either |
    |                    |                  | for x-axis, y-axis or both axis via specifying 'x', 'y' or both'.       |
    | title              | <text>           | Main title of subplots                                                  |
    | xlim               | <[num, num]|     | Define x-axis limit by defining a list with [left, right] range. If     |
    |                    |  auto>]          | xlim=auto, then x-axis limit is automatically chosen                    |
    | xticks             | <[num, ...]>     | Define x-axis ticks by defining a list with ticks                       |
    | xticklabels        | <[text, ...]>    | Define x-axis ticks labels by defining a list with labels               |
    | ylim               | <[num, num]>     | Define y-axis limit by defining a list with [bottom, top] range         |
    | yticks             | <[num, ...]>     | Define y-axis ticks by defining a list with ticks                       |
    | yticklabels        | <[text, ...]>    | Define y-axis ticks labels by defining a list with labels               |
    """

    def __init__(
        self, options: Dict[str, Any]=None) -> None:
        """Set up a new Report object

        Args:
            options:     Plotting options, which can overwrite default definition.
        """
        
        # Default plotting options
        self.options = {
            "alpha": 1,
            "colormap": "tab20",
            "dpi": 200,
            "figsize": (6, 8),
            "fontsize": 12,
            "fsize_subtitle": 8,
            "grid": False,
            "histogram": "",
            "histogram_binwidth": 0.25,
            "histogram_size": 1.2,
            "marker": ".",
            "markersize": 9,
            "legend": False,
            "legend_location": None,
            "legend_ncol": 1,
            "linestyle": "solid",
            "plot_to": "console",
            "plot_type": "scatter",
            "projection": None,
            "reg_line": False,
            "sharex": True,
            "sharey": True,
            "statistic": [],
            "tick_labelsize": [],
            "title": "",
            "xlim": [],
            "xticks": [],
            "xticklabels": [],
            "ylim": [],
            "yticks": [],
            "yticklabels": [],
        }
                             
        # Update options
        if options:
            set_options(options)
            
            
    def get_statistic(
        self,
        data: np.ndarray, 
        funcs: List[str] = ["rms", "mean", "std", "min", "max", "percentile"], 
        unit: str = "",
    ) -> List[str]:
        """Get text string with statistical information
    
        List of statistical functions (**funcs**), which can be chosen:
    
        | Function   | Description                      |
        |------------|----------------------------------|
        | max        | Maximal value of data array      |
        | min        | Minimal value of data array      |
        | mean       | Mean value of data array         |
        | percentile | 95th percentile of data array    |
        | rms        | Root mean square of data array   |
        | std        | Standard deviation of data array |
    
    
        Args:
            data:   Array with data.
            funcs:  List with statistical choices
    
        Returns:
            List with strings representing statistical information
        """
        stats = list()
    
        # Define functions
        func_def = {
            "max": ("Max", np.nanmax),
            "min": ("Min", np.nanmin),
            "mean": ("Mean", np.nanmean),
            "std": ("Std", np.nanstd),
        }
    
        if "rms" in funcs:
            rms = lambda x: np.sqrt(np.nanmean(np.square(x)))
            func_def.update({"rms": ("RMS", rms)})
    
        if "percentile" in funcs:
            percentile = lambda x: np.nanpercentile(x, 95)
            func_def.update({"percentile": ("95th perc.", percentile)})
    
        # Generate statistical text string
        for func in funcs:
            stat = np.apply_along_axis(func_def[func][1], 0, data)
            if np.abs(stat) >= 1000 or (stat < 0.01 and stat > -0.01):
                stats.append(f"{func_def[func][0]}: {stat:.0e} {Unit(unit).units:~P}")  # with abbreviated SI unit
            else:
                width = ".1f" if ("mm" == unit or "millimeter" == unit) else ".2f"
                stats.append(f"{func_def[func][0]}: {stat:{width}} {Unit(unit).units:~P}")  # with abbreviated SI unit
        return stats
    

    def set_options(self, options: Dict[str, Any]) -> None:
        """Overwrite default plotting options
        
        Args:
            options:    Plotting options, which can overwrite default definition.
        """
        self.options.update(options)
    
    
    #
    # BAR PLOTS
    #
    def plot_bar_dataframe_columns(
        self,
        df: "Dataframe",
        column: str,
        path: PosixPath,
        xlabel: str = "",
        ylabel: str = "",
        label: str = "label",
        colors: Union[List[str], None] = None,
        options: Union[Dict[str, Any], None] = None,
    ) -> None:
        """Generate bar plot of given dataframe columns
    
        If 'label' column is given in Dataframe (as 'df.label'), then the bars are color coded based on the defined labels.
        In addition a legend is added with information about the labels.
    
        Following **options** options can be overwritten:
    
        | Option         | Value            | Description                                                                |
        |----------------|------------------|----------------------------------------------------------------------------|
        | colormap       | <type>           | Color map type for plotting labels (e.g. viridis, jet, tab10, rainbow,     |
        |                |                  | hsv, plasma)                                                               |
        | dpi            | <num>            | Resolution of file in dots per inch                                        |
        | figsize        | (num, num)       | Figure size                                                                |
        | fontsize       | <num>            | Fontsize of x- and y-axis                                                  |
        | legend         | <True|False>     | Plot legend                                                                |
        | legend_location| <right, bottom>  | Legend location                                                            |
        | legend_ncol    | <num>            | The number of legend columns                                               |
        | plot_to        | <console|file>   | Plot figure on console or file                                             |
    
        Args:
           df:          Dataframe with data to plot.
           column:      Dataframe column to plot.
           path:        Figure path.
           xlabel:      x-axis label.
           ylabel:      y-axis label.
           label:       Dataframe column, which should be used as label.
           colors:      List with colors for defined label in "label" column. This option overwrites automatically chosen 
                        colors.
           options:     Dictionary with options, which overwrite default plot configuration.
        """
       
        # Overwrite options with argument definition
        if options:
            self.set_options(options)   
    
        # Assign to each label a color
        if label in df.columns:
            legend_labels, cmap = self._get_label_color(len(set(df[label])), colors=colors, cmap=self.options["colormap"])
    
            colors_dict = dict()
            for idx, label_ in enumerate(self._ordered_set(df[label])):
                colors_dict.update({label_: cmap(idx)})
            color = df[label].apply(lambda x: colors_dict[x])
        else:
            color = "steelblue"
    
        # Define figure size
        if "figsize" not in self.options.keys():
            fig_width = len(df.index) / 3 if len(df.index) > 30 else 6.4
            fig_height = fig_width / 1.33
            self.options["figsize"] = tuple((fig_width, fig_height))
    
        # Generate bar plot
        ax = df[column].plot(kind="bar", color=color, width=0.8, figsize=self.options["figsize"])
        # TODO
        # color=['green', 'red', 'yellow', 'blue', 'brown']
        # df_to_plot = df[column] if column else df
        # ax = df_to_plot.plot(kind="bar", color=color, width=0.8, figsize=self.options["figsize"])
        ax.set_xlabel(xlabel, fontsize=self.options["fontsize"])
        ax.set_ylabel(ylabel, fontsize=self.options["fontsize"])
    
        # Make legend
        if label in df.columns and self.options["legend"]:
            self.options["legend_location"] = "right" if self.options["legend_location"] == None else self.options["legend_location"]
            self._plot_legend(legend_labels, self._ordered_set(df[label]), self.options)
    
        # Automatically adjusts
        plt.tight_layout()
    
        # Save plot as file or show it on console
        if self.options["plot_to"] == "console":
            plt.show()
        elif self.options["plot_to"] == "file":
            plt.savefig(path, dpi=self.options["dpi"])
        else:
            log.fatal(f"Option <plot_to> is wrong with '{self.options['plot_to']}', expected 'console' or 'file'.")
    
        # Clear the current figure
        plt.clf()
        
        
    #
    # SCATTER/PLOT PLOTS
    #
    def plot(
        self,
        x_arrays: List[np.ndarray],
        y_arrays: List[np.ndarray],
        xlabel: str = "",
        ylabel: str = "",
        x_unit: str = "",
        y_unit: str = "",
        colors: Union[List[str], None] = None,
        labels: Union[List[str], None] = None,
        figure_path: str = "plot.png",
        options: Dict[str, Any] = None,
        events: Union[Dict[str, List[Any]], None] = None,
    ) -> None:
        """Generate scatter/plot plot
    
        Several scatter/plot plots can be plotted on one plot. This is defined via the chosen number of y_arrays data.
        Histogram is only plotted for the last given y-array in "y_arrays".
        
        Following **options** options can be overwritten:
    
        | Option             | Value            | Description                                                             |
        |--------------------|------------------|-------------------------------------------------------------------------|
        | colormap           | <type>           | Color map type for plotting either events or labels (e.g. viridis, jet, |
        |                    |                  | tab10, rainbow, hsv, plasma)                                            |
        | dpi                | <num>            | Resolution of file in dots per inch                                     |
        | figsize            | (num, num)       | Figure size given by (width, height) in inches                          |
        | fsize_subtitle     | <num>            | Fontsize of subplot title (statistical information)                     |
        | grid               | <True|False>     | Plot grid                                                               |
        | histogram          | <x, y>           | Plot x-axis histogram on top, y-axis histogram on right or for both     |
        |                    |                  | axis on scatter plot                                                    |
        | histogram_binwidth | <num>            | Histogram bin width                                                     |
        | histogram_size     | <num>            | Histogram y-axis size                                                   |
        | legend             | <True|False>     | Plot legend                                                             |
        | legend_location    | <right, bottom>  | Legend location                                                         |
        | legend_ncol        | <num>            | The number of legend columns                                            |
        | linestyle          | <style>          | Line style for plot type (e.g. 'solid', 'dashed')                       |
        | marker             | <'.'|'-'>        | Marker type                                                             |
        |                    |                  | if in one scatter subplot several plots should be plotted.              |
        | plot_to            | <console|file>   | Plot figure on console or file                                          |
        | plot_type          | <scatter|plot>   | Choose either "scatter" or "plot" type                                  |
        | projection         | <type>           | Projection type of plot (e.g. 'polar')                                  |
        | reg_line           | <True|False>     | Regression line flag                                                    |
        | statistic          | <rms, mean, ...> | Plot statistical information. Following function can be defined: 'max', |
        |                    |                  | 'mean', 'min', 'rms', 'std', 'percentile' (see function _get_statistic  |
        |                    |                  | for more information)                                                   |
        | tick_labelsize     | <(axis, size)>   | Change label size of x- and y-axis tick labels. This can be done either |
        |                    |                  | for x-axis, y-axis or both axis via specifying 'x', 'y' or both'.       |
        | title              | <text>           | Main title of subplots                                                  |
        | xlim               | <[num, num]|     | Define x-axis limit by defining a list with [left, right] range. If     |
        |                    |  auto>]          | xlim=auto, then x-axis limit is automatically chosen                    |
        | xticks             | <[num, ...]>     | Define x-axis ticks by defining a list with ticks                       |
        | xticklabels        | <[text, ...]>    | Define x-axis ticks labels by defining a list with labels               |
        | ylim               | <[num, num]>     | Define y-axis limit by defining a list with [bottom, top] range         |
        | yticks             | <[num, ...]>     | Define y-axis ticks by defining a list with ticks                       |
        | yticklabels        | <[text, ...]>    | Define y-axis ticks labels by defining a list with labels               |
    
        Args:
           x_arrays:       List of arrays with x-axis data to plot.
           y_arrays:       List of arrays with y-axis data to plot.
           xlabel:         X-axis label.
           ylabel:         Y-axis label. 
           x_unit:         X-axis unit.
           y_unit:         Y-axis unit.
           colors:         List with colors for each plot. It should corresponds to given number of y-axis arrays. 
                           Overwrites automatically chosen 'events'/'labels' colors.
           labels:         List with labels for each plot. It should corresponds to given number of y-axis arrays. 
                           Label colors are automatically chosen based on 'colormap'. 'colors' option overwrites 
                           automatically chosen label colors. NOTE: 'labels' and 'events' can not be chosen together, 
                           either 'labels' or 'events' should be defined.
           figure_path:    Figure path.
           options:        Dictionary with options, which overwrite default plot configuration.
           events:         Dictionary with event labels as key and lists of events as value. The events has to be 
                           related to x-axis data. Event colors are automatically chosen based on 'colormap'. NOTE: 
                           'labels' and 'events' can not be chosen together, either 'labels' or 'events' should be 
                           defined.
        """
    
        cmap = None

        # Overwrite options with argument definition
        if options:
            self.set_options(options)    
        original_histogram_option = self.options["histogram"]
    
        # Convert x_arrays, y_arrays to list
        x_arrays = [x_arrays] if not isinstance(x_arrays, list) else x_arrays
        y_arrays = [y_arrays] if not isinstance(y_arrays, list) else y_arrays
    
        # Generate scatter plot by using subplot function
        fig, ax = plt.subplots(
            nrows=1, ncols=1, figsize=self.options["figsize"], subplot_kw={"projection": self.options["projection"]}
        )
        fig.suptitle(f"{self.options['title']}", y=1.0)
    
        # Get event and label colors
        if events:
            legend_labels, cmap = self._get_label_color(len(events), colors, cmap=self.options["colormap"])
    
        if labels:
            legend_labels, cmap = self._get_label_color(len(labels), colors, cmap=self.options["colormap"])
    
        if colors is None:
            if cmap is None:
                colors = [None for ii in range(0, len(y_arrays))]
            else:
                colors = [cmap(ii) for ii in range(0, len(y_arrays))]
    
        # Plot several plots depending on number of y-arrays
        for idx, (x_array, y_array, color) in enumerate(zip(x_arrays, y_arrays, colors)):
    
            # Plot histogram only for the last scatter plot
            if self.options["histogram"]:
                if idx == (len(y_arrays) - 1):
                    self.options["histogram"] = original_histogram_option
                else:
                    self.options["histogram"] = ""
    
            # Plot figure
            self.subplot_row(
                ax, x_array, y_array, xlabel, ylabel, x_unit=x_unit, y_unit=y_unit, color=color
            )
    
            # Plot vertical line for events in plot
            if events:
                for idx, (label, entries) in enumerate(sorted(events.items())):
                    [ax.axvline(x=e, label=label, color=cmap(idx)) for e in entries]
    
        # Change tick labelsize
        if self.options["tick_labelsize"]:
            ax.tick_params(axis=self.options["tick_labelsize"][0], labelsize=self.options["tick_labelsize"][1])
    
        # Plot x-axis label
        ax.set(xlabel=xlabel)
    
        # Set polar plot self.options
        if self.options["projection"] == "polar":
            ax.set_theta_zero_location("N")  # sets 0(deg) to North
            ax.set_theta_direction(-1)  # sets plot clockwise
    
        # Plot legend
        if events:
            self.options["legend_location"] = "bottom" if self.options["legend_location"] == None else self.options["legend_location"]
            self._plot_legend(legend_labels, labels, self.options)
    
        if labels:
            if self.options["projection"] == "polar":
                self.options["legend_location"] = "bottom" if self.options["legend_location"] == None else self.options["legend_location"]
            else:
                self.options["legend_location"] = "right" if self.options["legend_location"] == None else self.options["legend_location"]
    
            self._plot_legend(legend_labels, labels, self.options)
    
        # Rotates and right aligns the x labels, and moves the bottom of the axes up to make room for them
        if isinstance(x_arrays[0][0], datetime):
            fig.autofmt_xdate()
    
        # Automatically adjusts subplot params so that the subplot(s) fits in to the figure area
        fig.tight_layout()
    
        # Adjust plot axes (to place title correctly)
        if self.options["projection"] == "polar":
            fig.subplots_adjust(top=0.83)
        else:
            fig.subplots_adjust(top=0.92)
    
        # Save plot as file or show it on console
        if self.options["plot_to"] == "console":
            plt.show()
        elif self.options["plot_to"] == "file":
            plt.savefig(figure_path, dpi=self.options["dpi"])
        else:
            log.fatal(f"Option <plot_to> is wrong with '{self.options['plot_to']}', expected 'console' or 'file'.")
    
        # Clear the current figure
        plt.clf()
        
        
    def plot_subplots(
        self,
        x_array: np.ndarray,
        y_arrays: List[np.ndarray],
        xlabel: str,
        ylabels: List[str],
        x_unit: str = "",
        y_units: Union[List[str], None] = None,
        colors: Union[List[str], None] = None,
        figure_path: str = "plot_subplot.png",
        subtitles: Union[List[List[str]], None] = None,
        options: Dict[str, Any] = None,
        events: Union[Dict[str, List[Any]], None] = None,
    ) -> None:
        """Generate subplots with one column
    
        The subplot has only one column. The number of rows is defined via the chosen number of y-axis data. Depending
        on the dimension of the y-axis several plots can be plotted in one subplot. For example:
            y_arrays = [np.array([1,2,3,4,5]), ...]     # ndim=1, only one plot plotted
            y_arrays = [ np.array(                      # ndim=2, 2 plots plotted in one subplot
                            [1,2,3,4,5],
                            [6,7,8,9,10]), ...]              
            y_arrays = [ np.array(                      # ndim=2, 3 plots plotted in one subplot
                            [1,2,3,4,5],
                            [6,7,8,9,10],
                            [11,12,13,14,15]), ...]   
                                                                                  
        Following **options** options can be overwritten:
    
        | Option             | Value            | Description                                                             |
        |--------------------|------------------|-------------------------------------------------------------------------|
        | colormap           | <type>           | Color map type for plotting events (e.g. viridis, jet, tab10, rainbow,  |
        |                    |                  | hsv, plasma)                                                            |
        | dpi                | <num>            | Resolution of file in dots per inch                                     |
        | figsize            | (num, num)       | Figure size given by (width, height) in inches                          |
        | fsize_subtitle     | <num>            | Fontsize of subplot title (statistical information)                     |
        | grid               | <True|False>     | Plot grid                                                               |
        | histogram          | <x, y>           | Plot x-axis histogram on top, y-axis histogram on right or for both     |
        |                    |                  | axis on scatter plot                                                    |
        | histogram_binwidth | <num>            | Histogram bin width                                                     |
        | histogram_size     | <num>            | Histogram y-axis size                                                   |
        | legend             | <True|False>     | Plot legend                                                             |
        | legend_location    | <right, bottom>  | Legend location                                                         |
        | legend_ncol        | <num>            | The number of legend columns                                            |
        | marker             | <'.'|'-'>        | Marker type                                                             |
        | plot_to            | <console|file>   | Plot figure on console or file                                          |
        | plot_type          | <scatter|plot>   | Choose either "scatter" or "plot" type                                  |
        | reg_line           | <True|False>     | Regression line flag                                                    |
        | sharex             | <True|False>     | Share x-axis                                                            |
        | sharey             | <True|False>     | Share y-axis                                                            |
        | statistic          | <rms, mean, ...> | Plot statistical information. Following function can be defined: 'max', |
        |                    |                  | 'mean', 'min', 'rms', 'std', 'percentile' (see function _get_statistic  |
        |                    |                  | for more information)                                                   |
        | tick_labelsize     | <(axis, size)>   | Change label size of x- and y-axis tick labels. This can be done either |
        |                    |                  | for x-axis, y-axis or both axis via specifying 'x', 'y' or both'.       |
        | title              | <text>           | Main title of subplots                                                  |
        | xlim               | <[num, num]|     | Define x-axis limit by defining a list with [left, right] range. If     |
        |                    |  auto>]          | xlim=auto, then x-axis limit is automatically chosen                    |
        | xticks             | <[num, ...]>     | Define x-axis ticks by defining a list with ticks                       |
        | xticklabels        | <[text, ...]>    | Define x-axis ticks labels by defining a list with labels               |
        | ylim               | <[num, num]>     | Define y-axis limit by defining a list with [bottom, top] range         |
        | yticks             | <[num, ...]>     | Define y-axis ticks by defining a list with ticks                       |
        | yticklabels        | <[text, ...]>    | Define y-axis ticks labels by defining a list with labels               |
    
        Args:
           x_array:        Array with x-axis data to plot.
           y_arrays:       List of arrays with y-axis data to plot. 
           xlabel:         X-axis label.
           ylabels:        List with y-axis labels. It should corresponds to given number of y-axis arrays.
           x_unit:         X-axis unit.
           y_units:        List with y-axis units. It should corresponds to given number of y-axis arrays. 
           colors:         List with colors for each plot. It should corresponds to given number of y-axis arrays. 
           figure_path:    Figure path.
           options:        Dictionary with options, which overwrite default plot configuration.
           subtitles:      List with title for each subplot. It should corresponds to given number of y-axis arrays.
           events:         Dictionary with event labels as key and lists of events as value. The events has to be related to
                           x-axis data. Event colors are automatically chosen based on 'colormap'. 
        """

        # Overwrite options with argument definition
        if options:
            self.set_options(options)  
    
        # Generate subplot
        fig, axes = plt.subplots(
            nrows=len(y_arrays), 
            ncols=1, 
            sharex=self.options["sharex"], 
            sharey=self.options["sharey"], 
            figsize=self.options["figsize"],
        )
        fig.suptitle(f"{self.options['title']}", y=1.0)
    
        # Get event and label colors
        if events:
            legend_labels, cmap = self._get_label_color(len(events), cmap=self.options["colormap"])
    
        if colors is None:
            if y_arrays[0].ndim == 2:
                colors = np.full((len(y_arrays), y_arrays[0].shape[0]), None)
            else:
                colors =  np.full((1, len(y_arrays)), None)
      
        if y_units is None:
            y_units = [None for ii in range(0, len(y_arrays))]

        if subtitles is None:
            subtitles = [list() for ii in range(0, len(y_arrays))]
    
        # Make 'axes' iterable (needed for 'zip')
        if not isinstance(axes, np.ndarray):
            axes = np.array([axes])
    
        # Plot each subplot row
        for ax, y_array, ylabel, color, y_unit, subtitle in zip(axes, y_arrays, ylabels, colors, y_units, subtitles):

            if y_array.ndim == 2:
                for row in range(0, y_array.shape[0]):
                    self.plot_subplot_row(
                            ax, 
                            x_array, 
                            y_array[row,:], 
                            xlabel, 
                            ylabel, 
                            x_unit=x_unit, 
                            y_unit=y_unit, 
                            color=color[row],
                            subtitle=subtitle,
                            options=self.options, 
                    )                                     

            else:
                self.plot_subplot_row(
                        ax, 
                        x_array, 
                        y_array, 
                        xlabel, 
                        ylabel, 
                        x_unit=x_unit, 
                        y_unit=y_unit, 
                        color=color,
                        subtitle=subtitle,
                        options=self.options, 
                ) 
    
            # Plot vertical line for events in each subplot
            if events:
                for idx, (label, entries) in enumerate(sorted(events.items())):
                    [ax.axvline(x=e, label=label, color=cmap(idx)) for e in entries]
    
        # Change tick labelsize
        if self.options["tick_labelsize"]:
            ax.tick_params(axis=self.options["tick_labelsize"][0], labelsize=self.options["tick_labelsize"][1])
    
        # Plot x-axis label only once below the last subplot row
        ax.set(xlabel=xlabel)
    
        # Plot event legend
        if events:
            self.options["legend_location"] = "bottom" if self.options["legend_location"] == None else self.options["legend_location"]
            self._plot_legend(legend_labels, labels=events.keys())
    
        # Rotates and right aligns the x labels, and moves the bottom of the axes up to make room for them
        if isinstance(x_array[0], datetime):
            fig.autofmt_xdate()
    
        # Automatically adjusts subplot params so that the subplot(s) fits in to the figure area
        fig.tight_layout()
    
        # Adjust plot axes (to place title correctly)
        fig.subplots_adjust(top=0.92)
    
        # Save plot as file or show it on console
        if self.options["plot_to"] == "console":
            plt.show()
        elif self.options["plot_to"] == "file":
            plt.savefig(figure_path, dpi=self.options["dpi"])
        else:
            log.fatal(f"Option <plot_to> is wrong with '{self.options['plot_to']}', expected 'console' or 'file'.")
    
        # Clear the current figure
        plt.clf()
    
    
    def plot_subplot_row(
        self,
        ax: "AxesSubplot",
        x_array: np.ndarray,
        y_array: np.ndarray,
        xlabel: str = "",
        ylabel: str = "",
        x_unit: str = "",
        y_unit: str = "",
        label: str = "",
        color: Union[None, np.ndarray] = None,
        subtitle: List[str] = [],
        options: Dict[str, Any] = None,
    ) -> None:
        """Generate single row of plot subplot
    
        Following **options** options can be overwritten:
    
        | Option             | Value            | Description                                                             |
        |--------------------|------------------|-------------------------------------------------------------------------|
        | alpha              | <num>            | Blending values of markers (0: transparent, 1: opaque)                  |
        | fsize_subtitle     | <num>            | Fontsize of subplot title (statistical information)                     |
        | grid               | <True|False>     | Plot grid                                                               |
        | histogram          | <x, y>           | Plot x-axis histogram on top, y-axis histogram on right or for both     |
        |                    |                  | axis on scatter plot                                                    |
        | histogram_binwidth | <num>            | Histogram bin width                                                     |
        | histogram_size     | <num>            | Histogram y-axis size                                                   |
        | linestyle          | <style>          | Line style for plot type (e.g. 'solid', 'dashed')                       |
        | marker             | <'.'|'-'>        | Marker type                                                             |
        | markersize         | <num>            | Marker size                                                             |
        | plot_type          | <scatter|plot>   | Choose either "scatter" or "plot" type                                  |
        | reg_line           | <True|False>     | Regression line flag                                                    |
        | statistic          | <rms, mean, ...> | Plot statistical information. Following function can be defined: 'rms', |
        |                    |                  | 'mean', 'min', 'max', 'std', 'percentile' (see function get_statistic   |
        |                    |                  | for more information)                                                   |
        | xlim               | <[num, num]|     | Define x-axis limit by defining a list with [left, right] range. If     |
        |                    |  auto>]          | xlim=auto, then x-axis limit is automatically chosen                    |
        | xticks             | <[num, ...]>     | Define x-axis ticks by defining a list with ticks                       |
        | xticklabels        | <[text, ...]>    | Define x-axis ticks labels by defining a list with labels               |
        | ylim               | <[num, num]>     | Define y-axis limit by defining a list with [bottom, top] range         |
        | yticks             | <[num, ...]>     | Define y-axis ticks by defining a list with ticks                       |
        | yticklabels        | <[text, ...]>    | Define y-axis ticks labels by defining a list with labels               |
    
        Args:
           ax:             Axes object needed for plotting subplot row.
           x_array:        Array with x-axis data to plot.
           y_array:        Array with y-axis data to plot.
           xlabel:         X-axis label.
           ylabels:        X-axis label.
           x_unit:         X-axis unit.
           y_unit:         Y-axis unit.
           label:          Legend label.
           color:          Marker color.
           subtitle:       List with element of subplot title.
           options:        Dictionary with options, which overwrite default plot configuration.
        """
    
        # Overwrite options with argument definition
        if options:
            self.set_options(options)  
    
        if self.options["plot_type"] == "scatter":
            import matplotlib
            matplotlib.rcParams["markers.fillstyle"] = "none"  # markers are not filled
            matplotlib.rcParams["lines.markeredgewidth"] = 0.0  # no marker edges plotted
    
        # Configure labels
        unit = f"[{y_unit}]" if y_unit else ""
        ax.set(ylabel=f"{ylabel} {unit}")
    
        # Plot linear regression line
        if self.options["reg_line"]:       
            lr = LinearRegression(x_array, y_array)
    
            # Update subtitle of plots
            rate_unit = f"{Unit(y_unit).units:~P}/{Unit(x_unit).units:~P}"  # get abbreviated SI units
            rms_unit = f"{Unit(y_unit).units:~P}"  # get abbreviated SI units
            width = ".1f" if ("mm" == y_unit or "millimeter" == y_unit) else ".3f"
            subtitle.append(f"Rate: {lr.slope:{width}} {rate_unit}, RMS: {lr.rms:{width}} {rms_unit}, R^2: {lr.r_square:.2f}")
            if "rms" in self.options["statistic"]:
                self.options["statistic"].remove("rms")
    
            # Plot regression line
            ax.plot(
                x_array,
                lr.y_modeled,
                alpha=self.options["alpha"],
                color="black",
                label="Regression line",
                linestyle="dashed",
            )
    
        # Generate scatter plot
        if self.options["plot_type"] == "scatter":
            ax.scatter(
                x_array,
                y_array,
                alpha=self.options["alpha"],
                color=color,
                label=label,
                marker=self.options["marker"],
                s=float(self.options["markersize"]),
            )
    
        elif self.options["plot_type"] == "plot":
            ax.plot(
                x_array,
                y_array,
                alpha=self.options["alpha"],
                color=color,
                label=label,
                linestyle=self.options["linestyle"],
                marker=self.options["marker"],
                markersize=self.options["markersize"],
            )
    
        # Set x-axis and y-axis limits, ticks and tick labels
        if not self.options["xlim"] == "auto":
            if self.options["xlim"]:
                ax.set_xlim(self.options["xlim"][0], self.options["xlim"][1])
            else:
                if isinstance(x_array, np.ndarray):
                    if x_array.ndim == 0:
                        x_array = np.expand_dims(x_array, axis=0)
                ax.set_xlim([min(x_array), max(x_array)])
    
        if self.options["ylim"]:
            ax.set_ylim(self.options["ylim"][0], self.options["ylim"][1])
    
        if self.options["xticks"]:
            ax.set_xticks(self.options["xticks"])
    
        if self.options["yticks"]:
            ax.set_yticks(self.options["yticks"])
    
        if self.options["xticklabels"]:
            ax.set_xticklabels(self.options["xticklabels"])
    
        if self.options["yticklabels"]:
            ax.set_yticklabels(self.options["yticklabels"])
    
        # Turn off scientific notation on axis labels
        if isinstance(ax.yaxis.get_major_formatter(), ScalarFormatter):
            ax.yaxis.get_major_formatter().set_scientific(False)
    
        # Add histograms for x- and y-axis
        if self.options["histogram"]:
            self._add_histogram(ax, x_array, y_array)
    
        # Plot grid
        if self.options["grid"]:
            ax.grid(True)
    
        # Plot statistical text line as title over each subplot
        if self.options["statistic"]:
            subtitle.extend(self.get_statistic(y_array, self.options["statistic"], y_unit))
    
        # Plot subtitle of current row
        if subtitle:
            ax.set_title(", ".join(subtitle), fontsize=self.options["fsize_subtitle"], horizontalalignment="center")


    #
    # AUXILIARY FUNCTIONS
    #
    def _add_histogram(
        self,
        ax: "AxesSubplot", 
        x_array: np.ndarray, 
        y_array: np.ndarray, 
        options: Union[Dict[str, Any], None] = None,
    ) -> None:
        """Add histograms to scatter plot
    
        Histograms can be added for the x-axis on top of the scatter plot and for the y-axis on the right side.
    
        Following **options** can be selected:
    
        | Option             | Value            | Description                                                         |
        |--------------------|------------------|---------------------------------------------------------------------|
        | histogram          | <x, y>           | Plot x-axis histogram on top, y-axis histogram on right or for      |
        |                    |                  | both axis on scatter plot                                           |
        | histogram_binwidth | <num>            | Histogram bin width                                                 |
        | histogram_size     | <num>            | Histogram y-axis size                                               |
    
        Args:
           ax:             Axes object needed for plotting subplot row.
           x_array:        Array with x-axis data to plot.
           y_array:        Array with y-axis data to plot.
           options:        Dictionary with options, which overwrite default plot configuration.
        """
       
        # Overwrite options with argument definition
        if options:
            self.set_options(options) 
    
        histogram = self.options["histogram"].replace(",", " ").split()
    
        # ax.set_aspect(1.)
    
        # Determine histogram axis limits
        binwidth = self.options["histogram_binwidth"]
        xymax = (
            np.nanmax(np.abs(y_array))
            if isinstance(x_array[0], datetime)
            else np.nanmax([np.nanmax(np.abs(x_array)), np.nanmax(np.abs(y_array))])
        )
        lim = (int(xymax / binwidth) + 1) * binwidth
        bins = np.arange(-lim, lim + binwidth, binwidth)
    
        # Create new axes on the top (x-axis) and on the right (y-axis) of the current axes
        divider = make_axes_locatable(ax)
        if "x" in histogram:
            ax_histx = divider.append_axes(position="top", size=self.options["histogram_size"], pad=0.1, sharex=ax)
            ax_histx.xaxis.set_tick_params(labelbottom=False)  # make some label invisible
            ax_histx.hist(x_array, bins=bins)
            ax_histx.set_ylabel("Counts")
    
        if "y" in histogram:
            ax_histy = divider.append_axes(position="right", size=self.options["histogram_size"], pad=0.1, sharey=ax)
            ax_histy.yaxis.set_tick_params(labelleft=False)  # make some label invisible
            ax_histy.hist(y_array, bins=bins, orientation="horizontal")
            ax_histy.set_xlabel("Counts")
    
    
    def _get_label_color(
        self,
        num_labels: Dict[str, List[Any]], 
        colors: Union[List[str], None] = None, 
        cmap: str = "tab20",
    ) -> Tuple[List["Line2D"], "ListedColormap"]:
        """Define colours for labels
    
        A color map is generated for given number of labels. If 'colors' is defined, then this color definition overwrites
        automatically generated color map.
    
        Args:
            num_labels:  Number of labels
            colors:      List with defined colors
            cmap:        Colour map name
    
        Returns: 
            Tuple with legend labels to plot and listed colour map
        """
        cmap = ListedColormap(colors) if colors else plt.get_cmap(cmap, lut=num_labels)
        legend_labels = list()
        for idx in range(0, num_labels):
            legend_labels.append(Line2D([0], [0], color=cmap(idx), linewidth="3"))
    
        return legend_labels, cmap
    
    
    def _plot_legend(
            self,
            legend_labels: List["matplotlib.lines.Line2D"], 
            labels: List[str], 
    ) -> None:
        """Plot legend to defined location
    
        Args:
            legend_labels:  List with of handles.
            labels:         List with labels for each plot.
        """
    
        # General definition of legend location
        legend_loc = {
            "bottom": {"bbox_to_anchor": (0.5, -0.3), "borderaxespad": 0.0, "loc": "upper center"},
            "right": {"bbox_to_anchor": (1.04, 1), "borderaxespad": 0.0, "loc": "upper left"},
        }
    
        plt.legend(
            legend_labels,
            labels,
            bbox_to_anchor=legend_loc[self.options["legend_location"]]["bbox_to_anchor"],
            loc=legend_loc[self.options["legend_location"]]["loc"],
            borderaxespad=legend_loc[self.options["legend_location"]]["borderaxespad"],
            ncol=self.options["legend_ncol"],
        )
    
    
    def _ordered_set(self, array: List[str]) -> List[str]:
        """Generate unique set ordered by adding first occurence of a item
        """
        from collections import OrderedDict
    
        return OrderedDict.fromkeys(array).keys()
