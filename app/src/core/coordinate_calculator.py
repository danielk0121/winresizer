def calculate_window_position(screen_size, mode, gap=0):
    """
    Calculates window bounds (x, y, w, h) based on screen size, mode, and gap.
    """
    screen_width, screen_height = screen_size

    # 1/2 splits
    if mode == "left_half":
        return (gap, gap, screen_width // 2 - (gap * 1.5), screen_height - (gap * 2))
    if mode == "right_half":
        return (screen_width // 2 + (gap * 0.5), gap, screen_width // 2 - (gap * 1.5), screen_height - (gap * 2))
    if mode == "top_half":
        return (gap, gap, screen_width - (gap * 2), screen_height // 2 - (gap * 1.5))
    if mode == "bottom_half":
        return (gap, screen_height // 2 + (gap * 0.5), screen_width - (gap * 2), screen_height // 2 - (gap * 1.5))

    # 1/4 splits
    if mode == "top_left_1/4":
        return (gap, gap, screen_width // 2 - (gap * 1.5), screen_height // 2 - (gap * 1.5))
    if mode == "top_right_1/4":
        return (screen_width // 2 + (gap * 0.5), gap, screen_width // 2 - (gap * 1.5), screen_height // 2 - (gap * 1.5))
    if mode == "bottom_left_1/4":
        return (gap, screen_height // 2 + (gap * 0.5), screen_width // 2 - (gap * 1.5), screen_height // 2 - (gap * 1.5))
    if mode == "bottom_right_1/4":
        return (screen_width // 2 + (gap * 0.5), screen_height // 2 + (gap * 0.5), screen_width // 2 - (gap * 1.5), screen_height // 2 - (gap * 1.5))

    # 1/3 and 2/3 splits
    unit_w = screen_width // 3
    if mode == "left_1/3":
        return (gap, gap, unit_w - (gap * 1.5), screen_height - (gap * 2))
    if mode == "center_1/3":
        return (unit_w + (gap * 0.5), gap, unit_w - (gap * 1.0), screen_height - (gap * 2))
    if mode == "right_1/3":
        return (2 * unit_w + (gap * 0.5), gap, unit_w - (gap * 1.5), screen_height - (gap * 2))

    if mode == "left_2/3":
        return (gap, gap, 2 * unit_w - (gap * 1.0), screen_height - (gap * 2))
    if mode == "right_2/3":
        return (unit_w + (gap * 0.5), gap, 2 * unit_w - (gap * 1.0), screen_height - (gap * 2))
    
    # Maximize
    if mode == "maximize":
        return (gap, gap, screen_width - (gap * 2), screen_height - (gap * 2))

    # Custom ratio: left_custom:N, right_custom:N, top_custom:N, bottom_custom:N
    if "_custom:" in mode:
        direction, pct_str = mode.split("_custom:")
        pct = int(pct_str) / 100
        if direction == "left":
            return (gap, gap, screen_width * pct - gap * 2, screen_height - gap * 2)
        if direction == "right":
            start_x = screen_width * (1 - pct)
            return (start_x + gap, gap, screen_width * pct - gap * 2, screen_height - gap * 2)
        if direction == "top":
            return (gap, gap, screen_width - gap * 2, screen_height * pct - gap * 2)
        if direction == "bottom":
            start_y = screen_height * (1 - pct)
            return (gap, start_y + gap, screen_width - gap * 2, screen_height * pct - gap * 2)

    return (gap, gap, screen_width - (gap * 2), screen_height - (gap * 2))
