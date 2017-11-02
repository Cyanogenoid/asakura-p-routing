from ctypes import windll, create_string_buffer, byref, c_ulong
import struct

import psutil


PROCESS_ALL_ACCESS = 0x1F0FFF


class Process():
    def __init__(self, *, name=None, pid=None):
        if pid is not None:
            self.pid = pid
        elif name is not None:
            self.pid = self.pid(name)
        else:
            raise ArgumentError('At least one of {name, pid} must be set')

    def write_buffer(self, address, buffer):
        bytes_read = c_ulong(0)
        num_bytes = len(buffer.raw) - 1  # string buffers end with an additional 0x00 byte, so remove that
        ret = windll.kernel32.WriteProcessMemory(self.handle, address, buffer, num_bytes, byref(bytes_read))
        if not ret:
            error = windll.kernel32.GetLastError()
            raise WindowsError('Failed with error code {}'.format(error))
        if num_bytes != bytes_read.value:
            raise RuntimeError('Tried to write {} bytes, but wrote {}'.format(num_bytes, bytes_read))

    def write_int32(self, address, value):
        buffer = struct.pack('<i', value)
        self.write_buffer(address, create_string_buffer(buffer))

    def write_double(self, address, value):
        buffer = struct.pack('<d', value)
        self.write_buffer(address, create_string_buffer(buffer))

    def read_buffer(self, address, num_bytes):
        buffer = create_string_buffer(num_bytes)
        bytes_read = c_ulong(0)
        ret = windll.kernel32.ReadProcessMemory(self.handle, address, buffer, num_bytes, byref(bytes_read))
        if not ret:
            error = windll.kernel32.GetLastError()
            raise WindowsError('Failed with error code {}'.format(error))
        if num_bytes != bytes_read.value:
            raise RuntimeError('Tried to read {} bytes, but got {}'.format(num_bytes, bytes_read))
        return buffer

    def read_int32(self, address):
        buffer = self.read_buffer(address, 4)
        return struct.unpack('<i', buffer)[0]

    def read_double(self, address):
        buffer = self.read_buffer(address, 8)
        return struct.unpack('<d', buffer)[0]

    def pid(self, name):
        for process in psutil.process_iter():
            if process.name() == name:
                return process.pid
        else:
            raise RuntimeError('No running process called "{}" found'.format(name))

    def __enter__(self):
        self.handle = windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, self.pid)
        return self

    def __exit__(self, *args):
        windll.kernel32.CloseHandle(self.handle)
        del self.handle


import time
address = 0x5B40A0

with Process(name='AssaCrip_en.exe') as process:
    i = 0
    for i in range(100):
        for i in range(41):
            process.write_int32(address, i)
            print('x position', process.read_double(0x5B3FA0))
            time.sleep(0.05)
        for i in reversed(range(1, 40)):
            process.write_int32(address, i)
            time.sleep(0.05)