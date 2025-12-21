#!/usr/bin/env python3
"""
FlexRadio Spot Broadcaster (EC5W v0.1b)
Aplicación con system tray para Windows que conecta a DX Cluster
y reenvía spots en formato N1MM UDP para SmartSDR/FlexRadio

Autor: EC5W
Versión: 0.1b
"""

import sys
import socket
import re
import threading
import time
import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QFormLayout,
    QSystemTrayIcon, QMenu, QAction, QMessageBox, QSpinBox, QCheckBox,
    QComboBox, QFrame, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QPixmap, QPainter, QBrush


# ============================================================================
# TRADUCCIONES
# ============================================================================

TRANSLATIONS = {
    'en': {
        'window_title': 'FlexRadio Spot Broadcaster (EC5W v0.1b)',
        'cluster_config': 'DX Cluster Configuration',
        'server': 'Server:',
        'port': 'Port:',
        'callsign': 'Callsign:',
        'command': 'Command:',
        'send': 'Send',
        'udp_config': 'UDP Configuration (SmartSDR)',
        'ip_address': 'IP Address:',
        'connect': '🔌 Connect',
        'disconnect': '⏹ Disconnect',
        'disconnecting': 'Disconnecting...',
        'spots': 'Spots:',
        'connected': 'Connected',
        'disconnected': 'Disconnected',
        'connecting': 'Connecting...',
        'spot_log': 'Spot Log',
        'clear_log': 'Clear Log',
        'minimize_tray': 'Minimize to system tray on close',
        'autoconnect': 'Auto-connect on startup',
        'language': 'Language:',
        'show': 'Show',
        'exit': 'Exit',
        'error': 'Error',
        'enter_callsign': 'Please enter your callsign',
        'tray_message': 'Application is still running in the background',
        'command_sent': 'Command sent:',
        'error_sending': 'Error sending command:',
        'total_spots': 'Disconnected. Total spots:',
        'connected_to': 'Connected to',
        'login_sent': 'Login sent:',
        'connection_error': 'Connection error:',
    },
    'es': {
        'window_title': 'FlexRadio Spot Broadcaster (EC5W v0.1b)',
        'cluster_config': 'Configuración del Cluster DX',
        'server': 'Servidor:',
        'port': 'Puerto:',
        'callsign': 'Indicativo:',
        'command': 'Comando:',
        'send': 'Enviar',
        'udp_config': 'Configuración UDP (SmartSDR)',
        'ip_address': 'Dirección IP:',
        'connect': '🔌 Conectar',
        'disconnect': '⏹ Desconectar',
        'disconnecting': 'Desconectando...',
        'spots': 'Spots:',
        'connected': 'Conectado',
        'disconnected': 'Desconectado',
        'connecting': 'Conectando...',
        'spot_log': 'Log de Spots',
        'clear_log': 'Limpiar Log',
        'minimize_tray': 'Minimizar al system tray al cerrar',
        'autoconnect': 'Conectar automáticamente al iniciar',
        'language': 'Idioma:',
        'show': 'Mostrar',
        'exit': 'Salir',
        'error': 'Error',
        'enter_callsign': 'Introduce tu indicativo',
        'tray_message': 'La aplicación sigue ejecutándose en segundo plano',
        'command_sent': 'Comando enviado:',
        'error_sending': 'Error enviando comando:',
        'total_spots': 'Desconectado. Total spots:',
        'connected_to': 'Conectado a',
        'login_sent': 'Login enviado:',
        'connection_error': 'Error de conexión:',
    }
}


# ============================================================================
# CLASES DE LÓGICA (del programa original)
# ============================================================================

@dataclass
class DXSpot:
    """Representa un spot DX parseado"""
    spotter: str
    frequency: float
    dx_call: str
    comment: str
    timestamp: datetime
    mode: str = ""


class DXSpotParser:
    """Parser para spots del formato DXSpider/AR-Cluster"""
    
    SPOT_PATTERN = re.compile(
        r'^DX\s+de\s+([A-Z0-9/]+)[:\s]+\s*'
        r'(\d+\.?\d*)\s+'
        r'([A-Z0-9/]+)\s+'
        r'(.{0,30}?)\s*'
        r'(\d{4})Z?\s*$',
        re.IGNORECASE
    )
    
    MODE_HINTS = {
        (1800, 1840): "CW", (1840, 2000): "LSB",
        (3500, 3600): "CW", (3600, 3800): "LSB",
        (7000, 7040): "CW", (7040, 7200): "LSB",
        (7074, 7076): "FT8",
        (10100, 10130): "CW", (10136, 10138): "FT8",
        (14000, 14070): "CW", (14070, 14100): "RTTY",
        (14074, 14076): "FT8", (14100, 14350): "USB",
        (18068, 18095): "CW", (18095, 18168): "USB",
        (18100, 18102): "FT8",
        (21000, 21070): "CW", (21070, 21150): "RTTY",
        (21074, 21076): "FT8", (21150, 21450): "USB",
        (24890, 24915): "CW", (24915, 24990): "USB",
        (28000, 28070): "CW", (28070, 28190): "RTTY",
        (28074, 28076): "FT8", (28300, 29700): "USB",
        (50000, 50100): "CW", (50313, 50315): "FT8",
        (50100, 54000): "USB",
    }
    
    @classmethod
    def guess_mode(cls, freq_khz: float, comment: str) -> str:
        comment_upper = comment.upper()
        if "FT8" in comment_upper or "FT4" in comment_upper:
            return "FT8"
        if "CW" in comment_upper:
            return "CW"
        if "SSB" in comment_upper or "USB" in comment_upper or "LSB" in comment_upper:
            return "USB" if freq_khz > 10000 else "LSB"
        if "RTTY" in comment_upper:
            return "RTTY"
        if "PSK" in comment_upper:
            return "PSK31"
        if "FM" in comment_upper:
            return "FM"
        
        for (low, high), mode in cls.MODE_HINTS.items():
            if low <= freq_khz <= high:
                return mode
        
        return "USB" if freq_khz > 10000 else "LSB"
    
    @classmethod
    def parse_spot(cls, line: str) -> Optional[DXSpot]:
        match = cls.SPOT_PATTERN.match(line.strip())
        if not match:
            return None
        
        spotter = match.group(1).upper()
        freq_khz = float(match.group(2))
        dx_call = match.group(3).upper()
        comment = match.group(4).strip()
        time_str = match.group(5)
        
        now = datetime.now(timezone.utc)
        try:
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            timestamp = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            timestamp = now
        
        mode = cls.guess_mode(freq_khz, comment)
        
        return DXSpot(
            spotter=spotter,
            frequency=freq_khz,
            dx_call=dx_call,
            comment=comment,
            timestamp=timestamp,
            mode=mode
        )


class N1MMSpotFormatter:
    """Formatea spots en XML compatible con N1MM/FlexRadio"""
    
    def __init__(self, station_name: str = "DXCLUSTER"):
        self.station_name = station_name
    
    def format_spot(self, spot: DXSpot) -> str:
        comment = spot.comment if spot.comment else " "
        
        freq = spot.frequency
        if freq == int(freq):
            freq_str = str(int(freq))
        else:
            freq_str = f"{freq:.2f}".replace('.', ',').rstrip('0').rstrip(',')
        
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\r\n'
        xml_str += '<spot>\r\n'
        xml_str += f'\t<app>N1MM</app>\r\n'
        xml_str += f'\t<StationName>{self.station_name}</StationName>\r\n'
        xml_str += f'\t<dxcall>{spot.dx_call}</dxcall>\r\n'
        xml_str += f'\t<frequency>{freq_str}</frequency>\r\n'
        xml_str += f'\t<spottercall>{spot.spotter}</spottercall>\r\n'
        xml_str += f'\t<timestamp>{spot.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</timestamp>\r\n'
        xml_str += f'\t<action>add</action>\r\n'
        xml_str += f'\t<mode>{spot.mode}</mode>\r\n'
        xml_str += f'\t<comment>{comment}</comment>\r\n'
        xml_str += f'\t<status>single mult</status>\r\n'
        xml_str += f'\t<statuslist>single mult</statuslist>\r\n'
        xml_str += '</spot>'
        
        return xml_str


class UDPBroadcaster:
    """Envía paquetes UDP"""
    
    def __init__(self, port: int = 12061, dest_addr: str = "127.0.0.1"):
        self.port = port
        self.dest_addr = dest_addr
        self.socket = None
        self._create_socket()
    
    def _create_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.dest_addr.endswith(".255") or self.dest_addr == "255.255.255.255":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    def send(self, message: str) -> bool:
        try:
            data = message.encode('utf-8')
            self.socket.sendto(data, (self.dest_addr, self.port))
            return True
        except Exception as e:
            return False
    
    def close(self):
        if self.socket:
            self.socket.close()


# ============================================================================
# THREAD DE CONEXIÓN AL CLUSTER
# ============================================================================

class ClusterThread(QThread):
    """Thread que maneja la conexión al cluster DX"""
    
    spot_received = pyqtSignal(str, object)  # mensaje, spot (puede ser None)
    status_changed = pyqtSignal(str, str)  # status, color
    log_message = pyqtSignal(str)
    
    def __init__(self, config: dict, lang: dict):
        super().__init__()
        self.config = config
        self.lang = lang
        self.running = False
        self.socket = None
        self.parser = DXSpotParser()
        self.formatter = None
        self.broadcaster = None
        self.spot_count = 0
    
    def run(self):
        self.running = True
        self.spot_count = 0
        
        # Crear formatter y broadcaster
        self.formatter = N1MMSpotFormatter(self.config.get('station_name', 'DXCLUSTER'))
        self.broadcaster = UDPBroadcaster(
            self.config.get('udp_port', 12061),
            self.config.get('udp_addr', '127.0.0.1')
        )
        
        try:
            # Conectar
            self.status_changed.emit(self.lang['connecting'], "#FFA500")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            self.socket.connect((
                self.config.get('server', 'dxspider.co.uk'),
                self.config.get('port', 7300)
            ))
            
            self.status_changed.emit(self.lang['connected'], "#00AA00")
            self.log_message.emit(f"{self.lang['connected_to']} {self.config['server']}:{self.config['port']}")
            
            # Esperar y enviar login
            time.sleep(2)
            self._read_available()
            
            callsign = self.config.get('callsign', 'N0CALL')
            self.socket.send(f"{callsign}\n".encode('utf-8'))
            self.log_message.emit(f"{self.lang['login_sent']} {callsign}")
            
            time.sleep(1)
            self._read_available()
            
            # Enviar comando inicial
            init_cmd = self.config.get('init_command', 'sh/dx/300')
            if init_cmd:
                self.socket.send(f"{init_cmd}\n".encode('utf-8'))
                self.log_message.emit(f"{self.lang['command_sent']} {init_cmd}")
            
            # Loop principal
            self.socket.settimeout(300)
            buffer = ""
            
            while self.running:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    
                    buffer += data.decode('utf-8', errors='replace')
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip('\r')
                        if line:
                            self._process_line(line)
                
                except socket.timeout:
                    # Keepalive
                    try:
                        self.socket.send(b"\n")
                    except:
                        break
                except Exception as e:
                    self.log_message.emit(f"Error: {e}")
                    break
        
        except Exception as e:
            self.log_message.emit(f"{self.lang['connection_error']} {e}")
        
        finally:
            self.status_changed.emit(self.lang['disconnected'], "#AA0000")
            if self.socket:
                try:
                    self.socket.send(b"bye\n")
                    self.socket.close()
                except:
                    pass
            if self.broadcaster:
                self.broadcaster.close()
            
            self.log_message.emit(f"{self.lang['total_spots']} {self.spot_count}")
    
    def _read_available(self):
        """Lee datos disponibles sin bloquear"""
        self.socket.setblocking(False)
        try:
            data = self.socket.recv(4096)
            if data:
                self.log_message.emit(data.decode('utf-8', errors='replace').strip())
        except BlockingIOError:
            pass
        self.socket.setblocking(True)
    
    def _process_line(self, line: str):
        """Procesa una línea del cluster"""
        spot = self.parser.parse_spot(line)
        
        if spot:
            xml_msg = self.formatter.format_spot(spot)
            if self.broadcaster.send(xml_msg):
                self.spot_count += 1
                msg = f"[{self.spot_count}] {spot.frequency:.1f} {spot.dx_call} de {spot.spotter} {spot.mode}"
                self.spot_received.emit(msg, spot)
        else:
            if line and not line.startswith('>'):
                self.spot_received.emit(f"[CLUSTER] {line}", None)
    
    def stop(self):
        self.running = False
    
    def send_command(self, cmd: str):
        """Envía un comando al cluster"""
        if self.socket and self.running:
            try:
                self.socket.send(f"{cmd}\n".encode('utf-8'))
                self.log_message.emit(f"{self.lang['command_sent']} {cmd}")
            except Exception as e:
                self.log_message.emit(f"{self.lang['error_sending']} {e}")


# ============================================================================
# VENTANA PRINCIPAL
# ============================================================================

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        self.cluster_thread = None
        self.settings = QSettings('FlexRadioSpotBroadcaster', 'Settings')
        self.current_lang = self.settings.value('language', 'en')
        self.lang = TRANSLATIONS[self.current_lang]
        
        self.init_ui()
        self.load_settings()
        self.init_tray()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle(self.lang['window_title'])
        self.setMinimumSize(700, 500)
        
        # Crear icono para la ventana
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#3498db")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setPen(QColor("white"))
        font = QFont("Arial", 22, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "DX")
        painter.end()
        self.setWindowIcon(QIcon(pixmap))
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # === Grupo de configuración del Cluster ===
        self.cluster_group = QGroupBox(self.lang['cluster_config'])
        cluster_layout = QFormLayout(self.cluster_group)
        cluster_layout.setSpacing(8)
        
        # Servidor
        server_layout = QHBoxLayout()
        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("dxspider.co.uk")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(7300)
        self.port_spin.setFixedWidth(80)
        server_layout.addWidget(self.server_edit)
        self.port_label = QLabel(self.lang['port'])
        server_layout.addWidget(self.port_label)
        server_layout.addWidget(self.port_spin)
        self.server_label = QLabel(self.lang['server'])
        cluster_layout.addRow(self.server_label, server_layout)
        
        # Callsign
        self.callsign_edit = QLineEdit()
        self.callsign_edit.setPlaceholderText("YOUR-CALL")
        self.callsign_edit.setMaxLength(15)
        self.callsign_label = QLabel(self.lang['callsign'])
        cluster_layout.addRow(self.callsign_label, self.callsign_edit)
        
        # Comando inicial con botón Enviar
        cmd_layout = QHBoxLayout()
        self.init_cmd_edit = QLineEdit()
        self.init_cmd_edit.setPlaceholderText("sh/fdx 200")
        self.send_cmd_btn = QPushButton(self.lang['send'])
        self.send_cmd_btn.setFixedWidth(80)
        self.send_cmd_btn.clicked.connect(self.send_command)
        self.send_cmd_btn.setEnabled(False)
        cmd_layout.addWidget(self.init_cmd_edit)
        cmd_layout.addWidget(self.send_cmd_btn)
        self.command_label = QLabel(self.lang['command'])
        cluster_layout.addRow(self.command_label, cmd_layout)
        
        layout.addWidget(self.cluster_group)
        
        # === Grupo de configuración UDP ===
        self.udp_group = QGroupBox(self.lang['udp_config'])
        udp_layout = QFormLayout(self.udp_group)
        udp_layout.setSpacing(8)
        
        # IP y Puerto UDP
        udp_addr_layout = QHBoxLayout()
        self.udp_addr_edit = QLineEdit()
        self.udp_addr_edit.setPlaceholderText("127.0.0.1")
        self.udp_port_spin = QSpinBox()
        self.udp_port_spin.setRange(1, 65535)
        self.udp_port_spin.setValue(12061)
        self.udp_port_spin.setFixedWidth(80)
        udp_addr_layout.addWidget(self.udp_addr_edit)
        self.udp_port_label = QLabel(self.lang['port'])
        udp_addr_layout.addWidget(self.udp_port_label)
        udp_addr_layout.addWidget(self.udp_port_spin)
        self.ip_label = QLabel(self.lang['ip_address'])
        udp_layout.addRow(self.ip_label, udp_addr_layout)
        
        layout.addWidget(self.udp_group)
        
        # === Botones de control ===
        btn_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton(self.lang['connect'])
        self.connect_btn.setMinimumHeight(40)
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        self.status_label = QLabel(f"● {self.lang['disconnected']}")
        self.status_label.setStyleSheet("color: #AA0000; font-weight: bold;")
        
        self.spot_count_label = QLabel(f"{self.lang['spots']} 0")
        self.spot_count_label.setStyleSheet("font-weight: bold;")
        
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.spot_count_label)
        btn_layout.addWidget(self.status_label)
        
        layout.addLayout(btn_layout)
        
        # === Log de spots ===
        self.log_group = QGroupBox(self.lang['spot_log'])
        log_layout = QVBoxLayout(self.log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #00ff00;
                border: 1px solid #333;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # Botón limpiar log
        self.clear_btn = QPushButton(self.lang['clear_log'])
        self.clear_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(self.clear_btn)
        
        layout.addWidget(self.log_group)
        
        # === Opciones adicionales ===
        options_layout = QHBoxLayout()
        
        self.minimize_check = QCheckBox(self.lang['minimize_tray'])
        self.minimize_check.setChecked(True)
        options_layout.addWidget(self.minimize_check)
        
        self.autoconnect_check = QCheckBox(self.lang['autoconnect'])
        options_layout.addWidget(self.autoconnect_check)
        
        options_layout.addStretch()
        
        # Selector de idioma
        self.lang_label = QLabel(self.lang['language'])
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Español", "es")
        self.lang_combo.setCurrentIndex(0 if self.current_lang == 'en' else 1)
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        options_layout.addWidget(self.lang_label)
        options_layout.addWidget(self.lang_combo)
        
        layout.addLayout(options_layout)
        
        # Aplicar estilo
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #2c3e50;
            }
            QLineEdit, QSpinBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #3498db;
            }
            QPushButton {
                padding: 8px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1a5276;
            }
        """)
    
    def init_tray(self):
        """Inicializa el icono del system tray"""
        # Crear icono programáticamente
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo circular
        painter.setBrush(QBrush(QColor("#3498db")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        
        # Texto "DX"
        painter.setPen(QColor("white"))
        font = QFont("Arial", 22, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "DX")
        painter.end()
        
        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self)
        
        # Menú del tray
        self.tray_menu = QMenu()
        
        self.show_action = QAction(self.lang['show'], self)
        self.show_action.triggered.connect(self.show_window)
        self.tray_menu.addAction(self.show_action)
        
        self.tray_connect_action = QAction(self.lang['connect'], self)
        self.tray_connect_action.triggered.connect(self.toggle_connection)
        self.tray_menu.addAction(self.tray_connect_action)
        
        self.tray_menu.addSeparator()
        
        self.quit_action = QAction(self.lang['exit'], self)
        self.quit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(self.quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.setToolTip(f"FlexRadio Spot Broadcaster - {self.lang['disconnected']}")
        self.tray_icon.show()
    
    def tray_activated(self, reason):
        """Maneja clicks en el icono del tray"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """Muestra la ventana principal"""
        self.showNormal()
        self.activateWindow()
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        if self.minimize_check.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "FlexRadio Spot Broadcaster",
                self.lang['tray_message'],
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.quit_app()
    
    def quit_app(self):
        """Cierra completamente la aplicación"""
        self.save_settings()
        if self.cluster_thread and self.cluster_thread.isRunning():
            self.cluster_thread.stop()
            self.cluster_thread.wait(3000)
        self.tray_icon.hide()
        QApplication.quit()
    
    def load_settings(self):
        """Carga la configuración guardada"""
        self.server_edit.setText(self.settings.value('server', 'dxspider.co.uk'))
        self.port_spin.setValue(int(self.settings.value('port', 7300)))
        self.callsign_edit.setText(self.settings.value('callsign', ''))
        self.init_cmd_edit.setText(self.settings.value('init_command', 'sh/fdx 200'))
        self.udp_addr_edit.setText(self.settings.value('udp_addr', '127.0.0.1'))
        self.udp_port_spin.setValue(int(self.settings.value('udp_port', 12061)))
        self.minimize_check.setChecked(self.settings.value('minimize_to_tray', True, type=bool))
        self.autoconnect_check.setChecked(self.settings.value('autoconnect', False, type=bool))
        
        # Autoconectar si está configurado
        if self.autoconnect_check.isChecked() and self.callsign_edit.text():
            self.toggle_connection()
    
    def save_settings(self):
        """Guarda la configuración"""
        self.settings.setValue('server', self.server_edit.text() or 'dxspider.co.uk')
        self.settings.setValue('port', self.port_spin.value())
        self.settings.setValue('callsign', self.callsign_edit.text())
        self.settings.setValue('init_command', self.init_cmd_edit.text())
        self.settings.setValue('udp_addr', self.udp_addr_edit.text() or '127.0.0.1')
        self.settings.setValue('udp_port', self.udp_port_spin.value())
        self.settings.setValue('minimize_to_tray', self.minimize_check.isChecked())
        self.settings.setValue('autoconnect', self.autoconnect_check.isChecked())
        self.settings.setValue('language', self.current_lang)
    
    def toggle_connection(self):
        """Conecta o desconecta del cluster"""
        if self.cluster_thread and self.cluster_thread.isRunning():
            # Desconectar
            self.cluster_thread.stop()
            self.connect_btn.setEnabled(False)
            self.connect_btn.setText(self.lang['disconnecting'])
        else:
            # Validar
            if not self.callsign_edit.text():
                QMessageBox.warning(self, self.lang['error'], self.lang['enter_callsign'])
                return
            
            # Guardar config
            self.save_settings()
            
            # Crear config
            config = {
                'server': self.server_edit.text() or 'dxspider.co.uk',
                'port': self.port_spin.value(),
                'callsign': self.callsign_edit.text().upper(),
                'init_command': self.init_cmd_edit.text(),
                'udp_addr': self.udp_addr_edit.text() or '127.0.0.1',
                'udp_port': self.udp_port_spin.value(),
                'station_name': 'STN1'
            }
            
            # Crear y arrancar thread
            self.cluster_thread = ClusterThread(config, self.lang)
            self.cluster_thread.spot_received.connect(self.on_spot_received)
            self.cluster_thread.status_changed.connect(self.on_status_changed)
            self.cluster_thread.log_message.connect(self.on_log_message)
            self.cluster_thread.finished.connect(self.on_thread_finished)
            self.cluster_thread.start()
            
            self.connect_btn.setText(self.lang['disconnect'])
            self.set_inputs_enabled(False)
    
    def on_spot_received(self, message: str, spot):
        """Maneja la recepción de un spot"""
        # Colorear según tipo
        if spot:
            color = "#00ff00"  # Verde para spots
            self.spot_count_label.setText(f"{self.lang['spots']} {self.cluster_thread.spot_count}")
        else:
            color = "#888888"  # Gris para mensajes del cluster
        
        self.log_text.append(f'<span style="color:{color}">{message}</span>')
        
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_status_changed(self, status: str, color: str):
        """Maneja cambios de estado de conexión"""
        self.status_label.setText(f"● {status}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.tray_icon.setToolTip(f"FlexRadio Spot Broadcaster - {status}")
        
        # Actualizar menú del tray
        if status == self.lang['connected']:
            self.tray_connect_action.setText(self.lang['disconnect'])
        else:
            self.tray_connect_action.setText(self.lang['connect'])
    
    def on_log_message(self, message: str):
        """Añade un mensaje al log"""
        self.log_text.append(f'<span style="color:#aaaaaa">{message}</span>')
    
    def on_thread_finished(self):
        """Maneja la finalización del thread"""
        self.connect_btn.setText(self.lang['connect'])
        self.connect_btn.setEnabled(True)
        self.set_inputs_enabled(True)
    
    def change_language(self, index):
        """Cambia el idioma de la interfaz"""
        self.current_lang = self.lang_combo.currentData()
        self.lang = TRANSLATIONS[self.current_lang]
        self.save_settings()
        
        # Actualizar todos los textos
        self.setWindowTitle(self.lang['window_title'])
        self.cluster_group.setTitle(self.lang['cluster_config'])
        self.server_label.setText(self.lang['server'])
        self.port_label.setText(self.lang['port'])
        self.callsign_label.setText(self.lang['callsign'])
        self.command_label.setText(self.lang['command'])
        self.send_cmd_btn.setText(self.lang['send'])
        self.udp_group.setTitle(self.lang['udp_config'])
        self.ip_label.setText(self.lang['ip_address'])
        self.udp_port_label.setText(self.lang['port'])
        self.log_group.setTitle(self.lang['spot_log'])
        self.clear_btn.setText(self.lang['clear_log'])
        self.minimize_check.setText(self.lang['minimize_tray'])
        self.autoconnect_check.setText(self.lang['autoconnect'])
        self.lang_label.setText(self.lang['language'])
        self.show_action.setText(self.lang['show'])
        self.quit_action.setText(self.lang['exit'])
        
        # Actualizar botón conectar según estado
        if self.cluster_thread and self.cluster_thread.isRunning():
            self.connect_btn.setText(self.lang['disconnect'])
            self.tray_connect_action.setText(self.lang['disconnect'])
            self.status_label.setText(f"● {self.lang['connected']}")
        else:
            self.connect_btn.setText(self.lang['connect'])
            self.tray_connect_action.setText(self.lang['connect'])
            self.status_label.setText(f"● {self.lang['disconnected']}")
        
        self.spot_count_label.setText(f"{self.lang['spots']} {self.cluster_thread.spot_count if self.cluster_thread else 0}")
    
    def set_inputs_enabled(self, enabled: bool):
        """Habilita/deshabilita los campos de entrada"""
        self.server_edit.setEnabled(enabled)
        self.port_spin.setEnabled(enabled)
        self.callsign_edit.setEnabled(enabled)
        self.init_cmd_edit.setEnabled(True)  # Siempre habilitado
        self.send_cmd_btn.setEnabled(not enabled)   # Habilitado cuando conectado
        self.udp_addr_edit.setEnabled(enabled)
        self.udp_port_spin.setEnabled(enabled)
    
    def send_command(self):
        """Envía un comando al cluster"""
        if self.cluster_thread and self.cluster_thread.isRunning():
            cmd = self.init_cmd_edit.text().strip()
            if cmd:
                self.cluster_thread.send_command(cmd)


# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FlexRadio Spot Broadcaster")
    app.setOrganizationName("EC5W")
    
    # No cerrar al cerrar última ventana (para mantener el tray)
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
