import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('skyfetch', str(Path(__file__).resolve().parents[1] / 'skyfetch'))
spec = importlib.util.spec_from_loader(loader.name, loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'XDG_CONFIG_HOME': self.tmp.name, 'XDG_CACHE_HOME': self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.location = {'name': 'Test', 'latitude': 0, 'longitude': 0, 'country_code': 'US'}
        self.data = {'current': {'weather_code': 63}}

    def test_all_demos_are_offline_and_ascii(self):
        with patch.object(app, 'fetch', side_effect=AssertionError('network')):
            for art in app.ART:
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(app.main(['--demo', art]), 0)
                self.assertTrue(out.getvalue().isascii())
                self.assertNotIn('\x1b', out.getvalue())

    def test_codes(self):
        for code in [0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99]:
            self.assertNotEqual(app.condition(code)[0], 'unknown')
        self.assertEqual(app.condition(0, 0)[0], 'night')
        self.assertEqual(app.condition(999)[0], 'unknown')

    def test_cache_refresh_stale_and_expiry(self):
        with patch.object(app, 'fetch', return_value=self.data) as fetch:
            self.assertEqual(app.weather(self.location, 'metric', False)[1], 'live')
            self.assertEqual(app.weather(self.location, 'metric', False)[1], 'cached')
            self.assertEqual(fetch.call_count, 1)
            app.weather(self.location, 'imperial', False)
            self.assertEqual(fetch.call_count, 2)
        with patch.object(app, 'fetch', side_effect=app.WeatherError('offline')):
            self.assertEqual(app.weather(self.location, 'metric', True)[1], 'stale (offline)')
            with patch.object(app.time, 'time', return_value=time.time() + 90000):
                with self.assertRaises(app.WeatherError): app.weather(self.location, 'metric', False)

    def test_corrupt_cache(self):
        with patch.object(app, 'fetch', return_value=self.data):
            app.weather(self.location, 'metric', False)
            for path in app.state_dir('CACHE').glob('*.json'): path.write_text('{bad')
            self.assertEqual(app.weather(self.location, 'metric', False)[1], 'live')

    def test_saved_coordinates_and_json(self):
        with patch.object(app, 'fetch', return_value=self.data), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(app.main(['--lat', '0', '--lon', '0', '--save', '--json']), 0)
            self.assertEqual(json.loads(out.getvalue())['location']['latitude'], 0)
            out.seek(0); out.truncate()
            self.assertEqual(app.main(['--json']), 0)
            self.assertEqual(json.loads(out.getvalue())['status'], 'cached')

    def test_invalid_coordinates(self):
        for args in [['--lat', '91', '--lon', '0'], ['--lat', '0'], ['--lat', 'nan', '--lon', '0']]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                app.main(args)
            self.assertEqual(exc.exception.code, 2)

    def test_search_and_no_results(self):
        with patch.object(app, 'fetch', return_value={'results': []}), self.assertRaises(app.WeatherError):
            app.locate('No Such City', None)
        with patch.object(app, 'fetch', return_value={'results': [self.location]}) as fetch:
            self.assertEqual(app.locate('Test', 'us'), [self.location])
            self.assertEqual(fetch.call_args[0][1]['countryCode'], 'US')
            fetch.return_value = {'results': [dict(self.location, country_code='GB')]}
            app.locate('London, UK', None)
            self.assertEqual(fetch.call_args[0][1]['name'], 'London')
            self.assertEqual(fetch.call_args[0][1]['countryCode'], 'GB')

    def test_city_state_country_and_abbreviations(self):
        kentucky = dict(self.location, name='Lexington', admin1='Kentucky', country='United States')
        mass = dict(kentucky, admin1='Massachusetts', latitude=42)
        with patch.object(app, 'fetch', return_value={'results': [kentucky, mass]}):
            self.assertEqual(app.locate('Lexington, KY, US'), [kentucky])
            self.assertEqual(app.locate('Lexington', 'United States', 'Massachusetts'), [mass])
            with patch.object(app, 'interactive', return_value=False), self.assertRaises(app.WeatherError):
                app.choose_location(app.locate('Lexington, US'))

    def test_first_run_and_saved_second_run(self):
        place = dict(self.location, name='Lexington', admin1='Kentucky', country='United States')
        with patch.object(app, 'interactive', return_value=True), patch('builtins.input', side_effect=['Lexington', 'KY', 'US', '1', 'imperial']), patch.object(app, 'locate', return_value=[place]) as lookup, patch.object(app, 'weather', return_value=(self.data, 'live', 0)), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.main([]), 0)
            lookup.assert_called_once_with('Lexington', 'US', 'KY')
        config = app.read_json(app.state_dir('CONFIG') / 'config.json')
        self.assertEqual(config['location'], place)
        self.assertEqual(config['units'], 'imperial')
        with patch('builtins.input', side_effect=AssertionError('prompted again')), patch.object(app, 'weather', return_value=(self.data, 'live', 0)), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.main([]), 0)

    def test_cancel_preserves_defaults(self):
        path = app.state_dir('CONFIG') / 'config.json'
        original = {'location': self.location, 'units': 'metric'}
        app.write_json(path, original)
        with patch.object(app, 'interactive', return_value=True), patch('builtins.input', side_effect=['Test', '', 'US', 'q']), patch.object(app, 'locate', return_value=[self.location]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(app.main(['--setup']), 1)
        self.assertEqual(app.read_json(path), original)

    def test_noninteractive_first_run_never_prompts(self):
        with patch.object(app, 'interactive', return_value=False), patch('builtins.input', side_effect=AssertionError('prompted')), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(app.main([]), 1)
            self.assertEqual(app.main(['--json']), 1)

    def test_dew_point_request_display_and_json(self):
        for units, value, suffix in [('metric', 13.2, 'C'), ('imperial', 55.8, 'F')]:
            data = {'current': {'weather_code': 0, 'dew_point_2m': value},
                    'current_units': {'dew_point_2m': '°' + suffix}}
            with patch.object(app, 'fetch', return_value=data) as fetch, contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(app.main(['--lat', '0', '--lon', '0', '--units', units]), 0)
                self.assertIn('dew_point_2m', fetch.call_args[0][1]['current'].split(','))
                self.assertIn('Dew point  {} deg {}'.format(value, suffix), out.getvalue())
                out.seek(0); out.truncate()
                self.assertEqual(app.main(['--lat', '0', '--lon', '0', '--units', units, '--json']), 0)
                self.assertEqual(json.loads(out.getvalue())['weather']['current']['dew_point_2m'], value)

    def test_missing_dew_point_and_narrow_terminal(self):
        with patch.object(app.shutil, 'get_terminal_size', return_value=os.terminal_size((40, 24))), contextlib.redirect_stdout(io.StringIO()) as out:
            app.render(self.location, self.data, 'live', 0, False)
        self.assertIn('Dew point  --', out.getvalue())
        self.assertIn('\n  Sky        Rain\n', out.getvalue())

    def test_partly_cloudy_night_uses_moon(self):
        for code in (1, 2):
            self.assertEqual(app.condition(code, 0)[0], 'partly-cloudy-night')
            self.assertEqual(app.condition(code, 1)[0], 'partly-cloudy')

    def test_network_error_exit(self):
        with patch.object(app, 'fetch', side_effect=app.WeatherError('offline')), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(app.main(['--lat', '0', '--lon', '0']), 1)
            self.assertIn('offline', err.getvalue())

if __name__ == '__main__': unittest.main()
