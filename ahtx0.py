# Biblioteca MicroPython para AHT10/AHT20
import time
class AHT20:
    def __init__(self, i2c, address=0x38):
        self.i2c = i2c
        self.addr = address
        time.sleep_ms(20)
        self.i2c.writeto(self.addr, b'\xBE')
        time.sleep_ms(10)

    def _read_data(self):
        self.i2c.writeto(self.addr, b'\xAC\x33\x00')
        time.sleep_ms(80)
        data = self.i2c.readfrom(self.addr, 6)
        return data

    @property
    def temperature(self):
        data = self._read_data()
        raw_temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        return ((raw_temp / 1048576.0) * 200.0) - 50.0

    @property
    def relative_humidity(self):
        data = self._read_data()
        raw_humi = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
        return (raw_humi / 1048576.0) * 100.0
