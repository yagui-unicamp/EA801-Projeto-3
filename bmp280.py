# Biblioteca mínima para BMP280
from ustruct import unpack
import time

BMP280_I2CADDR = const(0x76)
BMP280_REGISTER_CONTROL = const(0xF4)
BMP280_REGISTER_PRESSUREDATA = const(0xF7)
BMP280_REGISTER_TEMPDATA = const(0xFA)

class BMP280:
    def __init__(self, i2c, addr=BMP280_I2CADDR):
        self.i2c = i2c
        self.addr = addr
        self._load_calibration()
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x27')  # normal mode, temp and press oversampling x1

    def _load_calibration(self):
        calib = self.i2c.readfrom_mem(self.addr, 0x88, 24)
        self.dig_T1, self.dig_T2, self.dig_T3 = unpack('<Hhh', calib[0:6])
        self.dig_P1, self.dig_P2, self.dig_P3, self.dig_P4, self.dig_P5, self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9 = unpack('<Hhhhhhhhh', calib[6:24])

    def _read_raw_data(self):
        data = self.i2c.readfrom_mem(self.addr, BMP280_REGISTER_PRESSUREDATA, 6)
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return adc_t, adc_p

    def _compensate_temperature(self, adc_t):
        var1 = (((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        temp = (self.t_fine * 5 + 128) >> 8
        return temp / 100.0

    def _compensate_pressure(self, adc_p):
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 += ((var1 * self.dig_P5) << 17)
        var2 += (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            return 0
        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
        return p / 256.0

    @property
    def pressure(self):
        adc_t, adc_p = self._read_raw_data()
        self._compensate_temperature(adc_t)  # Needed for pressure compensation
        return self._compensate_pressure(adc_p)

    @property
    def temperature(self):
        adc_t, _ = self._read_raw_data()
        return self._compensate_temperature(adc_t)
