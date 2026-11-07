# Incident and recovery records

These records use only synthetic HL7 v2 messages. Unit tests verify parsing and
ACK generation; the commands below provide the corresponding integration
exercise against the running MLLP receiver.

## Missing PatientID

| Field | Record |
| --- | --- |
| Symptom | The sender receives `MSA|AE` and `ERR|||Missing PID-3 PatientID`. |
| Root cause | The incoming ADT message omits the required patient identifier in `PID-3`. |
| Test | Start the receiver, then run `python3 scripts/send_message.py messages/invalid_missing_patient_id.hl7`. |
| Recovery | Correct the source message so that `PID-3` contains a synthetic identifier. |
| Verification | Send `messages/adt_a04.hl7`; the receiver returns `MSA|AA` and records an accepted message in its audit log. |

## Fragmented MLLP input

| Field | Record |
| --- | --- |
| Symptom | A naive TCP receiver can reject or lose a valid message when its MLLP frame arrives in multiple reads. |
| Root cause | TCP preserves byte order but does not preserve application-message boundaries. |
| Test | `python3 -m unittest discover -s tests -v` includes a fragmented-frame test. |
| Recovery | The receiver accumulates bytes until the `FS CR` MLLP terminator is available, then processes each complete frame. |
| Verification | The fragmented-frame test passes and a normal ORM message sent through MLLP returns `ACK^O01^ACK` with `MSA|AA`. |
