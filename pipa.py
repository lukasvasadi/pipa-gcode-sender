import csv
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
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

        self.protocol_table = QTableWidget()

        self.lbl_command_name = QLabel("Command name")
        self.lbl_command_type = QLabel("Type")
        self.lbl_command_duration = QLabel("Time")

        self.txt_command_name = QLineEdit("Step 1...")
        self.txt_command_duration = QLineEdit("00:00:30")
        self.txt_gcode_direct = QLineEdit("G0 X0 Y0 Z0")

        self.command = QComboBox()
        self.command.addItem("Home")
        self.command.addItem("Add solution")
        self.command.addItem("Wash")
        self.command.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        self.btn_add = QPushButton("Add")
        self.btn_start = QPushButton("Start")
        self.btn_pause = QPushButton("Pause")
        self.btn_stop = QPushButton("Stop")

        self.progress = QProgressBar()
        self.step_index = 0

        # Execute main window
        self.main_window()

    def main_window(self):
        # Create layout
        self.setGeometry(650, 300, 600, 300)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.layout)

        self.generate_table()

        self.btn_start.clicked.connect(self.step_indexer)

        # Widget display
        self.h0_layout.addWidget(self.protocol_table)
        self.v0_layout.addWidget(self.lbl_command_name)
        self.v1_layout.addWidget(self.lbl_command_type)
        self.v2_layout.addWidget(self.lbl_command_duration)
        self.v0_layout.addWidget(self.txt_command_name)
        self.v1_layout.addWidget(self.command)
        self.v2_layout.addWidget(self.txt_command_duration)
        self.h2_layout.addWidget(self.btn_start)
        self.h2_layout.addWidget(self.btn_pause)
        self.h2_layout.addWidget(self.btn_stop)
        self.h3_layout.addWidget(self.progress)

        self.layout.addLayout(self.h0_layout)
        self.h1_layout.addLayout(self.v0_layout)
        self.h1_layout.addLayout(self.v1_layout)
        self.h1_layout.addLayout(self.v2_layout)
        self.h1_layout.addWidget(self.btn_add)
        self.layout.addLayout(self.h1_layout)
        self.layout.addLayout(self.h2_layout)
        self.layout.addLayout(self.h3_layout)

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


    # IMPORTANT: When serial port opened, Arduino automatically resets
    def connect(self):
        if platform.system() == "Windows":
            ports_available = list(list_ports.comports())
            for com in ports_available:
                if "USB Serial Port" in com.description:
                    port = com[0]
                    print(port)
                    try:
                        motherboard = serial.Serial(port=port, baudrate=500000, timeout=1)
                        # Toggle DTR to reset ATmega328 — important for cleaning serial buffer
                        motherboard.setDTR(False)
                        time.sleep(0.1)
                        # Wipe serial buffer
                        motherboard.reset_input_buffer()
                        # micro_controller.reset_output_buffer()
                        motherboard.setDTR(True)
                    except WindowsError:
                        print("Error: Problem with serial connection")
        else:
            motherboard = serial.Serial(port="com42", baudrate=500000, timeout=1)
            # Toggle DTR to reset ATmega328 — important for cleaning serial buffer
            motherboard.setDTR(False)
            time.sleep(0.1)
            # Wipe serial buffer
            motherboard.reset_input_buffer()
            # micro_controller.reset_output_buffer()
            motherboard.setDTR(True)

        time.sleep(1)
        transmission_incoming = True
        while transmission_incoming:
            transmission = motherboard.readline()[0:-2].decode("utf-8")
            # transmission = reader.readline().decode('ascii').strip()
            print(transmission)
            # print(transmission.decode('utf-8'))
            transmission_incoming = False

        setup_commands = self.package_setup_commands()
        motherboard.write(setup_commands.encode())

        time.sleep(1)
        transmit_data(motherboard)

    def package_setup_commands(self):
        # model = self.txt_reader_model.text()
        setting = self.txt_reader_setting.text()
        median = self.txt_gate_median.text()
        amplitude = self.txt_gate_amplitude.text()
        frequency = self.txt_freq.text()

        setup_commands = '<' + setting + ';' + median + ';' + amplitude + ';' + frequency + '>'
        print("Setup: " + setup_commands)
        return setup_commands

    def transmit_data(reader):
        fieldnames = ['time', 'sen1Ch1', 'sen1Ch2', 'sen1Ch3', 'sen1Ch4', 'sen1Ch5',
                      'sen2Ch1', 'sen2Ch2', 'sen2Ch3', 'sen2Ch4', 'sen2Ch5', 'cnt1', 'cnt2']
        with open('data.csv', 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(fieldnames)

        while True:
            with open('data.csv', 'a', newline='') as csv_file:
                # csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                time_start = time.time()
                transmission = reader.readline()[0:-2].decode('utf-8')
                print(transmission)
                data = transmission.split(',')
                # csv_writer.writerow([data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7],
                #                      data[8], data[9], data[10], data[11]])
                # print(time.time() - time_start)
                # time.sleep(1)

                if not transmission:
                    print("Finished")
                    break


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(window)
    mw.show()
    sys.exit(app.exec_())


# # Simple PyQT serial terminal v0.09 from iosoft.blog
#
# from PyQt5 import QtGui, QtCore
# from PyQt5.QtWidgets import QTextEdit, QWidget, QApplication, QVBoxLayout
#
# try:
#     import Queue
# except:
#     import queue as Queue
# import sys, time, serial
#
# WIN_WIDTH, WIN_HEIGHT = 684, 400  # Window size
# SER_TIMEOUT = 0.1  # Timeout for serial Rx
# RETURN_CHAR = "\n"  # Char to be sent when Enter key pressed
# PASTE_CHAR = "\x16"  # Ctrl code for clipboard paste
# baudrate = 115200  # Default baud rate
# portname = "COM1"  # Default port name
# hexmode = False  # Flag to enable hex display
#
#
# # Convert a string to bytes
# def str_bytes(s):
#     return s.encode('latin-1')
#
#
# # Convert bytes to string
# def bytes_str(d):
#     return d if type(d) is str else "".join([chr(b) for b in d])
#
#
# # Return hexadecimal values of data
# def hexdump(data):
#     return " ".join(["%02X" % ord(b) for b in data])
#
#
# # Return a string with high-bit chars replaced by hex values
# def textdump(data):
#     return "".join(["[%02X]" % ord(b) if b & gt
#     '\x7e' else b
#     for b in data])
#
#
# # Display incoming serial data
# def display(s):
#     if not hexmode:
#         sys.stdout.write(textdump(str(s)))
#     else:
#         sys.stdout.write(hexdump(s) + ' ')
#
#
# # Custom text box, catching keystrokes
# class MyTextBox(QTextEdit):
#     def __init__(self, *args):
#         QTextEdit.__init__(self, *args)
#
#     def keyPressEvent(self, event):  # Send keypress to parent's handler
#         self.parent().keypress_handler(event)
#
#
# # Main widget
# class MyWidget(QWidget):
#     text_update = QtCore.pyqtSignal(str)
#
#     def __init__(self, *args):
#         QWidget.__init__(self, *args)
#         self.textbox = MyTextBox()  # Create custom text box
#         font = QtGui.QFont()
#         font.setFamily("Courier New")  # Monospaced font
#         font.setPointSize(10)
#         self.textbox.setFont(font)
#         layout = QVBoxLayout()
#         layout.addWidget(self.textbox)
#         self.setLayout(layout)
#         self.resize(WIN_WIDTH, WIN_HEIGHT)  # Set window size
#         self.text_update.connect(self.append_text)  # Connect text update to handler
#         sys.stdout = self  # Redirect sys.stdout to self
#         self.serth = SerialThread(portname, baudrate)  # Start serial thread
#         self.serth.start()
#
#     def write(self, text):  # Handle sys.stdout.write: update display
#         self.text_update.emit(text)  # Send signal to synchronise call with main thread
#
#     def flush(self):  # Handle sys.stdout.flush: do nothing
#         pass
#
#     def append_text(self, text):  # Text display update handler
#         cur = self.textbox.textCursor()
#         cur.movePosition(QtGui.QTextCursor.End)  # Move cursor to end of text
#         s = str(text)
#         while s:
#             head, sep, s = s.partition("\n")  # Split line at LF
#             cur.insertText(head)  # Insert text at cursor
#             if sep:  # New line if LF
#                 cur.insertBlock()
#         self.textbox.setTextCursor(cur)  # Update visible cursor
#
#     def keypress_handler(self, event):  # Handle keypress from text box
#         k = event.key()
#         s = RETURN_CHAR if k == QtCore.Qt.Key_Return else event.text()
#         if len(s) & gt;0 and s[0] == PASTE_CHAR:  # Detect ctrl-V paste
#             cb = QApplication.clipboard()
#             self.serth.ser_out(cb.text())  # Send paste string to serial driver
#         else:
#             self.serth.ser_out(s)  # ..or send keystroke
#
#     def closeEvent(self, event):  # Window closing
#         self.serth.running = False  # Wait until serial thread terminates
#         self.serth.wait()
#
#
# # Thread to handle incoming &amp; outgoing serial data
# class SerialThread(QtCore.QThread):
#     def __init__(self, portname, baudrate):  # Initialise with serial port details
#         QtCore.QThread.__init__(self)
#         self.portname, self.baudrate = portname, baudrate
#         self.txq = Queue.Queue()
#         self.running = True
#
#     def ser_out(self, s):  # Write outgoing data to serial port if open
#         self.txq.put(s)  # ..using a queue to sync with reader thread
#
#     def ser_in(self, s):  # Write incoming serial data to screen
#         display(s)
#
#     def run(self):  # Run serial reader thread
#         print("Opening %s at %u baud %s" % (self.portname, self.baudrate,
#                                             "(hex display)" if hexmode else ""))
#         try:
#             self.ser = serial.Serial(self.portname, self.baudrate, timeout=SER_TIMEOUT)
#             time.sleep(SER_TIMEOUT * 1.2)
#             self.ser.flushInput()
#         except:
#             self.ser = None
#         if not self.ser:
#             print("Can't open port")
#             self.running = False
#         while self.running:
#             s = self.ser.read(self.ser.in_waiting or 1)
#             if s:  # Get data from serial port
#                 self.ser_in(bytes_str(s))  # ..and convert to string
#             if not self.txq.empty():
#                 txd = str(self.txq.get())  # If Tx data in queue, write to serial port
#                 self.ser.write(str_bytes(txd))
#         if self.ser:  # Close serial port when thread finished
#             self.ser.close()
#             self.ser = None
#
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     opt = err = None
#     for arg in sys.argv[1:]:  # Process command-line options
#         if len(arg) == 2 and arg[0] == "-":
#             opt = arg.lower()
#             if opt == '-x':  # -X: display incoming data in hex
#                 hexmode = True
#                 opt = None
#         else:
#             if opt == '-b':  # -B num: baud rate, e.g. '9600'
#                 try:
#                     baudrate = int(arg)
#                 except:
#                     err = "Invalid baudrate '%s'" % arg
#             elif opt == '-c':  # -C port: serial port name, e.g. 'COM1'
#                 portname = arg
#     if err:
#         print(err)
#         sys.exit(1)
#     w = MyWidget()
#     w.setWindowTitle('PyQT Serial Terminal ' + VERSION)
#     w.show()
#     sys.exit(app.exec_())
#
# # EOF
