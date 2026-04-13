from utils.helpers import apply_gap, is_similar
from core.coordinate_calculator import calculate_window_position

def determine_next_mode(current_mode, relative_bounds, screen_size, gap):
    """
    Determines the next mode for cycling based on current window position and mode.
    """
    next_mode = current_mode
    
    if current_mode == "left_half":
        half_bounds = apply_gap(*calculate_window_position(screen_size, "left_half"), gap)
        third_bounds = apply_gap(*calculate_window_position(screen_size, "left_1/3"), gap)
        if is_similar(relative_bounds, half_bounds): 
            next_mode = "left_1/3"
        elif is_similar(relative_bounds, third_bounds): 
            next_mode = "left_2/3"
            
    elif current_mode == "right_half":
        half_bounds = apply_gap(*calculate_window_position(screen_size, "right_half"), gap)
        third_bounds = apply_gap(*calculate_window_position(screen_size, "right_1/3"), gap)
        if is_similar(relative_bounds, half_bounds): 
            next_mode = "right_1/3"
        elif is_similar(relative_bounds, third_bounds): 
            next_mode = "right_2/3"
            
    return next_mode
