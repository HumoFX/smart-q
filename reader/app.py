import time

from usb import core, util
from serial import Serial, serialutil
from serial.tools import list_ports, list_ports_common, list_ports_osx, list_ports_linux
from loguru import logger

my_device_list_name = ("Netum", "Bluetooth-Incoming-Port",)
VID_list = (6790,)
COM_LIST = ('COM5',)


class SerialManager:
    def __init__(self):
        self.serial = None
        self._port = None
        self._baudrate = 9600
        self._bytesize = serialutil.EIGHTBITS
        self._parity = serialutil.PARITY_NONE
        self._stopbits = serialutil.STOPBITS_ONE
        self._timeout = None
        self._xonxoff = False
        self._rtscts = False
        self._dsrdtr = False
        self._inter_byte_timeout = None
        self._exclusive = None
        self._write_timeout = None
        self._dsrdtr_state = None
        self._rts_state = None
        self._break_state = None

    def connect(self, baudrate=9600, bytesize=serialutil.EIGHTBITS, parity=serialutil.PARITY_NONE,
                stopbits=serialutil.STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False,
                write_timeout=None, dsrdtr=False, inter_byte_timeout=None, exclusive=None):
        self._port = self._find_port()
        self.serial = Serial(self._port, baudrate, bytesize, parity, stopbits, timeout, xonxoff, rtscts,
                             write_timeout, dsrdtr, inter_byte_timeout, exclusive)
        self._baudrate = baudrate
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._timeout = timeout
        self._xonxoff = xonxoff
        self._rtscts = rtscts
        self._dsrdtr = dsrdtr
        self._inter_byte_timeout = inter_byte_timeout
        self._exclusive = exclusive
        self._write_timeout = write_timeout
        self._dsrdtr_state = None
        self._rts_state = None
        self._break_state = None

    @staticmethod
    def _find_port():
        """Find port by name"""
        for port in list_ports_osx.comports():
        # for port in list_ports_windows.comports():
            if port.device in COM_LIST:
                return port.device
            if port.vid in VID_list:
                return port.device996779156
        raise serialutil.SerialException("Could not find port")

    def is_connected(self):
        return self.serial is not None and self.serial.is_open

    async def read(self):
        while True:
            data = self.serial.read_all()
            if data:
                print(data)
                return data.decode('utf-8')
    # return None

    def disconnect(self):
        if self.serial:
            self.serial.close()
            self.serial = None