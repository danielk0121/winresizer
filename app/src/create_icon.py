import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt

def create_tray_icon():
    app = QApplication(sys.argv)
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw a simple white square with a border for the tray icon
    pen = QPen(Qt.white)
    pen.setWidth(4)
    painter.setPen(pen)
    painter.drawRect(8, 8, 48, 48)
    
    painter.setBrush(Qt.white)
    painter.drawRect(20, 20, 24, 24)
    
    painter.end()
    pixmap.save('app/src/ui/tray_icon.png', 'PNG')

if __name__ == '__main__':
    create_tray_icon()
