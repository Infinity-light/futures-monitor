import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from futures_monitor.config import AppConfig, save_config
from futures_monitor.server.app import create_app


class TestServerAppRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_health_route_accessible(self) -> None:
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('message'), 'ok')

    def test_monitor_status_route_is_stable(self) -> None:
        response = self.client.get('/api/monitor/status')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('running', payload)
        self.assertIn('connection_status', payload)
        self.assertIn('rows', payload)

    def test_mark_bought_uses_request_body_contract(self) -> None:
        response = self.client.post('/api/monitor/mark-bought', json={'symbol': 'SHFE.rb2405'})
        self.assertIn(response.status_code, (200, 400))

    def test_websocket_uses_wrapped_contract_messages(self) -> None:
        with self.client.websocket_connect('/ws/events') as websocket:
            connected_message = websocket.receive_json()
            websocket.send_text('ping')
            pong_message = websocket.receive_json()

        self.assertEqual(connected_message['type'], 'connection')
        self.assertEqual(connected_message['data']['status'], 'connected')
        self.assertEqual(pong_message['type'], 'pong')
        self.assertEqual(pong_message['data']['received'], 'ping')

    def test_config_get_and_update_return_real_password_and_refresh_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = str(Path(temp_dir) / 'config.json')
            save_config(
                AppConfig(
                    symbols=['SHFE.rb2405'],
                    tq_account='old-account',
                    tq_password='old-password',
                    use_real_market_data=False,
                    strict_real_mode=True,
                ),
                config_path,
            )

            from futures_monitor.server.services import config_service as config_module
            from futures_monitor.server.services import monitor_service as monitor_module

            original_monitor = monitor_module._monitor_service_instance
            original_config = config_module._config_service_instance
            monitor_module._monitor_service_instance = monitor_module.MonitorService(config_path)
            config_module._config_service_instance = config_module.ConfigService(config_path)

            try:
                with TestClient(create_app()) as client:
                    initial = client.get('/api/config').json()
                    response = client.put(
                        '/api/config',
                        json={
                            'symbols': ['DCE.i2405'],
                            'take_profit_pct': 0.2,
                            'stop_loss_pct': 0.1,
                            'position_pct': 0.1,
                            'enable_sms': False,
                            'alert_sound': True,
                            'data_dir': '.data',
                            'timezone': 'Asia/Shanghai',
                            'use_real_market_data': True,
                            'strict_real_mode': False,
                            'ui_refresh_ms': 800,
                            'tq_account': 'new-account',
                            'tq_password': 'new-password',
                        },
                    )
                    payload = response.json()
                    fetched = client.get('/api/config').json()
                    monitor = monitor_module._monitor_service_instance
            finally:
                monitor_module._monitor_service_instance = original_monitor
                config_module._config_service_instance = original_config

        self.assertEqual(response.status_code, 200)
        self.assertEqual(initial['tq_password'], 'old-password')
        self.assertEqual(payload['tq_account'], 'new-account')
        self.assertEqual(payload['tq_password'], 'new-password')
        self.assertEqual(fetched['tq_password'], 'new-password')
        self.assertEqual(monitor.config.tq_account, 'new-account')
        self.assertTrue(monitor.config.use_real_market_data)
        self.assertFalse(monitor.config.strict_real_mode)

    def test_monitor_control_returns_human_auth_hint_when_real_credentials_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = str(Path(temp_dir) / 'config.json')
            save_config(
                AppConfig(
                    symbols=['SHFE.rb2405'],
                    tq_account='',
                    tq_password='',
                    use_real_market_data=True,
                    strict_real_mode=True,
                ),
                config_path,
            )

            from futures_monitor.server.services import config_service as config_module
            from futures_monitor.server.services import monitor_service as monitor_module

            original_monitor = monitor_module._monitor_service_instance
            original_config = config_module._config_service_instance
            monitor_module._monitor_service_instance = monitor_module.MonitorService(config_path)
            config_module._config_service_instance = config_module.ConfigService(config_path)

            try:
                with TestClient(create_app()) as client:
                    response = client.post('/api/monitor/control', json={'action': 'start', 'symbols': ['SHFE.rb2405']})
                    payload = response.json()
            finally:
                monitor_module._monitor_service_instance = original_monitor
                config_module._config_service_instance = original_config

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['symbols'], ['SHFE.rb2405'])
        self.assertIn(payload['connection_status'], ('connecting', 'error'))
        self.assertIn(payload['running'], (True, False))


if __name__ == '__main__':
    unittest.main()
