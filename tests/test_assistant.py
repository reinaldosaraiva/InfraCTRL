import unittest
from unittest.mock import patch, MagicMock
from infractrl.assistant import process_query, detect_intent_regex


class TestAssistant(unittest.TestCase):
    @patch('infractrl.assistant.get_client_from_env')
    @patch('infractrl.assistant.query_openai')
    def test_process_query_list_devices(self, mock_query_openai, mock_get_client):
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.test_connection.return_value = True
        
        # Mock intent detection
        mock_query_openai.return_value = {"intent": "list_devices", "params": {"device_type": "router"}}
        
        # Mock devices
        mock_client.get_devices.return_value = [
            {"name": "device1", "device_type": {"model": "router"}},
            {"name": "device2", "device_type": {"model": "switch"}}
        ]
        
        # Test
        process_query("list all routers")
        
        # Assert
        mock_client.get_devices.assert_called_once()

    def test_detect_intent_regex_list_devices(self):
        # Test English query
        result = detect_intent_regex("list all routers")
        self.assertEqual(result["intent"], "list_devices")
        self.assertEqual(result["params"]["device_type"], "router")
        
        # Test Portuguese query
        result = detect_intent_regex("listar todos os roteadores")
        self.assertEqual(result["intent"], "list_devices")
        self.assertEqual(result["params"]["device_type"], "router")


if __name__ == '__main__':
    unittest.main()