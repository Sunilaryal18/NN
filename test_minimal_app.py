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

    def test_cow_creation_with_specific_id(self):
        """Test creating a new cow with a specific ID using POST to /cows/{id}."""
        logger.info("Testing cow creation with specific ID")
        cow_id = 'specific_cow_id'
        response = self.client.post(f'/cows/{cow_id}', json={
            'name': 'Daisy',
            'birthdate': '2019-05-15'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Cow created successfully")

        # Verify the cow was created with the specified ID
        get_response = self.client.get(f'/cows/{cow_id}')
        self.assertEqual(get_response.status_code, 200)
        cow_data = json.loads(get_response.data)
        self.assertEqual(cow_data['id'], cow_id)
        self.assertEqual(cow_data['name'], 'Daisy')
        logger.info("Cow creation with specific ID test complete")

    def test_get_cow_with_latest_sensor_data(self):
        """Test GET request to /cows/{id} fetches cow details with latest sensor data."""
        logger.info("Testing get cow with latest sensor data")
        cow_id = 'test_cow'
        self.client.post(f'/cows/{cow_id}', json={
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={'id': 'milk_sensor', 'unit': 'L'})
        self.client.post('/sensors', json={'id': 'weight_sensor', 'unit': 'kg'})

        # Add multiple measurements
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(5)]
        for i, timestamp in enumerate(timestamps):
            self.client.post('/measurements', json={
                'cow_id': cow_id,
                'sensor_id': 'milk_sensor',
                'timestamp': timestamp.timestamp(),
                'value': 10.0 + i
            })
            self.client.post('/measurements', json={
                'cow_id': cow_id,
                'sensor_id': 'weight_sensor',
                'timestamp': timestamp.timestamp(),
                'value': 500.0 + i
            })

        response = self.client.get(f'/cows/{cow_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('latest_milk_measurement', data)
        self.assertIn('latest_weight_measurement', data)
        self.assertAlmostEqual(data['latest_milk_measurement']['value'], 14.0, places=1)
        self.assertAlmostEqual(data['latest_weight_measurement']['value'], 504.0, places=1)
        logger.info("Get cow with latest sensor data test complete")

    def test_report_generation_for_specific_date(self):
        """Test report generation for a specific date."""
        logger.info("Testing report generation for specific date")
        cow_id = 'test_cow'
        self.client.post(f'/cows/{cow_id}', json={
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={'id': 'milk_sensor', 'unit': 'L'})
        self.client.post('/sensors', json={'id': 'weight_sensor', 'unit': 'kg'})

        # Add measurements for multiple days
        for i in range(40):
            date = datetime.now() - timedelta(days=i)
            self.client.post('/measurements', json={
                'cow_id': cow_id,
                'sensor_id': 'milk_sensor',
                'timestamp': date.timestamp(),
                'value': 20.0 + i * 0.1
            })
            self.client.post('/measurements', json={
                'cow_id': cow_id,
                'sensor_id': 'weight_sensor',
                'timestamp': date.timestamp(),
                'value': 500.0 + i * 0.5
            })

        # Generate report for a specific date (10 days ago)
        specific_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        response = self.client.get(f'/report?date={specific_date}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('cows', data)
        cow_report = data['cows'][0]
        self.assertEqual(cow_report['id'], cow_id)
        self.assertIn('avg_milk_production', cow_report)
        self.assertIn('avg_weight', cow_report)
        self.assertAlmostEqual(cow_report['avg_milk_production'], 21.5, delta=0.5)  # Approximate value
        self.assertAlmostEqual(cow_report['avg_weight'], 507.5, delta=2.5)  # Approximate value
        logger.info("Report generation for specific date test complete")

    def test_data_persistence(self):
        """Test that data persists after application restart."""
        logger.info("Testing data persistence")
        cow_id = 'persistent_cow'
        self.client.post(f'/cows/{cow_id}', json={
            'name': 'Persistent Bessie',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={'id': 'milk_sensor', 'unit': 'L'})
        self.client.post('/measurements', json={
            'cow_id': cow_id,
            'sensor_id': 'milk_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 15.0
        })

        # Simulate application restart
        self.tearDown()
        self.setUp()

        # Verify data still exists
        response = self.client.get(f'/cows/{cow_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Persistent Bessie')
        self.assertIn('latest_milk_measurement', data)
        self.assertAlmostEqual(data['latest_milk_measurement']['value'], 15.0, places=1)
        logger.info("Data persistence test complete")

    def test_potentially_ill_cows(self):
        """Test detection of potentially ill cows."""
        logger.info("Testing potentially ill cows detection")
        cow_id = 'test_cow'
        self.client.post(f'/cows/{cow_id}', json={
            'name': 'Bessie',
            'birthdate': '2020-01-01'
        })
        self.client.post('/sensors', json={'id': 'milk_sensor', 'unit': 'L'})
        self.client.post('/sensors', json={'id': 'weight_sensor', 'unit': 'kg'})

        # Add normal measurements
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            self.client.post('/measurements', json={
                'cow_id': cow_id,
                'sensor_id': 'milk_sensor',
                'timestamp': date.timestamp(),
                'value': 20.0
            })
            self.client.post('/measurements', json={
                'cow_id': cow_id,
                'sensor_id': 'weight_sensor',
                'timestamp': date.timestamp(),
                'value': 500.0
            })

        # Add a measurement indicating potential illness (significant drop in milk production)
        self.client.post('/measurements', json={
            'cow_id': cow_id,
            'sensor_id': 'milk_sensor',
            'timestamp': datetime.now().timestamp(),
            'value': 15.0  # 25% drop
        })

        response = self.client.get('/report')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('potentially_ill_cows', data)
        self.assertEqual(len(data['potentially_ill_cows']), 1)
        self.assertEqual(data['potentially_ill_cows'][0]['id'], cow_id)
        logger.info("Potentially ill cows detection test complete")

if __name__ == '__main__':
    logger.info("Starting test suite")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMinimalApp)
    runner = CustomTestRunner(verbosity=2)
    result = runner.run(suite)
    logger.info("Test suite complete")
    print(runner.stream.getvalue())  # Print the custom output
    exit(not result.wasSuccessful())