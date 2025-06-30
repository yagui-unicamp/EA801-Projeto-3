# --- Importação das Bibliotecas ---
from machine import Pin, SoftI2C, PWM
from time import sleep
from ulora import LoRa, ModemConfig, SPIConfig # Biblioteca para comunicação LoRa
from ssd1306 import SSD1306_I2C # Biblioteca para o display OLED
import os
import time

# --- Configuração dos Periféricos ---

# Configuração do Display OLED
# Define os pinos I2C para a comunicação com o display
i2c = SoftI2C(scl=Pin(15), sda=Pin(14))
# Inicializa o objeto do display OLED com resolução 128x64 pixels
oled = SSD1306_I2C(128, 64, i2c)

# Configuração dos Pinos dos LEDs
verde = Pin(11, Pin.OUT)
azul = Pin(12, Pin.OUT)
vermelho = Pin(13, Pin.OUT)

# --- Parâmetros da Comunicação LoRa ---
RFM95_RST = 28      # Pino de Reset do módulo LoRa
RFM95_SPIBUS = SPIConfig.rp2_0  # Define o barramento SPI a ser usado (específico para Raspberry Pi Pico)
RFM95_CS = 17       # Pino "Chip Select" para comunicação SPI
RFM95_INT = 20      # Pino de interrupção (DIO0) do módulo LoRa
RF95_FREQ = 915.0   # Frequência de operação em MHz (ex: 915.0 para US, 868.0 para EU, 433.0 para Ásia)
RF95_POW = 20       # Potência de transmissão em dBm (2 a 20)
CLIENT_ADDRESS = 1  # Endereço do nó que envia (nó sensor)
SERVER_ADDRESS = 2  # Endereço deste nó (nó receptor)

# --- Função de Callback para Recebimento de Dados ---

# Esta função é chamada automaticamente toda vez que uma mensagem LoRa é recebida.
def on_recv(payload):
    """
    Processa a mensagem recebida via LoRa.
    
    Args:
        payload: Objeto contendo os dados da mensagem (payload.message),
                 RSSI (payload.rssi) e SNR (payload.snr).
    """
    oled.fill(0)  # Limpa completamente o conteúdo do display OLED

    # Decodifica a mensagem de bytes para uma string no formato UTF-8
    message = payload.message.decode('utf-8')
    print("Mensagem Recebida:", message) # Imprime a mensagem no console serial

    # Tenta processar a mensagem como dados de sensores (formato "T:xx,H:xx,D:xx")
    try:
        parts = message.split(',') # Separa a string pela vírgula. Ex: ["T:25.3", "H:60.1", "D:75.5"]

        # Extrai as strings de cada sensor
        temp_str = parts[0] # "T:25.3"
        hum_str = parts[1]  # "H:60.1"
        db_str = parts[2]   # "D:75.5"

        # Extrai os valores numéricos, separando pelo ":" e convertendo para float
        temp_value = float(temp_str.split(':')[1])
        hum_value = float(hum_str.split(':')[1])
        db_value = float(db_str.split(':')[1])

        # Exibe os valores formatados no display OLED
        oled.text(f"Temp: {temp_value:.1f} C", 0, 0, 1)
        oled.text(f"Umidade: {hum_value:.1f}%", 0, 10, 1)
        oled.text(f"Decibeis: {db_value:.1f}dB", 0, 20, 1)

    except (IndexError, ValueError):
        # Se a mensagem não estiver no formato esperado, exibe a mensagem bruta
        oled.text("Msg recebida:", 0, 0, 1)
        oled.text(message, 0, 10, 1)
        print("Formato da mensagem inesperado.")

    # Atualiza o display com o novo conteúdo
    oled.show()

    # --- Controle dos LEDs e Buzzer com base em mensagens simples ---
    # Esta parte do código permite controlar o receptor com comandos simples (1, 2, 3, 4)
    # enviados pelo transmissor, útil para testes e depuração.
    if payload.message == b'1':
        vermelho.on()
        verde.off()
        azul.off()

    if payload.message == b'2':
        vermelho.off()
        verde.on()
        azul.off()
    
    if payload.message == b'3':
        vermelho.off()
        verde.off()
        azul.on()
        # A função play_ex_notes() não está definida neste arquivo.
        # Provavelmente seria uma função para tocar notas em um buzzer.
        # play_ex_notes() 
    
    if payload.message == b'4':
        vermelho.off()
        verde.off()
        azul.off()
        # Desliga o buzzer (o objeto buzzer_pwm não está definido aqui)
        # buzzer_pwm.duty_u16(0)


# --- Inicialização do Rádio LoRa ---
# Cria o objeto LoRa com todas as configurações definidas anteriormente
lora = LoRa(RFM95_SPIBUS, RFM95_INT, SERVER_ADDRESS, RFM95_CS,
            reset_pin=RFM95_RST, freq=RF95_FREQ, tx_power=RF95_POW, acks=True)

# Associa a função 'on_recv' ao evento de recebimento de pacotes
lora.on_recv = on_recv

# Coloca o rádio em modo de recebimento contínuo
lora.set_mode_rx()

# --- Configuração dos Botões (não utilizados no loop principal) ---
botao_a = Pin(5, Pin.IN, Pin.PULL_UP)
botao_b = Pin(6, Pin.IN, Pin.PULL_UP)

# --- Mensagem Inicial ---
# Exibe uma mensagem de boas-vindas no OLED ao iniciar
oled.fill(0)
oled.text("Receptor LoRa", 0, 0, 1)
oled.text("Aguardando...", 0, 20, 1)
oled.show()

# --- Loop Principal ---
# O programa entra em um loop infinito para se manter ativo.
# A recepção de dados ocorre por interrupções, gerenciadas pela biblioteca ulora.
# O sleep(0.1) ajuda a reduzir o consumo de processamento.
while True:
    sleep(0.1)