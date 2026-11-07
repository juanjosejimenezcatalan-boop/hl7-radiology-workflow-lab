"""Small dependency-free MLLP receiver for a synthetic HL7 v2 lab."""
from __future__ import annotations

import argparse
import logging
import socketserver
import time
from dataclasses import dataclass
from datetime import datetime, timezone

VT = b"\x0b"
FS_CR = b"\x1c\x0d"

@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    message_type: str
    control_id: str
    reason: str = ""

def parse_segments(message: str) -> dict[str, list[str]]:
    segments: dict[str, list[str]] = {}
    for line in message.replace("\n", "\r").split("\r"):
        if line:
            fields = line.split("|")
            segments.setdefault(fields[0], fields)
    return segments

def field(segments: dict[str, list[str]], name: str, number: int) -> str:
    fields = segments.get(name, [])
    return fields[number] if len(fields) > number else ""

def validate(message: str) -> ValidationResult:
    """Validate the deliberately small teaching profile used by this lab."""
    segments = parse_segments(message)
    if "MSH" not in segments:
        return ValidationResult(False, "UNKNOWN", "", "Missing MSH segment")
    message_type, control_id = field(segments, "MSH", 8), field(segments, "MSH", 9)
    if not message_type:
        return ValidationResult(False, "UNKNOWN", control_id, "Missing MSH-9 message type")
    if not control_id:
        return ValidationResult(False, message_type, "", "Missing MSH-10 control ID")
    if message_type not in {"ADT^A04", "ORM^O01", "ORU^R01"}:
        return ValidationResult(False, message_type, control_id, "Unsupported message type")
    if "PID" not in segments:
        return ValidationResult(False, message_type, control_id, "Missing PID segment")
    if not field(segments, "PID", 3).split("^")[0]:
        return ValidationResult(False, message_type, control_id, "Missing PID-3 PatientID")
    requirements = {
        "ADT^A04": ("PID",),
        "ORM^O01": ("PID", "ORC", "OBR"),
        "ORU^R01": ("PID", "ORC", "OBR", "OBX"),
    }
    for segment in requirements[message_type]:
        if segment not in segments:
            return ValidationResult(False, message_type, control_id, f"Missing {segment} segment")
    return ValidationResult(True, message_type, control_id)

def ack(result: ValidationResult) -> str:
    code = "AA" if result.accepted else "AE"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S+0000")
    message_parts = result.message_type.split("^")
    trigger_event = message_parts[1] if len(message_parts) > 1 else "U01"
    lines = [
        f"MSH|^~\\&|HL7_LAB|RADIOLOGY|SENDER|HOSPITAL|{timestamp}||ACK^{trigger_event}^ACK|ACK-{result.control_id or 'UNKNOWN'}|P|2.5.1",
        f"MSA|{code}|{result.control_id}",
    ]
    if not result.accepted:
        lines.append(f"ERR|||{result.reason}")
    return "\r".join(lines) + "\r"

def mllp_frame(message: str) -> bytes:
    return VT + message.encode("utf-8") + FS_CR

def extract_mllp_frames(buffer: bytes) -> tuple[list[str], bytes]:
    messages: list[str] = []
    while True:
        start = buffer.find(VT)
        if start < 0:
            return messages, b""
        end = buffer.find(FS_CR, start + 1)
        if end < 0:
            return messages, buffer[start:]
        messages.append(buffer[start + 1:end].decode("utf-8", errors="replace"))
        buffer = buffer[end + len(FS_CR):]

class MLLPHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        buffer = b""
        while data := self.request.recv(4096):
            buffer += data
            messages, buffer = extract_mllp_frames(buffer)
            for message in messages:
                result = validate(message)
                status = "ACCEPTED" if result.accepted else "REJECTED"
                logging.info("%s type=%s control_id=%s reason=%s", status, result.message_type, result.control_id, result.reason or "-")
                self.request.sendall(mllp_frame(ack(result)))

class MLLPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

class UTCFormatter(logging.Formatter):
    converter = time.gmtime

def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic HL7 radiology MLLP receiver")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2575)
    parser.add_argument("--log", default="logs/receiver.log")
    args = parser.parse_args()
    handler = logging.FileHandler(args.log)
    handler.setFormatter(UTCFormatter("%(asctime)sZ %(levelname)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    with MLLPServer((args.host, args.port), MLLPHandler) as server:
        logging.info("MLLP receiver started host=%s port=%s", args.host, args.port)
        server.serve_forever()

if __name__ == "__main__":
    main()
