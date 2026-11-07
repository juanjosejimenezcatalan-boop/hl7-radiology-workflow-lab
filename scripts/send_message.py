#!/usr/bin/env python3
"""Send one HL7 file via MLLP and print its ACK."""
from __future__ import annotations
import argparse
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.hl7_server import extract_mllp_frames, mllp_frame

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("message", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2576, help="Host MLLP port (default: 2576)")
    args = parser.parse_args()
    with socket.create_connection((args.host, args.port), timeout=5) as client:
        client.sendall(mllp_frame(args.message.read_text(encoding="utf-8")))
        response = client.recv(4096)
    frames, remainder = extract_mllp_frames(response)
    if remainder or not frames:
        raise SystemExit("No complete MLLP ACK received")
    print(frames[0].replace("\r", "\n"), end="")

if __name__ == "__main__":
    main()

