# FlexRadio Spot Broadcaster (EC5W v0.1b)

<img width="693" height="638" alt="image" src="https://github.com/user-attachments/assets/46c7d65c-7237-4cf7-a59b-3fdb85bd0f4e" />
<img width="1098" height="776" alt="image" src="https://github.com/user-attachments/assets/81cf8b34-64b7-4e3a-8519-b3d24dcd8b1b" />

Download: https://github.com/opalito/FlexRadioSpotBroadcaster/releases/download/master/FlexRadioSpotBroadcaster-0.1b.zip

[English](#english) | [Español](#español)


## English

### Description

FlexRadio Spot Broadcaster connects to a DX Cluster (DXSpider, AR-Cluster, etc.) and forwards spots in N1MM UDP format to SmartSDR/FlexRadio. Spots appear directly on the panadapter.

### Features

- System tray application (runs in background)
- Bilingual interface (English/Spanish)
- Configurable cluster server and port
- Custom command execution on connect and anytime
- Auto-connect on startup option
- Real-time spot log with color coding
- Settings saved automatically (Windows Registry)

### Requirements

- Windows 10/11
- Python 3.8+ (only for running from source)
- SmartSDR with CAT configured for N1MM spots

### SmartSDR CAT Configuration

1. Open SmartSDR CAT
2. Click "Add..."
3. In "Protocol" select **"N1MMSpot"** (important!)
4. UDP port: **12061** (or match your app setting)
5. Click "Save"

### Installation

#### Option A: Run from source

1. Install Python 3.8+ from https://www.python.org/downloads/
2. Install dependencies:
   ```
   pip install PyQt5
   ```
3. Run:
   ```
   python dxspot_forwarder_gui.py
   ```

#### Option B: Compile to .exe

1. Install dependencies:
   ```
   pip install PyQt5 pyinstaller
   ```
2. Compile:
   ```
   python -m PyInstaller --onefile --windowed --name "FlexRadioSpotBroadcaster" --icon=dxspot.ico dxspot_forwarder_gui.py
   ```
3. The executable will be in `dist\FlexRadioSpotBroadcaster.exe`

### Usage

1. Run the application
2. Enter your callsign
3. Configure cluster server (default: dxspider.co.uk:7300)
4. Click "Connect"
5. Spots will appear on your SmartSDR panadapter

### Configuration Options

| Field | Description | Default |
|-------|-------------|---------|
| Server | DX Cluster address | dxspider.co.uk |
| Port | Cluster port | 7300 |
| Callsign | Your callsign for login | (required) |
| Command | Command to execute (+ Send button) | sh/fdx 200 |
| IP Address | UDP destination | 127.0.0.1 |
| UDP Port | SmartSDR CAT port | 12061 |

### Options

- **Minimize to system tray on close**: App keeps running in background
- **Auto-connect on startup**: Connects automatically when app starts
- **Language**: Switch between English and Spanish

### Initial Command

The default command `sh/fdx 200` retrieves the last 200 spots in real-time format. This ensures historical spots are properly parsed and sent to SmartSDR.

Alternative commands:
- `sh/fdx 500` - Last 500 spots
- `sh/dx/100 on 20m` - Last 100 spots on 20m
- `sh/fdx 50 ft8` - Last 50 FT8 spots

Use the **Send** button to execute commands anytime while connected.

### System Tray

- **Double-click**: Show main window
- **Right-click**: Menu (Show, Connect/Disconnect, Exit)
- The app shows connection status in the tray tooltip

### Troubleshooting

**Spots not showing on panadapter:**
1. Verify SmartSDR CAT protocol is "N1MMSpot" (not "SpotsCluster")
2. Check UDP port matches (default 12061)
3. Spots only show within visible panadapter frequency range
4. Check "Levels" slider in SmartSDR Settings → Spots

**Windows SmartScreen warning:**
The .exe is not digitally signed. Click "More info" → "Run anyway". This is normal for unsigned applications.

**Connection fails:**
- Check internet connection
- Try alternative cluster: `dxc.ea4ure.com:7300` or `dx.n1mm.com:7300`

### Settings Storage

Settings are saved in Windows Registry:
```
HKEY_CURRENT_USER\Software\EC5W\FlexRadio Spot Broadcaster\Settings
```

### Author

EC5W - Version 0.1b

73!

---

## Español

### Descripción

FlexRadio Spot Broadcaster conecta a un Cluster DX (DXSpider, AR-Cluster, etc.) y reenvía los spots en formato N1MM UDP a SmartSDR/FlexRadio. Los spots aparecen directamente en el panadapter.

### Características

- Aplicación en system tray (funciona en segundo plano)
- Interfaz bilingüe (Inglés/Español)
- Servidor y puerto del cluster configurables
- Ejecución de comandos al conectar y en cualquier momento
- Opción de auto-conectar al iniciar
- Log de spots en tiempo real con colores
- Configuración guardada automáticamente (Registro de Windows)

### Requisitos

- Windows 10/11
- Python 3.8+ (solo para ejecutar desde código fuente)
- SmartSDR con CAT configurado para spots N1MM

### Configuración de SmartSDR CAT

1. Abre SmartSDR CAT
2. Click en "Add..."
3. En "Protocol" selecciona **"N1MMSpot"** (¡importante!)
4. Puerto UDP: **12061** (o el que configures en la app)
5. Click en "Save"

### Instalación

#### Opción A: Ejecutar desde código fuente

1. Instala Python 3.8+ desde https://www.python.org/downloads/
2. Instala dependencias:
   ```
   pip install PyQt5
   ```
3. Ejecuta:
   ```
   python dxspot_forwarder_gui.py
   ```

#### Opción B: Compilar a .exe

1. Instala dependencias:
   ```
   pip install PyQt5 pyinstaller
   ```
2. Compila:
   ```
   python -m PyInstaller --onefile --windowed --name "FlexRadioSpotBroadcaster" --icon=dxspot.ico dxspot_forwarder_gui.py
   ```
3. El ejecutable estará en `dist\FlexRadioSpotBroadcaster.exe`

### Uso

1. Ejecuta la aplicación
2. Introduce tu indicativo
3. Configura el servidor del cluster (por defecto: dxspider.co.uk:7300)
4. Click en "Conectar"
5. Los spots aparecerán en el panadapter de SmartSDR

### Opciones de Configuración

| Campo | Descripción | Por defecto |
|-------|-------------|-------------|
| Servidor | Dirección del Cluster DX | dxspider.co.uk |
| Puerto | Puerto del cluster | 7300 |
| Indicativo | Tu indicativo para login | (requerido) |
| Comando | Comando a ejecutar (+ botón Enviar) | sh/fdx 200 |
| Dirección IP | Destino UDP | 127.0.0.1 |
| Puerto UDP | Puerto de SmartSDR CAT | 12061 |

### Opciones

- **Minimizar al system tray al cerrar**: La app sigue funcionando en segundo plano
- **Conectar automáticamente al iniciar**: Conecta automáticamente al abrir la app
- **Idioma**: Cambiar entre Inglés y Español

### Comando Inicial

El comando por defecto `sh/fdx 200` obtiene los últimos 200 spots en formato tiempo real. Esto asegura que los spots históricos se parseen correctamente y se envíen a SmartSDR.

Comandos alternativos:
- `sh/fdx 500` - Últimos 500 spots
- `sh/dx/100 on 20m` - Últimos 100 spots en 20m
- `sh/fdx 50 ft8` - Últimos 50 spots FT8

Usa el botón **Enviar** para ejecutar comandos en cualquier momento mientras estés conectado.

### System Tray

- **Doble click**: Mostrar ventana principal
- **Click derecho**: Menú (Mostrar, Conectar/Desconectar, Salir)
- La app muestra el estado de conexión en el tooltip del tray

### Solución de Problemas

**Los spots no aparecen en el panadapter:**
1. Verifica que el protocolo en SmartSDR CAT sea "N1MMSpot" (no "SpotsCluster")
2. Comprueba que el puerto UDP coincida (por defecto 12061)
3. Los spots solo se muestran dentro del rango de frecuencia visible en el panadapter
4. Revisa el slider "Levels" en SmartSDR Settings → Spots

**Aviso de Windows SmartScreen:**
El .exe no está firmado digitalmente. Click en "Más información" → "Ejecutar de todas formas". Es normal para aplicaciones sin firmar.

**Falla la conexión:**
- Comprueba la conexión a internet
- Prueba un cluster alternativo: `dxc.ea4ure.com:7300` o `dx.n1mm.com:7300`

### Almacenamiento de Configuración

La configuración se guarda en el Registro de Windows:
```
HKEY_CURRENT_USER\Software\EC5W\FlexRadio Spot Broadcaster\Settings
```

### Autor

EC5W - Versión 0.1b

73!

---

## Files / Archivos

- `dxspot_forwarder_gui.py` - Main application / Aplicación principal
- `dxspot.ico` - Application icon / Icono de la aplicación
- `crear_exe.bat` - Script to compile .exe / Script para compilar .exe
- `README.md` - This file / Este archivo

## License / Licencia

Free for amateur radio use / Libre para uso radioaficionado
