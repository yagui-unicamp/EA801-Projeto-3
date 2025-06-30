# Sensor de Conforto Ambiental com LoRaWAN e BLE

## 📖 Sobre o Projeto

Este projeto consiste no desenvolvimento de um sistema de monitoramento de conforto ambiental de dois nós, como parte da disciplina de Laboratório de Sistemas Embarcados (EA801).

O **Nó Sensor (Transmissor)** é um dispositivo embarcado que utiliza uma placa BitDogLab (baseada em RP2040) para coletar dados de temperatura, umidade e nível de ruído. Ele oferece uma rica interface de usuário local com um display OLED, uma matriz de LEDs NeoPixel e um joystick para interação. Os dados coletados são transmitidos por duas vias de comunicação:

* **LoRa:** Para comunicação de longo alcance e baixo consumo com um nó receptor.
* **Bluetooth Low Energy (BLE):** Para comunicação de curto alcance com smartphones ou outros dispositivos compatíveis.

O **Nó Receptor** é uma estação base simples que recebe os dados via LoRa, processa as informações e as exibe em um display OLED local.

## ✨ Funcionalidades Principais

* **Coleta de Múltiplos Sensores:** Medição de temperatura e umidade com o sensor AHT20 e nível de ruído com um microfone analógico.
* **Comunicação Dupla:** Transmissão de dados simultânea via LoRa e Bluetooth Low Energy (BLE).
* **Interface Visual Rica:**
    * **Display OLED:** Exibe dados em tempo real, status do sistema e gráficos históricos.
    * **Matriz de LEDs (NeoPixel):** Fornece feedback visual intuitivo para o status da conexão, nível de ruído, temperatura e umidade.
* **Classificação de Conforto:** O sistema analisa os dados localmente e os classifica como "Ideal", "Aceitável" ou "Alerta".
* **Interatividade:** Um joystick permite ao usuário alternar entre os diferentes modos de visualização (ruído, temperatura, umidade).

## 🏗️ Arquitetura do Sistema

O sistema é composto por dois nós principais:

1.  **Nó Sensor (Transmissor):**
    * Lê os sensores (AHT20, Microfone).
    * Processa e classifica os dados.
    * Exibe informações no OLED e na matriz de LEDs.
    * Envia os dados via LoRa e anuncia via BLE.
2.  **Nó Receptor (Base):**
    * Fica em modo de escuta contínua (RX).
    * Recebe os pacotes LoRa enviados pelo nó sensor.
    * Decodifica a mensagem e exibe os dados de temperatura, umidade e ruído em seu display OLED.

## 🛠️ Tecnologias e Hardware

### Hardware Utilizado
* **Placa de Desenvolvimento:** BitDogLab (ou qualquer placa baseada em RP2040 com os periféricos necessários).
* **Sensores (Nó Sensor):**
    * Sensor de Temperatura e Umidade: `AHT20`
    * Sensor de Ruído: Microfone analógico conectado a uma porta ADC.
* **Módulo de Comunicação:** Módulo LoRa `RFM95W`.
* **Interface de Usuário (Nó Sensor):**
    * Display `OLED SSD1306` (128x64 I2C).
    * Matriz de LEDs `NeoPixel` 5x5.
    * Joystick analógico e botões.

### Software e Protocolos
* **Firmware:** `MicroPython`
* **Comunicação Sem Fio:** `LoRa` (ponto a ponto) e `Bluetooth Low Energy (BLE)`.
* **Bibliotecas MicroPython:** `ulora`, `ssd1306`, `ahtx0`, `neopixel`.

## ⚙️ Configuração e Instalação

### Pré-requisitos
* Duas placas BitDogLab/RP2040.
* Firmware MicroPython instalado em ambas as placas.
* Thonny IDE ou outra ferramenta para interagir com o REPL e transferir arquivos.

### Bibliotecas Necessárias
Antes de executar, certifique-se de que todas as bibliotecas listadas nos arquivos `main.py` estejam presentes na pasta `/lib` de ambas as placas. As principais são:
* `ulora.py`
* `ssd1306.py`
* `ahtx0.py`
* `neopixel.py`
* `ble_advertising.py`

### 1. Configuração do Nó Sensor (Transmissor)
1.  Copie o código do transmissor para um arquivo `main.py`.
2.  Transfira o `main.py` e as bibliotecas necessárias para a placa.
3.  Verifique as configurações de pinos e LoRa no início do código, especialmente `RF95_FREQ` (ex: `915.0` MHz para as Américas).

### 2. Configuração do Nó Receptor
1.  Copie o código do receptor para um arquivo `main.py`.
2.  Transfira o `main.py` e as bibliotecas para a segunda placa.
3.  Garanta que as configurações de LoRa (`RF95_FREQ`, `CLIENT_ADDRESS`, `SERVER_ADDRESS`) sejam compatíveis com as do transmissor.

## 🚀 Como Usar

### Nó Sensor
1.  Energize a placa. O display mostrará "Iniciando..." e depois "Aguardando conexão BLE...". A matriz de LEDs piscará em azul.
2.  Use um aplicativo de scanner BLE (como o nRF Connect) no seu celular para se conectar ao dispositivo chamado `BitDogLab-Sensor`.
3.  Após a conexão BLE, a matriz de LEDs ficará verde e o display mostrará "Conectado!". O sistema começará a coletar e exibir os dados.
4.  Use o **joystick para cima e para baixo** para alternar entre as telas de Ruído, Temperatura e Umidade.
5.  Os dados serão enviados via LoRa e BLE a cada 2 segundos (definido em `SENSOR_UPDATE_INTERVAL`).

### Nó Receptor
1.  Energize a placa. O display mostrará "Receptor LoRa - Aguardando...".
2.  O nó ficará automaticamente em modo de escuta.
3.  Quando uma mensagem LoRa do nó sensor for recebida, os dados de temperatura, umidade e ruído serão exibidos no display OLED.

## 📦 Estrutura da Mensagem LoRa

O nó sensor envia os dados para o receptor em um formato de string simples, codificado em UTF-8.

**Formato:** `T:<temperatura>,H:<umidade>,D:<ruido>`

**Exemplo:** `T:23.5,H:58.2,D:65.1`

O receptor decodifica essa string para extrair os valores e exibi-los.

## 👥 Autores
* **Lucas Yagui** - 240211
* **Gabriel Guimarães Dourado** - 177212
