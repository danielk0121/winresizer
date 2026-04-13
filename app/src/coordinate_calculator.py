def calculate_window_position(screen_size, mode):
    """
    주어진 화면 크기와 모드에 따라 창의 위치와 크기(x, y, w, h)를 반환합니다.
    """
    screen_width, screen_height = screen_size

    # 1/2 분할 (절반)
    if mode == "좌측_절반":
        return (0, 0, screen_width // 2, screen_height)
    if mode == "우측_절반":
        return (screen_width // 2, 0, screen_width // 2, screen_height)
    if mode == "위쪽_절반":
        return (0, 0, screen_width, screen_height // 2)
    if mode == "아래쪽_절반":
        return (0, screen_height // 2, screen_width, screen_height // 2)

    # 1/3 분할
    if mode == "좌측_1/3":
        return (0, 0, screen_width // 3, screen_height)
    if mode == "중앙_1/3":
        return (screen_width // 3, 0, screen_width // 3, screen_height)
    if mode == "우측_1/3":
        return (2 * (screen_width // 3), 0, screen_width // 3, screen_height)

    # 2/3 분할
    if mode == "좌측_2/3":
        return (0, 0, 2 * (screen_width // 3), screen_height)
    if mode == "우측_2/3":
        return (screen_width // 3, 0, 2 * (screen_width // 3), screen_height)
    
    # 기타 고정 모드
    if mode == "중앙_고정":
        window_width, window_height = 1200, 800
        x = max(0, (screen_width - window_width) // 2)
        y = max(0, (screen_height - window_height) // 2)
        return (x, y, window_width, window_height)
    
    if mode == "최대화":
        return (0, 0, screen_width, screen_height)
    
    return (0, 0, screen_width, screen_height)
