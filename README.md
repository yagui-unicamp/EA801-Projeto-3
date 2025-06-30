# Sensor de Conforto Ambiental com LoRa e BLE (EA801 - Projeto 3)

## 📖 Sobre o Projeto

Este repositório contém o projeto final da disciplina EA801 - Laboratório de Sistemas Embarcados da UNICAMP. O objetivo foi desenvolver um sistema completo de monitoramento de conforto ambiental utilizando a placa BitDogLab (baseada no RP2040), com comunicação sem fio via LoRa e Bluetooth Low Energy (BLE).

O sistema é composto por dois nós:
* **Nó Transmissor:** Um dispositivo sensor que coleta dados de temperatura, umidade e nível de ruído. Ele possui uma interface de usuário rica com display OLED e matriz de LEDs para feedback visual e transmite os dados coletados.
* **Nó Receptor:** Uma estação base que recebe os dados do transmissor via LoRa e os exibe em um display OLED local.

## ✨ Funcionalidades Principais

* **Coleta de Múltiplos Sensores:** Medição de temperatura e umidade (`AHT20`) e nível de ruído (microfone ADC).
* **Comunicação Dupla:** Transmissão de dados via LoRa para longo alcance e via Bluetooth Low Energy (BLE) para conexão local com smartphones.
* **Interface Visual Rica:**
    * **Display OLED:** Exibe dados em tempo real, status do sistema e gráficos históricos das medições.
    * **Matriz de LEDs NeoPixel:** Fornece feedback visual intuitivo para status de conexão, níveis de ruído, temperatura e umidade.
* **Classificação de Conforto:** O sistema analisa os dados localmente e classifica o ambiente como "Ideal", "Aceitável" ou "Alerta".
* **Interatividade:** Um joystick permite ao usuário alternar facilmente entre os diferentes modos de visualização no nó transmissor.

## 📂 Estrutura de Arquivos

O repositório está organizado de forma a separar claramente a lógica de cada um dos nós do sistema.

```
.
├── Receptor/
│   ├── main.py           # Código principal do nó receptor
│   └── libs/             # Bibliotecas necessárias para o receptor
│       ├── ssd1306.py
│       └── ulora.py
├── Transmissor/
│   ├── main.py           # Código principal do nó transmissor/sensor
│   └── libs/             # Bibliotecas necessárias para o transmissor
│       ├── ahtx0.py
│       ├── ble_advertising.py
│       ├── neopixel.py
│       ├── ssd1306.py
│       └── ulora.py
├── .gitignore
├── LICENSE
└── README.md
```

## 🛠️ Tecnologias e Hardware

* **Hardware:**
    * 2x Placas de Desenvolvimento BitDogLab (RP2040)
    * Sensor de Temperatura e Umidade: `AHT20`
    * Sensor de Ruído: Microfone analógico
    * Módulo de Comunicação: LoRa `RFM95W`
    * Display `OLED SSD1306` (128x64 I2C)
    * Matriz de LEDs `NeoPixel` 5x5
* **Software e Protocolos:**
    * Firmware: `MicroPython`
    * Comunicação Sem Fio: `LoRa` (ponto a ponto) e `Bluetooth Low Energy (BLE)`

## 🚀 Configuração e Instalação

Siga os passos abaixo para colocar o sistema em funcionamento.

### Pré-requisitos
* Duas placas BitDogLab/RP2040 com firmware MicroPython instalado.
* Thonny IDE ou outra ferramenta para interagir com as placas e transferir os arquivos.

### Passo 1: Obter os Arquivos
Clone este repositório para o seu computador:
```bash
git clone [https://github.com/yagui-unicamp/EA801-Projeto-3.git](https://github.com/yagui-unicamp/EA801-Projeto-3.git)
```

### Passo 2: Configuração do Nó Transmissor
1.  Conecte uma das placas ao seu computador.
2.  No Thonny IDE, navegue até a pasta `Transmissor` que você acabou de clonar.
3.  Faça o upload de **todo o conteúdo** da pasta `Transmissor` (ou seja, o arquivo `main.py` e a pasta `libs` com seus arquivos) para a **raiz** da placa.
4.  Reinicie a placa (pressione `Ctrl+D` no Thonny).

### Passo 3: Configuração do Nó Receptor
1.  Conecte a segunda placa ao seu computador.
2.  No Thonny IDE, navegue até a pasta `Receptor`.
3.  Faça o upload de **todo o conteúdo** da pasta `Receptor` (o arquivo `main.py` e a pasta `libs`) para a **raiz** da segunda placa.
4.  Reinicie a placa.

### Passo 4: Execução
* O **Nó Transmissor** irá iniciar e procurar por uma conexão BLE. Use um app como o nRF Connect para se conectar a ele. Após a conexão, ele começará a transmitir os dados.
* O **Nó Receptor** iniciará automaticamente em modo de escuta e exibirá os dados no OLED assim que recebê-los.

## 📡 Estrutura da Mensagem LoRa

O transmissor envia os dados para o receptor como uma string formatada, codificada em UTF-8.

**Formato:** `T:<temperatura>,H:<umidade>,D:<ruido>`

**Exemplo de Payload:** `T:24.1,H:56.1,D:62.0`

## 👥 Autores

* **Lucas Yagui** - [yagui-unicamp](https://github.com/yagui-unicamp)
* **Gabriel Guimarães Dourado**
