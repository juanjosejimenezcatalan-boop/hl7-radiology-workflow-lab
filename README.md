# HL7 Radiology Workflow Lab

A dependency-free, synthetic HL7 v2 lab that models the information flow that
precedes and follows radiology imaging. HL7 carries patient identity, orders,
and reports; DICOM carries images.

> **Safety:** Every identifier, name, order, report, and log in this repository
> is synthetic. Do not use this teaching server with clinical systems or PHI.

## Workflow

```text
Patient registration       ADT^A04  (MSH, PID)
          |
          v
CT chest order             ORM^O01  (MSH, PID, ORC, OBR)
          |
          v
Radiology report           ORU^R01  (MSH, PID, ORC, OBR, OBX)
```

See the detailed [sequence diagram](docs/workflow.md).

## What this lab demonstrates

- Receives framed HL7 v2 messages over TCP using MLLP (`VT ... FS CR`).
- Validates a small, explicit teaching profile for `MSH`, `PID`, `ORC`, `OBR`,
  and `OBX`.
- Returns `MSA|AA` on acceptance or `MSA|AE` plus `ERR` on rejection.
- Records a non-PHI audit log and handles a missing-PatientID failure.
- Includes unit tests for validation and fragmented MLLP input.

This is not a production conformance engine. Production interfaces require a
vendor-specific conformance profile, TLS/network controls, full parsing,
message persistence, and operational monitoring.

## Run with Docker

The receiver publishes host port `2576` and listens on `2575` inside Docker.

```sh
docker compose up -d --build
python3 scripts/send_message.py messages/adt_a04.hl7
python3 scripts/send_message.py messages/orm_o01_ct_chest.hl7
python3 scripts/send_message.py messages/oru_r01_ct_chest.hl7
docker compose logs -f hl7-receiver
```

Each successful command prints an ACK containing `MSA|AA` and the original
message control ID.

## Rejection scenario

Send an ADT registration without `PID-3`:

```sh
python3 scripts/send_message.py messages/invalid_missing_patient_id.hl7
```

Expected response:

```text
MSA|AE|ADT-INVALID-001
ERR|||Missing PID-3 PatientID
```

The receiver logs only message metadata and the validation outcome. See the
synthetic [example log](logs/example.log).

## Test without Docker

```sh
python3 -m unittest discover -s tests -v
python3 -m src.hl7_server --port 2575 --log logs/receiver.log
# In a second terminal:
python3 scripts/send_message.py messages/orm_o01_ct_chest.hl7 --port 2575
```

## Repository layout

```text
messages/       Synthetic ADT, ORM, ORU, and invalid-input fixtures
src/            MLLP framing, validation, ACK generation, TCP server
scripts/        MLLP sender utility
tests/          Unit tests
logs/           Sanitized example audit log
docs/           Mermaid workflow diagram
```

## Background

In radiology, ADT updates patient/visit information, ORM represents an imaging
order, and ORU transports a report or result. The Royal College of
Radiologists' *Implementing Ordercomms* publication is now listed as archived;
see its [archived-publication entry](https://www.rcr.ac.uk/our-services/all-our-publications/archived-publications/).
For an implementation-level workflow mapping `ADT^A04`, `ORM^O01`, and
`ORU^R01`, see the [HL7 technical workflow reference](https://www.moh.gov.sa/Ministry/MediaCenter/Ads/Documents/2018-05-28-007.pdf).
