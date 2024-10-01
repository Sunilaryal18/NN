import unittest
from minimal_app import app, db, Cow, Sensor, MilkMeasurement, WeightMeasurement
from datetime import datetime, timedelta
import json
import logging
import warnings
from io import StringIO

# Suppress all warnings
warnings.filterwarnings("ignore")

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CustomTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_results.append((test, "PASS"))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_results.append((test, "FAIL"))

    def addError(self, test, err):
        super().addError(test, err)
        self.test_results.append((test, "ERROR"))

class CustomTestRunner(unittest.TextTestRunner):
    def __init__(self, stream=None, descriptions=True, verbosity=1):
        if stream is None:
            stream = StringIO()
        super().__init__(stream, descriptions, verbosity)

    def _makeResult(self):
        return CustomTestResult(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        result = super().run(test)
        self.stream.writeln("\nTest Results Summary:")
        self.stream.writeln("=" * 70)
        self.stream.writeln(f"{'Test Case':<50} {'Result':<10}")
        self.stream.writeln("-" * 70)
        for test, status in result.test_results:
            self.stream.writeln(f"{test.id():<50} {status:<10}")
        self.stream.writeln("=" * 70)
        self.stream.writeln(f"Total tests: {result.testsRun}")
        self.stream.writeln(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
        self.stream.writeln(f"Failed: {len(result.failures)}")
        self.stream.writeln(f"Errors: {len(result.errors)}")
        return result

class TestMinimalApp(unittest.TestCase):

    def setUp(self):
        """Set up test client and create new database for testing."""
        logger.info("Setting up test environment")
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
        logger.info("Test environment set up complete")

    def tearDown(self):
        """Clean up after test."""
        logger.info("Tearing down test environment")
        with app.app_context():
            db.session.remove()
            db.drop_all()
        logger.info("Test environment tear down complete")

    def test_index(self):
        """Test the index route."""
        logger.info("Testing index route")
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Welcome to the Minimal Flask App")
        logger.info("Index route test complete")

    def test_add_cow(self):
        """Test adding a new cow."""
        logger.info("Testing add cow")
        response = self.client.post('/cows', json={
            'id': 'test_cow',
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Cow added successfully")
        logger.info("Add cow test complete")

    def test_get_cows(self):
        """Test retrieving all cows."""
        # First, add a cow
        logger.info("Adding cow for get_cows test")
        self.client.post('/cows', json={
            'id': 'test_cow',
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        # Then, get all cows
        logger.info("Getting all cows for get_cows test")
        response = self.client.get('/cows')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Bessie')
        logger.info("Get cows test complete")

    def test_add_sensor(self):
        """Test adding a new sensor."""
        logger.info("Testing add sensor")
        response = self.client.post('/sensors', json={
            'id': 'test_sensor',
            'unit': 'L'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Sensor added successfully")
        logger.info("Add sensor test complete")

    def test_add_measurement(self):
        """Test adding a new measurement."""
        # First, add a cow and a sensor
        logger.info("Adding cow and sensor for add_measurement test")
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
        logger.info("Adding measurement for add_measurement test")
        response = self.client.post('/measurements', json={
            'cow_id': 'test_cow',
            'sensor_id': 'test_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 10.5
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Measurement added successfully")
        logger.info("Add measurement test complete")

    def test_create_cow(self):
        """Test creating a new cow with a specific ID."""
        logger.info("Testing create cow")
        response = self.client.post('/cows/test_cow_id', json={
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Cow created successfully")
        logger.info("Create cow test complete")

    def test_generate_report(self):
        """Test report generation."""
        # Add a cow and some measurements
        logger.info("Testing report generation")
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
        logger.info("Report generation test complete")

    def test_invalid_cow_creation(self):
        """Test creating a cow with invalid data."""
        logger.info("Testing invalid cow creation")
        response = self.client.post('/cows', json={
            'id': 'invalid_cow',
            'name': 'Invalid',
            'birthdate': 'not-a-date'
        })
        self.assertEqual(response.status_code, 400)
        logger.info("Invalid cow creation test complete")

    def test_invalid_measurement(self):
        """Test adding an invalid measurement."""
        logger.info("Testing invalid measurement")
        response = self.client.post('/measurements', json={
            'cow_id': 'non_existent_cow',
            'sensor_id': 'non_existent_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': -10  # Negative value
        })
        self.assertEqual(response.status_code, 400)
        logger.info("Invalid measurement test complete")

    def test_get_non_existent_cow(self):
        """Test retrieving details for a non-existent cow."""
        logger.info("Testing get non-existent cow")
        response = self.client.get('/cows/non_existent_cow')
        self.assertEqual(response.status_code, 404)
        logger.info("Get non-existent cow test complete")

    def test_debug_db(self):
        """Test the debug_db endpoint."""
        logger.info("Testing debug_db endpoint")
        response = self.client.get('/debug_db')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('cows', data)
        self.assertIn('milk_measurements', data)
        self.assertIn('weight_measurements', data)
        logger.info("Debug_db test complete")

    def test_debug_measurements(self):
        """Test the debug_measurements endpoint."""
        logger.info("Testing debug_measurements endpoint")
        # First, add a cow and some measurements
        logger.info("Adding cow and measurements for debug_measurements test")
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
        logger.info("Debugging measurements for debug_measurements test")
        response = self.client.get('/debug_measurements/test_cow')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('milk_measurements', data)
        self.assertIn('weight_measurements', data)
        logger.info("Debug measurements test complete")

if __name__ == '__main__':
    logger.info("Starting test suite")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMinimalApp)
    runner = CustomTestRunner(verbosity=2)
    result = runner.run(suite)
    logger.info("Test suite complete")
    print(runner.stream.getvalue())  # Print the custom output
    exit(not result.wasSuccessful())