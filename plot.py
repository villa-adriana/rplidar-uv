import math
import signal
import time
from rplidar import RPLidar

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from rich.text import Text

PORT = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"

running = True


def handle_sigint(sig, frame):
    global running
    running = False


def polar_to_cart(angle_deg, distance_mm):
    theta = math.radians(angle_deg)
    r = distance_mm / 1000.0
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    return x, y


def angle_in_sector(angle, start, end):
    if start <= end:
        return start <= angle <= end
    return angle >= start or angle <= end


def sector_filter(scan, start_deg, end_deg):
    return [
        d for (_, a, d) in scan
        if d > 0 and angle_in_sector(a, start_deg, end_deg)
    ]


def fmt_distance(mm):
    return f"{mm/1000:.2f} m" if mm is not None else "—"


def build_radar_text(scan, max_range_mm=3000, width=61, height=25):
    grid = [[" " for _ in range(width)] for _ in range(height)]
    cx = width // 2
    cy = height - 1

    for (_, angle, dist) in scan:
        if dist <= 0 or dist > max_range_mm:
            continue

        x, y = polar_to_cart(angle, dist)

        gx = int(cx + (x / (max_range_mm / 1000)) * (width // 2))
        gy = int(cy - (y / (max_range_mm / 1000)) * (height - 1))

        if 0 <= gx < width and 0 <= gy < height:
            grid[gy][gx] = "•"

    grid[cy][cx] = "R"

    lines = ["".join(row) for row in grid]
    return Text("\n".join(lines))


def build_status_panel(front_min, left_min, right_min, density, risk, info, health):
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right")
    table.add_column(justify="left")

    table.add_row("Front:", fmt_distance(front_min))
    table.add_row("Left:", fmt_distance(left_min))
    table.add_row("Right:", fmt_distance(right_min))
    table.add_row("Close pts (<1m):", str(density))
    table.add_row("Risk score:", str(risk))
    table.add_row("Health:", str(health))
    table.add_row("FW:", f"{info['firmware']}")

    return Panel(table, title="RPLIDAR Status", border_style="cyan")


def main():
    global running
    signal.signal(signal.SIGINT, handle_sigint)

    lidar = RPLidar(PORT)

    info = lidar.get_info()
    health = lidar.get_health()

    layout = Layout()
    layout.split_column(
        Layout(name="status", size=10),
        Layout(name="radar"),
    )

    try:
        with Live(layout, refresh_per_second=15, screen=True):
            for scan in lidar.iter_scans(max_buf_meas=500):
                if not running:
                    break

                front = sector_filter(scan, 330, 30)
                left = sector_filter(scan, 60, 120)
                right = sector_filter(scan, 240, 300)

                def min_or_none(values):
                    return min(values) if values else None

                front_min = min_or_none(front)
                left_min = min_or_none(left)
                right_min = min_or_none(right)

                close_points = [d for (_, _, d) in scan if 0 < d < 1000]
                density = len(close_points)

                risk = 0
                if front_min is not None and front_min < 500:
                    risk += 2
                if density > 40:
                    risk += 1

                layout["status"].update(
                    build_status_panel(
                        front_min,
                        left_min,
                        right_min,
                        density,
                        risk,
                        info,
                        health,
                    )
                )

                layout["radar"].update(
                    Panel(
                        build_radar_text(scan),
                        title="Radar View (Top-Down)",
                        border_style="green",
                    )
                )

                time.sleep(0.05)

    finally:
        try:
            lidar.stop()
        except Exception:
            pass
        try:
            lidar.stop_motor()
        except Exception:
            pass
        lidar.disconnect()


if __name__ == "__main__":
    main()

