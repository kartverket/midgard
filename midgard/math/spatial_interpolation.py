"""Methods for spatial interpolation in numpy arrays

Description:
------------



Example:
--------

TODO

"""


# Third party imports
import numpy as np
from scipy.interpolate import griddata


def interpolate_for_position(
                    grid_x: np.ndarray, 
                    grid_y: np.ndarray, 
                    values: np.ndarray, 
                    x: float,
                    y: float, 
                    method: str="linear"
) -> float:
    """Interpolation in grid with size (n, m) for a given position
    
    Interpolation is based on scipy.interpolate.griddata module. More information about this module can be found under:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html
    
    Args:
        grid_x: (n,m) Array with x-positions for each grid point 
        grid_y: (n,m) Array with y-positions for each grid point 
        values: (n,m) Array with data values for each grid point
        x:            x-position
        y:            y-position
        method: Method of interpolation:
                    linear:  tessellate the input point set to N-D simplices, and interpolate linearly on each simplex
                    nearest: value of data point closest to the point of interpolation
                    cubic:   value determined from a piecewise cubic
                    
    Returns:
        Interpolated value in data grid for a given position
    """
    if x < grid_x[0][0] or x > grid_x[0][-1]:
        raise ValueError(f"Given x-position {x:.3f} exceeds grid x-position boundaries [left: {grid_x[0][0]:.3f}, right: {grid_x[0][-1]:.3f}]")

    if y < grid_y[-1][0] or y > grid_y[0][0]:
        raise ValueError(f"Given y-position {y:.3f} exceeds grid y-position boundaries [left: {grid_y[0][0]:.3f}, right: {grid_y[0][-1]:.3f}]")
    
    grid_points = np.array([grid_x.flatten(), grid_y.flatten()]).T
    
    return griddata(grid_points, values.flatten(), (x, y), method=method)
