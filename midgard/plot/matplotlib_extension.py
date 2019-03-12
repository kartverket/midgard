# Standard library imports
from typing import Any, Dict, List, Tuple, Union

# External library imports
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np

# Midgard imports
from midgard.math.unit import Unit


def _plot_regression_line(ax: "AxesSubplot", x_data: "ndarray", y_data: "ndarray") -> Tuple[float, float]:
    """Plot linear regression line

    Args:
        ax:      Axes object needed for plotting regression line.
        x_data:  Array with x-axis data
        y_data:  Array with y-axis data

    Returns:
        Tuple with rate and y-axis offset
    """
    fit = np.polyfit(x_data, y_data, 1)
    fit_fn = np.poly1d(fit)  # fit_fn is a function which takes in x_data and returns an estimate for y_data
    ax.plot(x_data, y_data, "yo", x_data, fit_fn(x_data), "--k")

    # Other solution
    # from sklearn.linear_model import LinearRegression
    # linear_regressor = LinearRegression()  # create object for the class
    # linear_regressor.fit(x_array, y_arrays[0])  # perform linear regression
    # reg_line = linear_regressor.predict(x_array) # make predictions

    return fit[0], fit[1]


# TODO: Distinguish between _get_statistic and _get_statistic_text
def get_statistic(
    data: "ndarray", funcs: List[str] = ["rms", "mean", "std", "min", "max", "percentile"], unit: str = ""
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
    func_def = {"max": ("Max", np.max), "min": ("Min", np.min), "mean": ("Mean", np.mean), "std": ("Std", np.std)}

    if "rms" in funcs:
        rms = lambda x: np.sqrt(np.mean(np.square(x)))
        func_def.update({"rms": ("RMS", rms)})

    if "percentile" in funcs:
        percentile = lambda x: np.percentile(x, 95)
        func_def.update({"percentile": ("95th perc.", percentile)})

    # Generate statistical text string
    for func in funcs:
        stat = np.apply_along_axis(func_def[func][1], 0, data)
        stats.append(f"{func_def[func][0]}: {stat:.2f} {Unit(unit).units:~P}")  # with abbreviated SI unit

    return stats


def plot_scatter_subplots(
    x_array: "ndarray",
    y_arrays: List["ndarray"],
    xlabel: str,
    ylabels: List[str],
    x_unit: str = "",
    y_unit: str = "",
    figure_path: str = "plot_scatter_subplot.png",
    opt_args: Union[Dict[str, Any], None] = None,
    events: Union[Tuple[Any, str, str], None] = None,  # TODO: description
) -> None:
    """Generate scatter subplot

    The subplot has only one column. The number of rows is defined via the chosen number of y-axis data.

    Example:

    Following **opt_arg** options can be selected:

    | Option         | Value            | Description                                                                |
    |----------------|------------------|----------------------------------------------------------------------------|
    | dpi            | <num>            | Resolution of file in dots per inch                                        |
    | figsize        | (num, num)       | Figure size                                                                |
    | fsize_subtitle | <num>            | Fontsize of subplot title (statistical information)                        |
    | marker         | <'.'|'-'>        | Marker type                                                                |
    | plot_to        | <console|file>   | Plot figure on console or file                                             |
    | reg_line       | <True|False>     | Regression line flag                                                       |
    | sharex         | <True|False>     | Share x-axis                                                               |
    | sharey         | <True|False>     | Share y-axis                                                               |
    | statistic      | <rms, mean, ...> | Plot statistical information. Following function can be defined: 'max',    |
    |                |                  | 'mean', 'min', 'rms', 'std', 'percentile' (see function _get_statistic for |
    |                |                  | more information)                                                          |
    | title          | <text>           | Main title of subplots                                                     |

    Args:
       x_array:        Array with x-axis data to plot.
       y_arrays:       List of arrays with y-axis data to plot.
       xlabel:         X-axis label.
       ylabels:        List with y-axis labels. It should corresponds to given number of y-axis arrays.
       x_unit:         X-axis unit.
       y_unit:         Y-axis unit.
       figure_path:    Figure path.
       opt_args:       Dictionary with options, which overwrite default plot configuration.
    """

    # Define plotting options
    options = {
        "dpi": 200,
        "figsize": (6, 8),
        "fsize_subtitle": 8,
        "marker": ".",
        "legend": False,
        "plot_to": "console",
        "reg_line": False,
        "sharex": True,
        "sharey": True,
        "statistic": ["rms", "mean", "std", "min", "max", "percentile"],
        "title": "",
    }

    # Overwrite options with argument definition
    if opt_args:
        options.update(opt_args)

    # Generate subplot
    fig, axes = plt.subplots(
        len(ylabels), 1, sharex=options["sharex"], sharey=options["sharey"], figsize=options["figsize"]
    )
    fig.suptitle(f"{options['title']}", y=1.0)

    # Get label colors for events
    if events:
        custom_lines, cmap = _get_label_color(events)

    # Plot each subplot row
    for ax, y_array, ylabel in zip(axes, y_arrays, ylabels):

        plot_scatter_subplot_row(ax, x_array, y_array, xlabel, ylabel, x_unit=x_unit, y_unit=y_unit, opt_args=options)

        # Plot vertical line for events in each subplot
        if events:
            for idx, (label, entries) in enumerate(sorted(events.items())):
                [ax.axvline(x=e, label=label, color=cmap(idx)) for e in entries]

    # Plot x-axis label only once below the last subplot row
    ax.set(xlabel=xlabel)

    # Plot event legend
    if events:
        plt.legend(custom_lines, sorted(events.keys()), bbox_to_anchor=(1.0, -0.4), loc=1, borderaxespad=0.0, ncol=3)

    # Rotates and right aligns the x labels, and moves the bottom of the axes up to make room for them
    fig.autofmt_xdate()

    # Automatically adjusts subplot params so that the subplot(s) fits in to the figure area
    fig.tight_layout()

    # Adjust plot axes (to place title correctly)
    fig.subplots_adjust(top=0.95)

    # Save plot as file or show it on console
    if options["plot_to"] == "console":
        plt.show()
    elif options["plot_to"] == "file":
        plt.savefig(figure_path, dpi=options["dpi"])
    else:
        log.fatal(f"Option <plot_to> is wrong with '{options['plot_to']}', expected 'console' or 'file'.")

    # Clear the current figure
    plt.clf()


def _get_label_color(labels, cmap="tab10"):
    # TODO: description
    cmap = plt.get_cmap(cmap)
    custom_lines = list()
    for idx in range(0, len(labels)):
        custom_lines.append(Line2D([0], [0], color=cmap(idx)))

    return custom_lines, cmap


def plot_scatter_subplot_row(
    ax: "AxesSubplot",
    x_array: "ndarray",
    y_array: "ndarray",
    xlabel: str = "",
    ylabel: str = "",
    x_unit: str = "",
    y_unit: str = "",
    label: str = "",
    color: Union[None, "ndarray"] = None,
    opt_args: Union[Dict[str, Any], None] = None,
) -> None:
    """Generate single row of scatter subplot

    Example:

    Following **options** can be selected:

    | Option         | Value            | Description                                                                |
    |----------------|------------------|----------------------------------------------------------------------------|
    | alpha          | <num>            | Blending values of markers (0: transparent, 1: opaque)                     |
    | fsize_subtitle | <num>            | Fontsize of subplot title (statistical information)                        |
    | marker         | <'.'|'-'>        | Marker type                                                                |
    | markersize     | <num>            | Marker size                                                                |
    | reg_line       | <True|False>     | Regression line flag                                                       |
    | statistic      | <rms, mean, ...> | Plot statistical information. Following function can be defined: 'max',    |
    |                |                  | 'mean', 'min', 'rms', 'std', 'percentile' (see function get_statistic for  |
    |                |                  | more information)                                                          |

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
       opt_args:       Dictionary with options, which overwrite default plot configuration.
    """
    subtitle = list()

    # Define plotting options
    options = {
        "alpha": 1,
        "fsize_subtitle": 8,
        "marker": ".",
        "markersize": 9,
        "reg_line": False,
        "statistic": ["rms", "mean", "std", "min", "max", "percentile"],
    }

    # Overwrite options with argument definition
    if opt_args:
        options.update(opt_args)

    # Configure labels
    unit = f"[{y_unit}]" if y_unit else ""
    ax.set(ylabel=f"{ylabel} {unit}")
    ax.set_xlim([min(x_array), max(x_array)])

    # Generate scatter plot
    ax.scatter(
        x_array,
        y_array,
        alpha=options["alpha"],
        color=color,
        label=label,
        marker=options["marker"],
        s=options["markersize"],
    )

    # Plot linear regression line
    if options["reg_line"]:
        unit = f"{Unit(y_unit).units:~P}/{Unit(x_unit).units:~P}"  # get abbreviated SI units
        rate, _ = _plot_regression_line(ax, x_array, y_array)
        subtitle.append(f"Rate: {rate:.3f} {unit}")

    # Plot statistical text line as title over each subplot
    if options["statistic"]:
        subtitle.extend(get_statistic(y_array, options["statistic"], y_unit))

    # Plot subtitle of current row
    if subtitle:
        ax.set_title(", ".join(subtitle), fontsize=options["fsize_subtitle"], horizontalalignment="center")
