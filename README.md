# rplidar-uv

A minimal real-time terminal radar display for the **RPLIDAR A1M8** laser range scanner, managed with [uv](https://github.com/astral-sh/uv).

## What it does

Connects to an RPLIDAR A1M8 over USB, continuously reads 360° scan data, and renders two live panels in the terminal:

- **Radar View** – a top-down ASCII dot-map of detected obstacles (up to 3 m range).
- **Status Panel** – nearest distance in the front, left, and right sectors; number of close points (< 1 m); a simple risk score; device health; and firmware version.

Press **Ctrl+C** to stop cleanly.

## Requirements

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- RPLIDAR A1M8 connected via a CP2102 USB-to-UART adapter

The default port is:

```
/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0
```

Edit the `PORT` constant at the top of `plot.py` if your device appears at a different path.

## Run

```bash
uv run plot.py
```

`uv` will automatically create a virtual environment and install the required dependencies ([`rplidar`](https://pypi.org/project/rplidar/) and [`rich`](https://pypi.org/project/rich/)) on the first run.
