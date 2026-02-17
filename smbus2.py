class SMBus:
    def __init__(self, bus_num=1):
        raise RuntimeError("smbus2 stub used on non-Pi system. Use simulator instead.")

    def read_byte_data(self, addr, reg):
        raise RuntimeError("smbus2 stub")

    def write_byte_data(self, addr, reg, value):
        raise RuntimeError("smbus2 stub")

    def close(self):
        pass
