import unittest
from minimal_app import app, db, Cow, Sensor, MilkMeasurement, WeightMeasurement
from datetime import datetime, timedelta
import json

class TestMinimalApp(unittest.TestCase):

    def setUp(self):
        """Set up test client and create new database for testing."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index(self):
        """Test the index route."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Welcome to the Minimal Flask App")

    def test_add_cow(self):
        """Test adding a new cow."""
        response = self.client.post('/cows', json={
            'id': 'test_cow',
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Cow added successfully")

    def test_get_cows(self):
        """Test retrieving all cows."""
        # First, add a cow
        self.client.post('/cows', json={
            'id': 'test_cow',
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        # Then, get all cows
        response = self.client.get('/cows')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Bessie')

    def test_add_sensor(self):
        """Test adding a new sensor."""
        response = self.client.post('/sensors', json={
            'id': 'test_sensor',
            'unit': 'L'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Sensor added successfully")

    def test_add_measurement(self):
        """Test adding a new measurement."""
        # First, add a cow and a sensor
        self.client.post('/cows', json={
            'id': 'test_cow',
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={
            'id': 'test_sensor',
            'unit': 'L'
        })
        # Then, add a measurement
        response = self.client.post('/measurements', json={
            'cow_id': 'test_cow',
            'sensor_id': 'test_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 10.5
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Measurement added successfully")

    def test_create_cow(self):
        """Test creating a new cow with a specific ID."""
        response = self.client.post('/cows/test_cow_id', json={
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Cow created successfully")

    def test_get_cow_details(self):
        """Test retrieving details for a specific cow."""
        # First, add a cow and some measurements
        self.client.post('/cows', json={
            'id': 'test_cow',
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={
            'id': 'milk_sensor',
            'unit': 'L'
        })
        self.client.post('/sensors', json={
            'id': 'weight_sensor',
            'unit': 'kg'
        })
        self.client.post('/measurements', json={
            'cow_id': 'test_cow',
            'sensor_id': 'milk_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 10.5
        })
        self.client.post('/measurements', json={
            'cow_id': 'test_cow',
            'sensor_id': 'weight_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 500
        })
        # Then, get cow details
        response = self.client.get('/cows/test_cow')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Bessie')
        self.assertIsNotNone(data['avg_milk_production'])
        self.assertIsNotNone(data['avg_weight'])

    def test_generate_report(self):
        """Test report generation."""
        # Add a cow and some measurements
        self.client.post('/cows', json={
            'id': 'test_cow',
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={
            'id': 'milk_sensor',
            'unit': 'L'
        })
        self.client.post('/sensors', json={
            'id': 'weight_sensor',
            'unit': 'kg'
        })
        self.client.post('/measurements', json={
            'cow_id': 'test_cow',
            'sensor_id': 'milk_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 10.5
        })
        self.client.post('/measurements', json={
            'cow_id': 'test_cow',
            'sensor_id': 'weight_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 500
        })
        # Generate report
        response = self.client.get('/report')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('cows', data)
        self.assertIn('potentially_ill_cows', data)

    def test_detect_ill_cows(self):
        """Test detection of potentially ill cows."""
        # Add a cow with significant weight loss
        self.client.post('/cows', json={
            'id': 'ill_cow',
            'name': 'Sickly',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={
            'id': 'weight_sensor',
            'unit': 'kg'
        })
        # Add an average weight measurement
        self.client.post('/measurements', json={
            'cow_id': 'ill_cow',
            'sensor_id': 'weight_sensor',
            'timestamp': (datetime.now() - timedelta(days=7)).timestamp(),
            'value': 500
        })
        # Add a recent weight measurement with significant loss
        self.client.post('/measurements', json={
            'cow_id': 'ill_cow',
            'sensor_id': 'weight_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 450  # 10% weight loss
        })
        # Generate report
        response = self.client.get('/report')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('potentially_ill_cows', data)
        self.assertEqual(len(data['potentially_ill_cows']), 1)
        self.assertEqual(data['potentially_ill_cows'][0]['id'], 'ill_cow')

    def test_invalid_cow_creation(self):
        """Test creating a cow with invalid data."""
        response = self.client.post('/cows', json={
            'id': 'invalid_cow',
            'name': 'Invalid',
            'birthdate': 'not-a-date'
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_measurement(self):
        """Test adding an invalid measurement."""
        response = self.client.post('/measurements', json={
            'cow_id': 'non_existent_cow',
            'sensor_id': 'non_existent_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': -10  # Negative value
        })
        self.assertEqual(response.status_code, 400)

    def test_get_non_existent_cow(self):
        """Test retrieving details for a non-existent cow."""
        response = self.client.get('/cows/non_existent_cow')
        self.assertEqual(response.status_code, 404)

    def test_debug_db(self):
        """Test the debug_db endpoint."""
        response = self.client.get('/debug_db')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('cows', data)
        self.assertIn('milk_measurements', data)
        self.assertIn('weight_measurements', data)

    def test_debug_measurements(self):
        """Test the debug_measurements endpoint."""
        # First, add a cow and some measurements
        self.client.post('/cows', json={
            'id': 'test_cow',
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={
            'id': 'milk_sensor',
            'unit': 'L'
        })
        self.client.post('/measurements', json={
            'cow_id': 'test_cow',
            'sensor_id': 'milk_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 10.5
        })
        # Then, debug measurements
        response = self.client.get('/debug_measurements/test_cow')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('milk_measurements', data)
        self.assertIn('weight_measurements', data)

if __name__ == '__main__':
    unittest.main()