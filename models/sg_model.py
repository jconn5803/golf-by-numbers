import pandas as pd
from scipy.interpolate import interp1d
import numpy as np
import os

def expected_shots_calc(distance_from_hole, lie):
    """This model calculates the expected number of strokes to hole out from specified position
    """
    
    if lie == "In the Hole":
        return 0
    # Load in the expected strokes df
    # Build the file path dynamically based on the current file location
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "strokes_gained_benchmark.csv")
    expected_df = pd.read_csv(data_path)
    # Only store the lie we are interested in
    expected_df = expected_df[expected_df["lie"] == f"{lie}"]

    # Set up the x and y values for linear interpolation model
    x_array = expected_df["distance"].values
    y_array = expected_df["average_shots"].values
    # Creates linear interpolation model
    model = interp1d(x_array, y_array)

    #Return expected number of strokes from the model
    return model(distance_from_hole)

def SG_calculator(distance_before, lie_before, distance_after, lie_after):
    """ This function calculates strokes gained for a shot
    """
    if lie_after == "OOB":
        return  -2

    # Calculates current position expected strokes
    expected_before = expected_shots_calc(distance_before, lie_before)
    # Calculate expected number of strokes from position ball hit to
    expected_after = expected_shots_calc(distance_after, lie_after)

    return round(expected_before - expected_after - 1, 2) # Round to 2dp

def shot_type_func(lie, distance, par):
    """This function categorises the current shot based upon the lie, distance and hole par"""

    # Define Putting Category
    if lie == "Green":
        return "Putting"
    
    # Define the off the Tee category
    elif lie == "Tee" and par == 3:
        return "Approach" # Tee shots on Par 3s are approach shots
    
    elif lie == "Tee":
        return "Off the Tee"
    
    # Define the short game category
    elif distance < 50 and lie != "Green":
        return "Around the Green"
    
    # All other shots should be approach by default    
    else:
        return "Approach"
    

