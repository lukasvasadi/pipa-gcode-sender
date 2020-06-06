import os
import sys
# from PyQt5.QtGui import *
# from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import serial
from serial.tools import list_ports
import platform
import time

import qtmodern.styles
import qtmodern.windows


class Window(QMainWindow):
    """
    GUI for passing g-code commands to liquid handler.
    """

    def __init__(self):
        super(Window, self).__init__()
        QApplication.setStyle(QStyleFactory.create('Plastique'))

        self.layout = QVBoxLayout()
        self.v0_layout = QVBoxLayout()
        # self.v0_layout.addStretch(1)
        self.v1_layout = QVBoxLayout()
        self.v1_layout.addStretch(1)
        self.v2_layout = QVBoxLayout()
        # self.v2_layout.addStretch(1)
        self.h0_layout = QHBoxLayout()
        self.h1_layout = QHBoxLayout()
        self.h2_layout = QHBoxLayout()
        self.h3_layout = QHBoxLayout()
        self.h4_layout = QHBoxLayout()
        self.h5_layout = QHBoxLayout()
        self.h6_layout = QHBoxLayout()
        self.h7_layout = QHBoxLayout()

        self.protocol_table = QTableWidget()

        self.lbl_command_name = QLabel("Command name")
        self.lbl_command_type = QLabel("Type")
        self.lbl_command_duration = QLabel("Time")
        self.lbl_serial_terminal = QLabel("Serial terminal")
        self.lbl_command_line = QLabel("Command line")

        self.txt_command_name = QLineEdit("Step 1...")
        self.txt_command_duration = QLineEdit("00:00:30")
        self.txt_gcode_direct = QLineEdit("G0 X0 Y0 Z0")
        self.txt_command_line = QLineEdit("G1 E0")

        self.command = QComboBox()
        self.command.addItem("Home")
        self.command.addItem("Add solution")
        self.command.addItem("Wash")
        self.command.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        self.btn_add = QPushButton("Add")
        self.btn_connect = QPushButton("Connect")
        self.btn_start = QPushButton("Start")
        self.btn_pause = QPushButton("Pause")
        self.btn_stop = QPushButton("Stop")
        self.btn_send = QPushButton("Send")

        self.progress = QProgressBar()
        self.step_index = 0

        self.text_editor = QTextEdit()

        self.instructions = {"command": [], "type": [], "time": []}

        # Execute main window
        self.main_window()

    def main_window(self):
        # Create layout
        self.setGeometry(650, 300, 600, 600)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.layout)

        self.generate_table()

        self.btn_add.clicked.connect(self.add_step)
        self.btn_connect.clicked.connect(self.connect)
        self.btn_start.clicked.connect(self.step_indexer)
        self.btn_send.clicked.connect(self.transmit)

        # Widget display
        self.h0_layout.addWidget(self.protocol_table)
        self.v0_layout.addWidget(self.lbl_command_name)
        self.v1_layout.addWidget(self.lbl_command_type)
        self.v2_layout.addWidget(self.lbl_command_duration)
        self.v0_layout.addWidget(self.txt_command_name)
        self.v1_layout.addWidget(self.command)
        self.v2_layout.addWidget(self.txt_command_duration)
        self.h2_layout.addWidget(self.btn_connect)
        self.h2_layout.addWidget(self.btn_start)
        self.h2_layout.addWidget(self.btn_pause)
        self.h2_layout.addWidget(self.btn_stop)
        self.h3_layout.addWidget(self.progress)
        self.h4_layout.addWidget(self.lbl_serial_terminal)
        self.h5_layout.addWidget(self.text_editor)
        self.h6_layout.addWidget(self.lbl_command_line)
        self.h7_layout.addWidget(self.txt_command_line)
        self.h7_layout.addWidget(self.btn_send)

        self.layout.addLayout(self.h0_layout)
        self.h1_layout.addLayout(self.v0_layout)
        self.h1_layout.addLayout(self.v1_layout)
        self.h1_layout.addLayout(self.v2_layout)
        self.h1_layout.addWidget(self.btn_add)
        self.layout.addLayout(self.h1_layout)
        self.layout.addLayout(self.h2_layout)
        self.layout.addLayout(self.h3_layout)
        self.layout.addLayout(self.h4_layout)
        self.layout.addLayout(self.h5_layout)
        self.layout.addLayout(self.h6_layout)
        self.layout.addLayout(self.h7_layout)

        self.layout.setSpacing(10)

        self.show()

    def generate_table(self):
        self.protocol_table.setSelectionBehavior(QTableView.SelectRows)
        # self.protocol_table.setRowCount()
        self.protocol_table.setColumnCount(3)
        self.protocol_table.setHorizontalHeaderLabels(["Command Name", "Command Type", "Delay Time"])
        header = self.protocol_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

    def step_indexer(self):
        while self.step_index < 101:
            self.progress.setValue(self.step_index)
            time.sleep(1)
            self.step_index += 10
        self.step_index = 0
        self.progress.setValue(self.step_index)

    def add_step(self):
        self.instructions["command"].append(self.txt_command_name.text())
        self.instructions["type"].append(str(self.command.currentText()))
        self.instructions["time"].append(self.txt_command_duration.text())

        print(self.instructions)
        self.text_editor.append("Example text")

    def connect(self):
        self.text_editor.append("Welcome")
        if platform.system() == "Windows":
            ports_available = list(list_ports.comports())
            for com in ports_available:
                if "USB Serial Device" in com.description:
                    port = com[0]
                    self.text_editor.append("Port: " + port)
                    try:
                        self.motherboard = serial.Serial(port=port, baudrate=250000, timeout=1)
                        # Toggle DTR to reset microcontroller — important for cleaning serial buffer
                        self.motherboard.setDTR(False)
                        time.sleep(0.1)
                        # Wipe serial buffer
                        self.motherboard.reset_input_buffer()
                        self.motherboard.reset_output_buffer()
                        self.motherboard.setDTR(True)
                        break
                    except WindowsError:
                        print("Error: Problem with serial connection")
        else:
            self.motherboard = serial.Serial(port="com31", baudrate=250000, timeout=1)
            # Toggle DTR to reset microcontroller — important for cleaning serial buffer
            self.motherboard.setDTR(False)
            time.sleep(0.1)
            # Wipe serial buffer
            self.motherboard.reset_input_buffer()
            # micro_controller.reset_output_buffer()
            self.motherboard.setDTR(True)

        time.sleep(1)
        # self.receive()

        # Send command to enable cold extrusion
        command = "M302 S0\r\n"
        self.motherboard.write(command.encode())

    def transmit(self):
        command = self.txt_command_line.text()
        command = command + "\r\n"
        self.motherboard.write(command.encode())
        time.sleep(1)
        self.receive()
        self.txt_command_line.setText("G1 E0")
        # self.motherboard.close()

    def receive(self):
        transmission = self.motherboard.readline()[0:-1].decode('utf-8', 'ignore')

        self.text_editor.append(transmission)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(window)
    mw.show()
    sys.exit(app.exec_())
