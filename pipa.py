import os
import sys
import platform
import time
import serial
from serial.tools import list_ports
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import qtmodern.styles
import qtmodern.windows


class Window(QMainWindow):
    """
    GUI for passing g-code commands to liquid handler.

    Use the following helpful g-code commands upon startup:
        M122 to see report on driver status.
        M914 alone shows Stallguard sensitivity values (can also be used to override values).
        M906 - Set or get motor current in milliamps using axis codes X, Y, Z, E. Report values if no axis codes given.
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
        self.btn_stop = QPushButton("EOS")
        self.btn_send = QPushButton("Send")

        self.btn_stop.setStyleSheet("background-color: #DD1D1D")

        self.progress = QProgressBar()
        self.step_index = 0

        self.text_editor = QTextEdit()

        self.instructions = {"command": [], "type": [], "time": []}
        self.g_code_command_array = []
        self.motherboard = ''

        # Execute main window
        self.main_window()

    def main_window(self):
        # Create layout
        self.setGeometry(650, 300, 600, 600)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.layout)

        self.generate_table()

        self.btn_add.clicked.connect(self.load_instructions)
        self.btn_connect.clicked.connect(self.connect)
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.em_stop)
        self.btn_send.clicked.connect(self.transmit_cmd_line)
        # self.txt_command_line.keyPressEvent = self.keyPressEvent

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
        self.protocol_table.setRowCount(len(self.instructions["command"]))
        self.protocol_table.setColumnCount(3)
        self.protocol_table.setHorizontalHeaderLabels(["Command Name", "Command Type", "Delay Time"])
        header = self.protocol_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        for row in range(len(self.instructions["command"])):
            self.protocol_table.setItem(row, 0, QTableWidgetItem(self.instructions["command"][row]))
            self.protocol_table.setItem(row, 1, QTableWidgetItem(self.instructions["type"][row]))
            self.protocol_table.setItem(row, 2, QTableWidgetItem(self.instructions["time"][row]))

        self.protocol_table.resizeRowsToContents()

    def load_instructions(self):
        try:
            # Re-initialize command array
            self.g_code_command_array = []
            file_path = QFileDialog.getOpenFileName(self, 'Open file', os.getenv('HOME'))[0]
            with open(file_path, 'r') as file_g_code:  # Open with intention to read
                for line in file_g_code:
                    self.g_code_command_array.append(line)
                    # print(line)
        except IndexError:
            self.text_editor.append("Error: file may have incorrect format")
        except NameError:
            self.text_editor.append("Error: cannot load file")

    def step_indexer(self):
        # while self.step_index < 101:
        #     self.progress.setValue(self.step_index)
        #     time.sleep(1)
        #     self.step_index += 10
        # self.step_index = 0
        self.progress.setValue(self.step_index)

        # M31 reports print time

    def add_step(self):
        command_name = self.txt_command_name.text()
        command_type = str(self.command.currentText())
        command_time = self.txt_command_duration.text()

        self.instructions["command"].append(command_name)
        self.instructions["type"].append(command_type)
        self.instructions["time"].append(command_time)

        print(self.instructions)
        self.text_editor.append(command_name + ", " + command_type + ", " + command_time)
        self.generate_table()

    def connect(self):
        self.text_editor.append("Welcome")
        try:
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

            # time.sleep(1)
            self.initialize()
        except AttributeError:
            self.text_editor.append("Error: motherboard not detected")

    def initialize(self):
        # Retrieve firmware info
        # command_info = "M115"
        # self.transmit(command_info)
        # self.receive()

        # Set units to mm
        command_units_mm = "G21"
        self.transmit(command_units_mm)
        self.receive()

        # Enable cold extrusion
        command_cold_extrusion = "M302 S0"
        self.transmit(command_cold_extrusion)
        self.receive()

        # TMC debugging
        # command_tmc_debug = "M122"
        # self.transmit(command_tmc_debug)
        # self.receive()

        # Home all motors
        command_home_y = "G28 Y"
        self.transmit(command_home_y)
        self.receive()

        command_home_x = "G28 X"
        self.transmit(command_home_x)
        self.receive()
        
        command_home_z = "G28 Z"
        self.transmit(command_home_z)
        self.receive()

        # M106 turns on fan and sets speed; M107 turns fan off
        # M502 performs factory reset of all configurable settings (EEPROM)
        # M500 saves new settings
        # M92 set axis steps per unit
        # M119 endstop states
        # M122 TMC debugging

    def transmit(self, command):
        command = command.upper() + "\r\n"
        # self.text_editor.append(command[0:-2])
        self.motherboard.write(command.encode())
        # Wait for motherboard to receive transmission
        time.sleep(1)

    def transmit_cmd_line(self):
        command = self.txt_command_line.text()
        command = command.upper() + "\r\n"
        self.motherboard.write(command.encode())
        self.text_editor.append(command[0:-2])
        time.sleep(1)
        self.receive()
        self.txt_command_line.setText("G1 E0")
        # self.motherboard.close()

    def receive(self):
        # Attempt to read all incoming messages from motherboard
        while True:
            transmission = self.motherboard.readline()[0:-1].decode('utf-8', 'ignore')
            if transmission == "":
                break
            self.text_editor.append(transmission)
            time.sleep(0.1)

    def em_stop(self):
        # M112 EMERGENCY STOP
        command_em_stop = "M112"
        self.transmit(command_em_stop)
        self.receive()

    def start(self):
        while True:
            for i in range(len(self.g_code_command_array)):
                self.step_index = i
                self.transmit(self.g_code_command_array[i])
                self.receive()
                self.step_indexer()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            print("Pressed Q")
        elif event.key() == Qt.Key_Enter:
            print("Pressed Enter")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(window)
    mw.show()
    sys.exit(app.exec_())
