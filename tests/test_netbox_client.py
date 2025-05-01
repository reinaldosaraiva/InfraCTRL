import unittest
from unittest.mock import patch, MagicMock
import os
from infractrl.netbox_client import NetBoxClient


class TestNetBoxClient(unittest.TestCase):
    def setUp(self):
        self.client = NetBoxClient('http://test-netbox/api', 'test-token')

    @patch('infractrl.netbox_client.requests.get')
    @patch('infractrl.netbox_client.os.getenv')
    def test_test_connection(self, mock_getenv, mock_get):
        # Setup mock for non-simulation mode
        mock_getenv.return_value = 'false'
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        result = self.client.test_connection()
        
        # Assert
        self.assertTrue(result)
        mock_get.assert_called_once_with(
            'http://test-netbox/api/dcim/devices/',
            headers=self.client.headers,
            params={'limit': 1}
        )

    @patch('infractrl.netbox_client.os.getenv')
    @patch('infractrl.netbox_client.requests.get')
    def test_get_devices(self, mock_get, mock_getenv):
        # Setup mock for non-simulation mode
        mock_getenv.return_value = 'false'
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': [{'name': 'test-device'}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        result = self.client.get_devices()
        
        # Assert
        self.assertEqual(result, [{'name': 'test-device'}])
        mock_get.assert_called_once()

    @patch('infractrl.netbox_client.os.getenv')
    def test_get_devices_simulation(self, mock_getenv):
        # Setup mock for simulation mode
        mock_getenv.return_value = 'true'
        
        # Test
        result = self.client.get_devices(limit=2)
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'router-core-01')


if __name__ == '__main__':
    unittest.main()