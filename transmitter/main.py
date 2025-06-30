# -*- coding: utf-8 -*-
"""
Projeto Final BitDogLab - Integrado com LoRa
"""
import bluetooth
import ubluetooth
from ble_advertising import advertising_payload
from machine import Pin, ADC, SoftI2C, I2C, SPI
import utime
import math
import ujson
import random
import machine
import struct
import bmp280
import ahtx0
from ssd1306 import SSD1306_I2C
import neopixel
from ulora import LoRa, ModemConfig, SPIConfig

# ========================
# UUIDs Globais (BLE)
# ========================
ENV_SERVICE_UUID = ubluetooth.UUID(0x181A)  # Environmental Sensing Service
TEMP_CHAR_UUID = ubluetooth.UUID(0x2A6E)    # Temperature (IEEE 11073-10101)
HUM_CHAR_UUID = ubluetooth.UUID(0x2A6F)     # Humidity (Percentage)
SOUND_CHAR_UUID = ubluetooth.UUID('00002B06-0000-1000-8000-00805F9B34FB')  # Sound Level (Custom)

# ========================
# Configurações Globais
# ========================
class Config:
    TEMP_IDEAL = (20, 26)
    HUM_IDEAL = (40, 60)
    DB_IDEAL = (50, 80)
    
    COLOR_NOISE = (50, 0, 0)
    COLOR_TEMP_COLD = (0, 0, 50)
    COLOR_TEMP_HOT = (50, 0, 0)
    COLOR_HUM = (0, 0, 50)
    COLOR_WAITING = (0, 0, 50)
    COLOR_CONNECTED = (0, 50, 0)
    
    MATRIX_SIZE = 5
    NUM_LEDS = 25
    HISTORY_SIZE = 50
    BLE_NAME = "BitDogLab-Sensor"
    NUM_SAMPLES = 500
    SENSOR_UPDATE_INTERVAL = 2 # Intervalo para atualização BLE e LoRa

# ========================
# Configurações LoRa
# ========================
RFM95_SPIBUS = SPIConfig.rp2_0  # SPI0: SCK=18, MOSI=19, MISO=16
RFM95_CS = 17  # Chip select
RFM95_RST = 28  # Pino de reset
RFM95_INT = 20  # Pino de interrupção (DIO0)
RF95_FREQ = 915.0  # Frequência em MHz (ajuste conforme a sua região)
CLIENT_ADDRESS = 1
SERVER_ADDRESS = 2

# ========================
# Inicialização do Hardware
# ========================
# Configuração do sensor BME280 na interface I2C0 (pinos GPIO0 SDA, GPIO1 SCL)
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
aht20 = ahtx0.AHT20(i2c)

i2c1 = SoftI2C(scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c1)
oled.fill(0)
oled.text("Iniciando...", 0, 0)
oled.show()

np = neopixel.NeoPixel(Pin(7), Config.NUM_LEDS)
LED_MATRIX = [
    [24, 23, 22, 21, 20],
    [15, 16, 17, 18, 19],
    [14, 13, 12, 11, 10],
    [5, 6, 7, 8, 9],
    [4, 3, 2, 1, 0]
]

NOISE_LEVELS = [
    [12],                # Centro
    [11, 13, 7, 17],     # 1º Círculo
    [10, 14, 2, 16, 8, 18, 22, 6],
    [9, 15, 1, 19, 3, 21, 5, 23],
    [4, 20, 0, 24]       # Círculo externo
]

# Controles
joystick_y = ADC(Pin(26))
button_a = Pin(5, Pin.IN, Pin.PULL_UP)
button_b = Pin(6, Pin.IN, Pin.PULL_UP)
mic = ADC(Pin(28))

# Histórico de dados
history = {
    "temp": [22] * Config.HISTORY_SIZE,
    "hum": [50] * Config.HISTORY_SIZE,
    "db": [40] * Config.HISTORY_SIZE
}

# Inicializa o LoRa
try:
    lora = LoRa(RFM95_SPIBUS, RFM95_INT, CLIENT_ADDRESS, RFM95_CS, reset_pin=RFM95_RST, freq=RF95_FREQ, tx_power=20, modem_config=ModemConfig.Bw125Cr45Sf128)
    print("LoRa inicializado com sucesso!")
except Exception as e:
    print(f"Erro ao inicializar LoRa: {e}")
    lora = None # Define lora como None para indicar falha

# ========================
# Configuração Bluetooth
# ========================
class BitDogBLE:
    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._connected = False
        self._conn_handle = None

        # Configuração de segurança
        try:
            self._ble.config(security=3)
        except Exception as e:
            print("Config security error:", e)
        
        # Registro do serviço com propriedades corretas
        env_service = (
            ENV_SERVICE_UUID,
            [
                (TEMP_CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,),
                (HUM_CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,),
                (SOUND_CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,),
            ]
        )
        
        services = (env_service,)
        ((self._temp_char, self._hum_char, self._sound_char),) = self._ble.gatts_register_services(services)
        
        # Configura os formatos dos dados
        self._ble.gatts_write(self._temp_char, struct.pack('<h', 0))  # Int16
        self._ble.gatts_write(self._hum_char, struct.pack('<h', 0))    # UInt8
        self._ble.gatts_write(self._sound_char, struct.pack('<h', 0)) # UInt8 (dB)
        
        self._ble.irq(self._irq)
        self._advertise()

    def _advertise(self):
        adv_data = advertising_payload(
            name=Config.BLE_NAME,
            services=[ENV_SERVICE_UUID],
            appearance=0x0341  # Generic Sensor
        )
        self._ble.gap_advertise(100000, adv_data=adv_data)
        print("Aguardando conexão BLE...")


    def _irq(self, event, data):
        if event == 1:  # Central conectado
            self._connected = True
            self._conn_handle = data[0]  # salva conn_handle
            print("Dispositivo BLE conectado!")
            self._ble.gap_advertise(None)

        elif event == 2:  # Central desconectado
            self._connected = False
            self._conn_handle = None
            print("Dispositivo BLE desconectado!")
            self._advertise()


    def update_data(self, temp, hum, db):
        try:
            temp_int = int(temp * 100)  # Temperatura em centésimos de grau
            hum_int = int(hum * 100)    # Umidade
            db_int = int(db)            # Som

            self._ble.gatts_write(self._temp_char, struct.pack('<h', temp_int))
            self._ble.gatts_write(self._hum_char, struct.pack('<h', hum_int))
            self._ble.gatts_write(self._sound_char, struct.pack('<h', db_int))

            if self._connected and self._conn_handle is not None:
                self._ble.gatts_notify(self._conn_handle, self._temp_char)
                self._ble.gatts_notify(self._conn_handle, self._hum_char)
                self._ble.gatts_notify(self._conn_handle, self._sound_char)

        except Exception as e:
            print("Erro ao enviar dados BLE:", e)

# ========================
# Funções LoRa
# ========================
def send_lora_message(temp, hum, db):
    global lora
    if lora:
        try:
            # Converte os dados em uma string formatada para envio LoRa
            message_str = f"T:{temp:.1f},H:{hum:.1f},D:{db:.1f}"
            message_bytes = message_str.encode('utf-8')
            
            print(f"Tentando enviar LoRa: {message_str}")
            if lora.send_to_wait(message_bytes, SERVER_ADDRESS):
                print("Mensagem LoRa enviada com sucesso!")
            else:
                print("Falha ao enviar a mensagem LoRa.")
        except Exception as e:
            print(f"Erro ao enviar dados via LoRa: {e}")
    else:
        print("LoRa não está inicializado. Dados não enviados via LoRa.")

# ========================
# Funções de Visualização
# ========================
def show_connection_status(connected):
    """Mostra status de conexão na matriz de LEDs"""
    np.fill((0, 0, 0))
    
    if connected:
        color = Config.COLOR_CONNECTED
        # Padrão conectado (cruz + cantos)
        leds = [12, 6, 8, 16, 18, 0, 4, 20, 24]
    else:
        color = Config.COLOR_WAITING
        # Padrão espera (cruz central)
        leds = [12, 6, 8, 16, 18]
    
    for led in leds:
        np[led] = color
    np.write()

def show_noise(db, classification):
    """Exibe ruído como círculos concêntricos"""
    np.fill((0, 0, 0))
    
    level = min(4, max(0, int((db - 40) / 10)))
    if (level <= 1):
        color = (0, 50, 0)
    elif (level <= 3):
        color = (50, 50, 0)
    else:
        color = (50, 0, 0)    
    
    for i in range(level + 1):
        for led in NOISE_LEVELS[i]:
            np[led] = color

    np.write()

def show_temperature(temp):
    np.fill((0, 0, 0))
    
    # Define faixas de temperatura
    cold_threshold = 15  # °C
    hot_threshold = 30   # °C
    
    if temp <= cold_threshold:
        # Só azul (frio)
        r, g, b = 0, 0, 50
        levels = 1
    elif temp >= hot_threshold:
        # Só vermelho (quente)
        r, g, b = 50, 0, 0
        levels = 5
    else:
        # Interpolação entre azul e vermelho
        ratio = (temp - cold_threshold) / (hot_threshold - cold_threshold)
        r = int(50 * ratio)
        b = int(50 * (1 - ratio))
        g = 0
        levels = 1 + int(4 * ratio)  # Níveis intermediários
    
    # Acende os LEDs
    for row in range(levels):
        for col in range(5):
            np[LED_MATRIX[4-row][col]] = (r, g, b)
    
    np.write()

def show_humidity(hum):
    # Calcula o número de LEDs a acender
    num_on = int(hum / 4)
    # Limita entre 0 e NUM_LEDS
    num_on = max(0, min(num_on, 25))
    # Flatten da matriz de LEDs em ordem
    ordered_leds = [led for row in LED_MATRIX for led in row]
    for idx, led_index in enumerate(ordered_leds):
        if idx < num_on:
            # Exemplo de cor para umidade: azul (RGB)
            np[led_index] = (0, 0, 50)
        else:
            np[led_index] = (0, 0, 0)
    np.write()

def draw_graph(data, y_pos, height, color):
    min_val = min(data)
    max_val = max(data)
    range_val = max_val-min_val if max_val != min_val else 1
    
    for i in range(len(data)-1):
        x1 = int(i*(128/(Config.HISTORY_SIZE-1)))
        y1 = y_pos + height - int((data[i]-min_val)*height/range_val)
        x2 = int((i+1)*(128/(Config.HISTORY_SIZE-1)))
        y2 = y_pos + height - int((data[i+1]-min_val)*height/range_val)
        oled.line(x1,y1,x2,y2,color)

def update_display(mode, value, classification):
    oled.fill(0)
    titles = {
        0: ("Ruido", "dB", history["db"], Config.DB_IDEAL),
        1: ("Temp", "C", history["temp"], Config.TEMP_IDEAL),
        2: ("Umidade", "%", history["hum"], Config.HUM_IDEAL)
    }
    title, unit, data, ideal = titles[mode]
    
    oled.text(f"{title}: {value:.1f}{unit}", 0, 0)
    oled.text(f"Status: {classification}", 0, 12)
    
    draw_graph(data, 20, 40, 1)
    
    try:
        oled.hline(0, 20+40-int((ideal[0]-min(data))*40//(max(data)-min(data))), 128, 1)
        oled.hline(0, 20+40-int((ideal[1]-min(data))*40//(max(data)-min(data))), 128, 1)
    except:
        pass
    
    oled.show()

def classify(value, ranges):
    if value < ranges[0]:
        return "Alerta"
    elif ranges[0] <= value <= ranges[1]:
        return "Ideal"
    else:
        return "Aceitavel"

# ========================
# Funções de Sensoriamento
# ========================
def get_decibels(samples):
    mean = sum(samples)/len(samples)
    squared = [(s-mean)**2 for s in samples]
    rms = math.sqrt(sum(squared)/len(samples))
    voltage_rms = (rms/4095)*3.3
    return int(20*math.log10(voltage_rms/0.00002)) if voltage_rms > 0 else 0

def read_sensors():
    
    temp = aht20.temperature  # Lê a temperatura do AHT20
    hum = aht20.relative_humidity   # Lê a umidade do AHT20
    
    # Leitura real do microfone
    samples = [mic.read_u16()>>4 for _ in range(Config.NUM_SAMPLES)]
    db = get_decibels(samples)
    
    # Atualiza histórico
    for key, value in zip(["temp", "hum", "db"], [temp, hum, db]):
        history[key].append(value)
        history[key] = history[key][-Config.HISTORY_SIZE:]
    
    return temp, hum, db

def main():
    try:
        # Inicializa BLE
        ble = BitDogBLE()
        
        # Espera por conexão com feedback visual
        oled.fill(0)
        oled.text("Aguardando", 0, 10)
        oled.text("conexao BLE...", 0, 25)
        oled.show()
        
        last_blink = utime.time()
        show_conn = False
        
        while not ble._connected:
            if utime.time() - last_blink > 0.5:
                show_conn = not show_conn
                show_connection_status(show_conn)
            # Verifica se LoRa está inicializado e exibe na tela
            if lora:
                oled.text("LoRa OK", 0, 40)
            else:
                oled.text("LoRa FALHA", 0, 40)
            oled.show()
            last_blink = utime.time()
            utime.sleep_ms(100)
            
        # Conexão estabelecida
        show_connection_status(True)
        oled.fill(0)
        oled.text("Conectado!", 0, 20)
        if lora:
            oled.text("LoRa OK", 0, 40)
        else:
            oled.text("LoRa FALHA", 0, 40)
        oled.show()
        utime.sleep(1)
        
        # Loop principal
        current_mode = 0
        modes = [
            (show_noise, "db", Config.DB_IDEAL),
            (show_temperature, "temp", Config.TEMP_IDEAL),
            (show_humidity, "hum", Config.HUM_IDEAL)
        ]
        last_update_time = utime.time() # Variável para controlar o intervalo de atualização
        
        while True:
            temp, hum, db = read_sensors()
            
            # Atualiza BLE e LoRa em um intervalo comum
            if utime.time() - last_update_time > Config.SENSOR_UPDATE_INTERVAL:
                ble.update_data(temp, hum, db)
                send_lora_message(temp, hum, db) # Envia dados via LoRa
                last_update_time = utime.time()
            
            # Controle de modo via joystick
            y_val = joystick_y.read_u16()
            # Adiciona uma pequena histerese para evitar mudança de modo muito rápida
            if y_val < 24000 and current_mode != 0: # Para cima (modo anterior)
                current_mode = (current_mode - 1 + 3) % 3 # +3 para garantir que o resultado seja positivo
                utime.sleep_ms(300) # Pequeno delay para debounce
            elif y_val > 41000 and current_mode != 2: # Para baixo (próximo modo)
                current_mode = (current_mode + 1) % 3
                utime.sleep_ms(300) # Pequeno delay para debounce
            
            # Atualização da exibição
            display_func, key, ideal = modes[current_mode]
            current_value = {"temp": temp, "hum": hum, "db": db}[key]
            classification = classify(current_value, ideal)
            
            if key == "db":
                show_noise(current_value, classification)
            else:
                display_func(current_value)
            
            update_display(current_mode, current_value, classification)
            
            utime.sleep_ms(100) # Loop mais rápido para leitura de joystick e display
            
    except Exception as e:
        print("Erro fatal:", e)
        oled.fill(0)
        oled.text("Erro:", 0, 10)
        oled.text(str(e)[:20], 0, 25)
        oled.show()
        utime.sleep(5)
        machine.reset()

if __name__ == "__main__":
    main()
