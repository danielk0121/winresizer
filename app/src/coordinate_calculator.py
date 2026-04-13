def calculate_window_position(screen_size, mode, gap=0):
    """
    주어진 화면 크기, 모드, 그리고 간격(gap)에 따라 창의 위치와 크기(x, y, w, h)를 반환합니다.
    """
    screen_width, screen_height = screen_size

    # 1/2 분할 (절반)
    if mode == "좌측_절반":
        return (gap, gap, screen_width // 2 - (gap * 1.5), screen_height - (gap * 2))
    if mode == "우측_절반":
        return (screen_width // 2 + (gap * 0.5), gap, screen_width // 2 - (gap * 1.5), screen_height - (gap * 2))
    if mode == "위쪽_절반":
        return (gap, gap, screen_width - (gap * 2), screen_height // 2 - (gap * 1.5))
    if mode == "아래쪽_절반":
        return (gap, screen_height // 2 + (gap * 0.5), screen_width - (gap * 2), screen_height // 2 - (gap * 1.5))

    # 1/4 분할 (모서리)
    if mode == "좌상단_1/4":
        return (gap, gap, screen_width // 2 - (gap * 1.5), screen_height // 2 - (gap * 1.5))
    if mode == "우상단_1/4":
        return (screen_width // 2 + (gap * 0.5), gap, screen_width // 2 - (gap * 1.5), screen_height // 2 - (gap * 1.5))
    if mode == "좌하단_1/4":
        return (gap, screen_height // 2 + (gap * 0.5), screen_width // 2 - (gap * 1.5), screen_height // 2 - (gap * 1.5))
    if mode == "우하단_1/4":
        return (screen_width // 2 + (gap * 0.5), screen_height // 2 + (gap * 0.5), screen_width // 2 - (gap * 1.5), screen_height // 2 - (gap * 1.5))

    # 1/3 및 2/3 분할 (복잡한 계산은 간격을 고려하여 정밀하게 처리)
    unit_w = screen_width // 3
    if mode == "좌측_1/3":
        return (gap, gap, unit_w - (gap * 1.5), screen_height - (gap * 2))
    if mode == "중앙_1/3":
        return (unit_w + (gap * 0.5), gap, unit_w - (gap * 1.0), screen_height - (gap * 2))
    if mode == "우측_1/3":
        return (2 * unit_w + (gap * 0.5), gap, unit_w - (gap * 1.5), screen_height - (gap * 2))

    if mode == "좌측_2/3":
        return (gap, gap, 2 * unit_w - (gap * 1.0), screen_height - (gap * 2))
    if mode == "우측_2/3":
        return (unit_w + (gap * 0.5), gap, 2 * unit_w - (gap * 1.0), screen_height - (gap * 2))
    
    # 최대화
    if mode == "최대화":
        return (gap, gap, screen_width - (gap * 2), screen_height - (gap * 2))
    
    return (gap, gap, screen_width - (gap * 2), screen_height - (gap * 2))
