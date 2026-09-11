"""
Victus AI - Alexa Style HUD (Floating GUI)
Transparent overlay showing AI status, runs in separate thread.
"""
import sys
import os
import threading
import math

HAS_QT = False
try:
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QRectF
    from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
    HAS_QT = True
except ImportError:
    print("[!] PyQt5 not installed. HUD disabled.")

class HUDSignals(QObject):
    update_status = pyqtSignal(str)

class AlexaRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 150)
        self.status = "OFFLINE"
        
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        
    def set_status(self, status):
        self.status = status
        
    def animate(self):
        self.angle = (self.angle + 5) % 360
        
        if self.status == "SPEAKING":
            self.pulse += 10 * self.pulse_dir
        elif self.status == "THINKING":
            self.pulse += 5 * self.pulse_dir
        else:
            self.pulse += 2 * self.pulse_dir
            
        if self.pulse > 100:
            self.pulse = 100
            self.pulse_dir = -1
        elif self.pulse < 0:
            self.pulse = 0
            self.pulse_dir = 1
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = 50 + (self.pulse * 0.1) # base radius 50, pulses up to 60
        
        if self.status == "LISTENING":
            color = QColor(0, 150, 255, 200) # Deep Blue
            glow = QColor(0, 150, 255, 100)
            style = "pulse"
        elif self.status == "THINKING":
            color = QColor(0, 255, 200, 200) # Cyan
            glow = QColor(0, 255, 200, 100)
            style = "spin"
        elif self.status == "SPEAKING":
            color = QColor(200, 255, 255, 255) # Bright White/Cyan
            glow = QColor(0, 200, 255, 150)
            style = "pulse_heavy"
        else:
            color = QColor(100, 100, 100, 100) # Offline Gray
            glow = QColor(0, 0, 0, 0)
            style = "solid"
            
        # Draw Glow
        if style != "solid" and self.status != "OFFLINE":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            glow_radius = radius + (self.pulse * 0.15)
            painter.drawEllipse(QRectF(center_x - glow_radius, center_y - glow_radius, glow_radius * 2, glow_radius * 2))

        # Draw Main Ring
        pen = QPen(color)
        pen.setWidth(8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        if style == "spin":
            # Draw spinning arcs
            span_angle = 100 * 16
            start_angle = self.angle * 16
            painter.drawArc(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2), int(start_angle), int(span_angle))
            painter.drawArc(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2), int(start_angle + 180*16), int(span_angle))
        else:
            # Draw solid ring
            painter.drawEllipse(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2))

class HUDWindow(QWidget):
    def __init__(self, upload_callback=None):
        super().__init__()
        self.upload_callback = upload_callback
        self.signals = HUDSignals()
        self.signals.update_status.connect(self._set_status)

        self.setWindowTitle("Victus AI HUD")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 250)

        # Position: bottom-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 220, screen.height() - 300)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        self.ring = AlexaRing()
        layout.addWidget(self.ring, alignment=Qt.AlignCenter)
        
        self.upload_btn = QPushButton("📷 Upload Image")
        self.upload_btn.setFixedSize(120, 35)
        self.upload_btn.setStyleSheet(
            "QPushButton { background-color: rgba(20, 20, 40, 200); color: white; "
            "border: 1px solid #00e5ff; border-radius: 15px; font-weight: bold; }"
            "QPushButton:hover { background-color: rgba(0, 229, 255, 100); }"
        )
        self.upload_btn.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def _set_status(self, status):
        self.ring.set_status(status)

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image for AI", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path and self.upload_callback:
            # Run the callback in a separate thread so we don't freeze the GUI
            threading.Thread(target=self.upload_callback, args=(file_path,), daemon=True).start()


class HUD:
    """Thread-safe HUD controller."""

    def __init__(self, upload_callback=None):
        self.window = None
        self.app = None
        self.ready = threading.Event()
        self.upload_callback = upload_callback

        if not HAS_QT:
            self.enabled = False
            return

        self.enabled = True
        self.thread = threading.Thread(target=self._run_qt, daemon=True)
        self.thread.start()
        self.ready.wait(timeout=5)

    def _run_qt(self):
        self.app = QApplication(sys.argv if not QApplication.instance() else [])
        self.window = HUDWindow(self.upload_callback)
        self.window.show()
        self.ready.set()
        self.app.exec_()

    def set_status(self, status):
        if self.enabled and self.window:
            self.window.signals.update_status.emit(status)

# Global HUD instance to be shared across modules
global_hud = None

def init_hud(upload_callback=None):
    global global_hud
    if global_hud is None:
        global_hud = HUD(upload_callback)
    return global_hud

def set_hud_status(status):
    if global_hud:
        global_hud.set_status(status)
