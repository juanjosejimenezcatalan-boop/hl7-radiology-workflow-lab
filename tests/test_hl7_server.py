import unittest
from src.hl7_server import ack, extract_mllp_frames, mllp_frame, parse_segments, validate

ADT = "MSH|^~\\&|REG|HOSPITAL|RIS|RADIOLOGY|20261107090000||ADT^A04|ADT-001|P|2.5.1\rPID|1||PAT-1001^^^HOSPITAL^MR||TEST^PATIENT\r"
ORM = "MSH|^~\\&|EHR|HOSPITAL|RIS|RADIOLOGY|20261107090500||ORM^O01|ORM-001|P|2.5.1\rPID|1||PAT-1001^^^HOSPITAL^MR||TEST^PATIENT\rORC|NW|ORD-1001\rOBR|1|ORD-1001|ACC-1001|CTCHEST^CT Chest without contrast\r"
ORU = "MSH|^~\\&|RIS|RADIOLOGY|EHR|HOSPITAL|20261107100000||ORU^R01|ORU-001|P|2.5.1\rPID|1||PAT-1001^^^HOSPITAL^MR||TEST^PATIENT\rORC|RE|ORD-1001\rOBR|1|ORD-1001|ACC-1001|CTCHEST^CT Chest without contrast\rOBX|1|TX|RPT^Report||No acute thoracic abnormality.\r"

class HL7ServerTest(unittest.TestCase):
    def test_accepts_workflow_messages(self):
        for message in (ADT, ORM, ORU):
            self.assertTrue(validate(message).accepted)

    def test_rejects_missing_patient_id(self):
        result = validate(ADT.replace("PAT-1001^^^HOSPITAL^MR", ""))
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "Missing PID-3 PatientID")

    def test_ack_uses_the_request_trigger_event(self):
        expected = {ADT: "ACK^A04^ACK", ORM: "ACK^O01^ACK", ORU: "ACK^R01^ACK"}
        for message, message_type in expected.items():
            self.assertEqual(parse_segments(ack(validate(message)))["MSH"][8], message_type)

    def test_extracts_fragmented_frame(self):
        frame = mllp_frame(ADT)
        messages, remainder = extract_mllp_frames(frame[:-2])
        self.assertEqual(messages, [])
        messages, remainder = extract_mllp_frames(remainder + frame[-2:])
        self.assertEqual(messages, [ADT])
        self.assertEqual(remainder, b"")

if __name__ == "__main__":
    unittest.main()

