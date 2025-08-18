import unittest
from ticket_extractor import parse_ticket

class TestTicketAddressFields(unittest.TestCase):
    def test_address_fields_extraction(self):
        ticket = {
            "id": 123,
            "number": "TICKET-123",
            "state": "New",
            "custom_fields_values": [
                {"name": "New Employee Name", "value": "Jane Doe"},
                {"name": "New Employee Title", "value": "Engineer"},
                {"name": "New Employee Department", "value": "IT"},
                {"name": "streetAddress", "value": "123 Main St"},
                {"name": "city", "value": "Salt Lake City"},
                {"name": "state - Formatted (UT)", "value": "UT"},
                {"name": "zipCode", "value": "84101"},
                {"name": "countryCode - Formatted (US)", "value": "US"}
            ]
        }
        user_data = parse_ticket(ticket)
        self.assertEqual(user_data["streetAddress"], "123 Main St")
        self.assertEqual(user_data["city"], "Salt Lake City")
        self.assertEqual(user_data["state"], "UT")
        self.assertEqual(user_data["zipCode"], "84101")
        self.assertEqual(user_data["countryCode"], "US")
        self.assertEqual(user_data["timezone"], "America/Denver")

    def test_missing_address_fields(self):
        ticket = {
            "id": 124,
            "number": "TICKET-124",
            "state": "New",
            "custom_fields_values": [
                {"name": "New Employee Name", "value": "John Smith"},
                {"name": "New Employee Title", "value": "Engineer"},
                {"name": "New Employee Department", "value": "IT"},
                # Missing address fields
            ]
        }
        user_data = parse_ticket(ticket)
        self.assertEqual(user_data, {})

if __name__ == "__main__":
    unittest.main()
