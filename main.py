from __future__ import annotations

import argparse
import logging
import os
import threading
from pathlib import Path

from backend.api_server import create_app
from backend.controller import ControllerConfig, IntegratedTrafficController


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Integrated RL traffic signal control controller")
    parser.add_argument("--sumo-cfg", default="simulation/sumo/corridor.sumocfg")
    parser.add_argument("--interval", type=float, default=2.0, help="Decision loop interval in seconds")
    parser.add_argument("--serial-port", default=None, help="COM port for Arduino/ESP32")
    parser.add_argument("--serve-api", action="store_true", help="Expose REST API for dashboard")
    parser.add_argument("--api-port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    expected_root = Path(__file__).resolve().parent
    if Path.cwd().resolve() != expected_root:
        os.chdir(expected_root)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logging.getLogger(__name__).info("RUN RULE: running from %s", Path.cwd())

    args = parse_args()
    cfg = ControllerConfig(
        decision_interval_sec=args.interval,
        sumo_cfg=args.sumo_cfg,
        serial_port=args.serial_port,
    )

    controller = IntegratedTrafficController(cfg)

    if args.serve_api:
        app = create_app(controller.telemetry)
        api_thread = threading.Thread(
            target=lambda: app.run(host="0.0.0.0", port=args.api_port, debug=False, use_reloader=False),
            daemon=True,
        )
        api_thread.start()

    controller.run_forever()


if __name__ == "__main__":
    main()
