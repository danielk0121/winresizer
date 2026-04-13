def calculate_window_position(screen_size, mode):
    """
    주어진 화면 크기와 모드에 따라 창의 위치와 크기(x, y, w, h)를 반환합니다.
    """
    screen_width, screen_height = screen_size

    if mode == "좌측_절반":
        return (0, 0, screen_width // 2, screen_height)
    
    if mode == "우측_절반":
        return (screen_width // 2, 0, screen_width // 2, screen_height)
    
    if mode == "중앙_고정":
        # 1200x800 해상도 중앙 배치 (기본값)
        window_width, window_height = 1200, 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        return (x, y, window_width, window_height)
    
    return (0, 0, screen_width, screen_height)
