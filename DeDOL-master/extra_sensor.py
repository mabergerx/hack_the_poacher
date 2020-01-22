import numpy as np

def extra_sensor_pa(pa_loc, po_loc, ani_den, row_num, column_num):
    """
    This function implements the extra sensor data for the ranger, it needs to return an array with shape (row_num, column_num) the return value. An example can be found in env.py/observation_grid
    """
    return np.zeros((row_num, column_num))

def extra_sensor_po(po_loc, pa_loc, ani_den, row_num, column_num):
    """
    This function implements the extra sensor data for the ranger, it needs to return an array with shape (row_num, column_num) the return value. An example can be found in env.py/observation_grid
    """
    return np.zeros((row_num, column_num))