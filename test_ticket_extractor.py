import unittest
from ticket_extractor import parse_ticket


class TestTicketExtractor(unittest.TestCase):
    def test_manager_email_extraction(self):
        # Simulate a ticket with required fields and a manager in custom_fields_values
        ticket = {
            "id": 12345,
            "number": "TICKET-001",
            "state": "New",
            "custom_fields_values": [
                {"name": "New Employee Name", "value": "Jane Doe"},
                {"name": "New Employee Title", "value": "Engineer"},
                {"name": "New Employee Department", "value": "IT"},
                {
                    "name": "Reports to",
                    "value": "Manager Name",
                    "user": {
                        "name": "Manager Name",
                        "email": "manager@example.com"
                    }
                }
            ]
        }
        user_data = parse_ticket(ticket)
        self.assertIn("manager_email", user_data)
        self.assertEqual(user_data["manager_email"], "manager@example.com")

if __name__ == "__main__":
    unittest.main()
