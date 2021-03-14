# midgard.plot


## midgard.plot.matplotext
Matplotlib extension class

**Description:**

Wrapper functions around matplotlib subroutines are defined in this class.



### **MatPlotExt**

Full name: `midgard.plot.matplotext.MatPlotExt`

Signature: `(options: Dict[str, Any] = None) -> None`

Class for plotting - Extension of matplotlib


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


## midgard.plot.matplotlib_extension
Matplotlib extension library

**Description:**

Wrapper functions around matplotlib subroutines are defined in this library.



### **get_statistic**()

Full name: `midgard.plot.matplotlib_extension.get_statistic`

Signature: `(data: numpy.ndarray, funcs: List[str] = ['rms', 'mean', 'std', 'min', 'max', 'percentile'], unit: str = '') -> List[str]`

Get text string with statistical information

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

**Returns:**

List with strings representing statistical information


### **plot**()

Full name: `midgard.plot.matplotlib_extension.plot`

Signature: `(x_arrays: List[numpy.ndarray], y_arrays: List[numpy.ndarray], xlabel: str = '', ylabel: str = '', x_unit: str = '', y_unit: str = '', colors: Union[List[str], NoneType] = None, labels: Union[List[str], NoneType] = None, figure_path: str = 'plot_scatter.png', opt_args: Dict[str, Any] = {}, events: Union[Dict[str, List[Any]], NoneType] = None) -> None`

Generate scatter/plot plot

Several scatter/plot plots can be plotted on one plot. This is defined via the chosen number of y_arrays data.
Histogram is only plotted for the last given y-array in "y_arrays".

Following **opt_arg** options can be selected:

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

**Args:**

   x_arrays:       List of arrays with x-axis data to plot.
   y_arrays:       List of arrays with y-axis data to plot.
   xlabel:         X-axis label.
   ylabel:         Y-axis label. 
   x_unit:         X-axis unit.
   y_unit:         Y-axis unit.
   colors:         List with colors for each plot. It should corresponds to given number of y-axis arrays. 
                   Overwrites automatically chosen 'events'/'labels' colors.
   labels:         List with labels for each plot. It should corresponds to given number of y-axis arrays. Label 
                   colors are automatically chosen based on 'colormap'. 'colors' option overwrites automatically
                   chosen label colors. NOTE: 'labels' and 'events' can not be chosen together, either 'labels' or
                   'events' should be defined.
   figure_path:    Figure path.
   opt_args:       Dictionary with options, which overwrite default plot configuration.
   events:         Dictionary with event labels as key and lists of events as value. The events has to be related to
                   x-axis data. Event colors are automatically chosen based on 'colormap'. NOTE: 'labels' and
                   'events' can not be chosen together, either 'labels' or 'events' should be defined.


### **plot_bar_dataframe_columns**()

Full name: `midgard.plot.matplotlib_extension.plot_bar_dataframe_columns`

Signature: `(df: 'Dataframe', column: str, path: pathlib.PosixPath, xlabel: str = '', ylabel: str = '', label: str = 'label', colors: Union[List[str], NoneType] = None, opt_args: Union[Dict[str, Any], NoneType] = None) -> None`

Generate bar plot of given dataframe columns

If 'label' column is given in Dataframe (as 'df.label'), then the bars are color coded based on the defined labels.
In addition a legend is added with information about the labels.

Following **opt_arg** options can be selected:

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

**Args:**

   df:          Dataframe with data to plot.
   column:      Dataframe column to plot.
   path:        Figure path.
   xlabel:      x-axis label.
   ylabel:      y-axis label.
   label:       Dataframe column, which should be used as label.
   colors:      List with colors for defined label in "label" column. This option overwrites automatically chosen 
                colors.
   opt_args:    Dictionary with options, which overwrite default plot configuration.


### **plot_scatter_subplots**()

Full name: `midgard.plot.matplotlib_extension.plot_scatter_subplots`

Signature: `(x_array: numpy.ndarray, y_arrays: List[numpy.ndarray], xlabel: str, ylabels: List[str], x_unit: str = '', y_units: Union[List[str], NoneType] = None, colors: Union[List[str], NoneType] = None, figure_path: str = 'plot_scatter_subplot.png', opt_args: Dict[str, Any] = {}, events: Union[Dict[str, List[Any]], NoneType] = None) -> None`

Generate scatter subplot

The subplot has only one column. The number of rows is defined via the chosen number of y-axis data.

Following **opt_arg** options can be selected:

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

**Args:**

   x_array:        Array with x-axis data to plot.
   y_arrays:       List of arrays with y-axis data to plot.
   xlabel:         X-axis label.
   ylabels:        List with y-axis labels. It should corresponds to given number of y-axis arrays.
   x_unit:         X-axis unit.
   y_units:        List with y-axis units. It should corresponds to given number of y-axis arrays. 
   colors:         List with colors for each plot. It should corresponds to given number of y-axis arrays. 
   figure_path:    Figure path.
   opt_args:       Dictionary with options, which overwrite default plot configuration.
   events:         Dictionary with event labels as key and lists of events as value. The events has to be related to
                   x-axis data. Event colors are automatically chosen based on 'colormap'. 


### **plot_subplot_row**()

Full name: `midgard.plot.matplotlib_extension.plot_subplot_row`

Signature: `(ax: 'AxesSubplot', x_array: numpy.ndarray, y_array: numpy.ndarray, xlabel: str = '', ylabel: str = '', x_unit: str = '', y_unit: str = '', label: str = '', color: Union[NoneType, numpy.ndarray] = None, opt_args: Dict[str, Any] = {}) -> None`

Generate single row of plot subplot

Following **options** can be selected:

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

**Args:**

   ax:             Axes object needed for plotting subplot row.
   x_array:        Array with x-axis data to plot.
   y_array:        Array with y-axis data to plot.
   xlabel:         X-axis label.
   ylabels:        X-axis label.
   x_unit:         X-axis unit.
   y_unit:         Y-axis unit.
   label:          Legend label.
   color:          Marker color.
   opt_args:       Dictionary with options, which overwrite default plot configuration.
