from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Cow(db.Model):
    """Represents a cow in the farm.

    Attributes:
        id (str): Unique identifier for the cow
        name (str): Name of the cow
        birthdate (str): Birthdate of the cow in YYYY-MM-DD format
        milk_measurements (relationship): Relationship to MilkMeasurement model
        weight_measurements (relationship): Relationship to WeightMeasurement model
    """
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    birthdate = db.Column(db.String, nullable=False)
    milk_measurements = db.relationship('MilkMeasurement', backref='cow', lazy=True)
    weight_measurements = db.relationship('WeightMeasurement', backref='cow', lazy=True)

class Sensor(db.Model):
    """Represents a sensor in the farm.

    Attributes:
        id (str): Unique identifier for the sensor
        unit (str): Unit of measurement for the sensor (e.g., 'L' for liters, 'kg' for kilograms)
    """
    id = db.Column(db.String, primary_key=True)
    unit = db.Column(db.String(50), nullable=False)

class Measurement(db.Model):
    """Represents a generic measurement in the farm.

    Attributes:
        id (int): Unique identifier for the measurement
        sensor_id (str): ID of the sensor that took the measurement
        cow_id (str): ID of the cow the measurement is for
        timestamp (float): Unix timestamp of when the measurement was taken
        value (float): The measured value
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sensor_id = db.Column(db.String, db.ForeignKey('sensor.id'), nullable=False)
    cow_id = db.Column(db.String, db.ForeignKey('cow.id'), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    value = db.Column(db.Float, nullable=False)

class MilkMeasurement(db.Model):
    """Represents a milk production measurement for a cow.

    Attributes are the same as the Measurement class.
    """
    __tablename__ = 'milk_measurement'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cow_id = db.Column(db.String, db.ForeignKey('cow.id'), nullable=False)
    sensor_id = db.Column(db.String, db.ForeignKey('sensor.id'), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    value = db.Column(db.Float, nullable=False)

class WeightMeasurement(db.Model):
    """Represents a weight measurement for a cow.

    Attributes are the same as the Measurement class.
    """
    __tablename__ = 'weight_measurement'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cow_id = db.Column(db.String, db.ForeignKey('cow.id'), nullable=False)
    sensor_id = db.Column(db.String, db.ForeignKey('sensor.id'), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    value = db.Column(db.Float, nullable=False)

# Routes
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Minimal Flask App"})

@app.route('/cows', methods=['GET'])
def get_cows():
    """Retrieve all cows from the database.

    Returns:
        JSON response with list of cows or error message
    """
    cows = Cow.query.all()
    if not cows:
        return jsonify({"message": "No cows found"}), 404
    return jsonify([{"id": cow.id, "name": cow.name, "birthdate": cow.birthdate} for cow in cows])

@app.route('/cows', methods=['POST'])
def add_cow():
    """Add a new cow to the database.

    Returns:
        JSON response confirming addition or error message
    """
    data = request.get_json()
    new_cow = Cow(id=data['id'], name=data['name'], birthdate=data['birthdate'])
    db.session.add(new_cow)
    db.session.commit()
    return jsonify({"message": "Cow added successfully"}), 201

@app.route('/sensors', methods=['POST'])
def add_sensor():
    """Add a new sensor to the database.

    Returns:
        JSON response confirming addition or error message
    """
    data = request.get_json()
    new_sensor = Sensor(id=data['id'], unit=data['unit'])
    db.session.add(new_sensor)
    db.session.commit()
    return jsonify({"message": "Sensor added successfully"}), 201

# Keep only this implementation of the /measurements POST route
@app.route('/measurements', methods=['POST'])
def add_measurement():
    """Add a new measurement to the database.

    Returns:
        JSON response confirming addition or error message
    """
    data = request.get_json()
    try:
        measurement_data = MeasurementCreate(**data)
        new_measurement = Measurement(**measurement_data.model_dump())
        db.session.add(new_measurement)
        db.session.commit()
        return jsonify({"message": "Measurement added successfully"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/cow', methods=['GET'])
def get_cow():
    print("Cow endpoint was hit")
    return jsonify({"message": "This is the cow endpoint"})

# Data Validation Models
class CowCreate(BaseModel):
    id: str
    name: str
    birthdate: str

    @field_validator('birthdate')
    @classmethod
    def validate_birthdate(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Birthdate must be in YYYY-MM-DD format')
        return v

class MeasurementCreate(BaseModel):
    sensor_id: str
    cow_id: str
    timestamp: float
    value: float

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v

@app.route('/cows/<string:id>', methods=['POST'])
def create_cow(id: str):
    """Create a new cow with the given ID.

    Args:
        id (str): Unique identifier for the cow

    Returns:
        JSON response confirming creation or error message
    """
    data = request.get_json()
    cow_data = CowCreate(id=id, **data)
    existing_cow = Cow.query.get(id)
    if existing_cow:
        return jsonify({"message": "Cow already exists"}), 409
    new_cow = Cow(**cow_data.dict())
    db.session.add(new_cow)
    db.session.commit()
    return jsonify({"message": "Cow created successfully"}), 201

@app.route('/cows/<string:id>', methods=['GET'])
def get_cow_details(id: str):
    """Retrieve details for a specific cow.

    Args:
        id (str): Unique identifier for the cow

    Returns:
        JSON response with cow details or error message
    """
    cow = Cow.query.get(id)
    if not cow:
        return jsonify({"message": "Cow not found"}), 404

    # Calculate average milk production
    avg_milk = db.session.query(func.avg(MilkMeasurement.value)).filter(MilkMeasurement.cow_id == id).scalar()

    # Calculate average weight
    avg_weight = db.session.query(func.avg(WeightMeasurement.value)).filter(WeightMeasurement.cow_id == id).scalar()

    # Get latest milk measurement
    latest_milk = MilkMeasurement.query.filter_by(cow_id=id).order_by(MilkMeasurement.timestamp.desc()).first()

    # Get latest weight measurement
    latest_weight = WeightMeasurement.query.filter_by(cow_id=id).order_by(WeightMeasurement.timestamp.desc()).first()

    return jsonify({
        "id": cow.id,
        "name": cow.name,
        "birthdate": cow.birthdate,
        "avg_milk_production": float(avg_milk) if avg_milk is not None else None,
        "avg_weight": float(avg_weight) if avg_weight is not None else None,
        "latest_milk": {
            "value": latest_milk.value,
            "timestamp": latest_milk.timestamp,
            "sensor_id": latest_milk.sensor_id
        } if latest_milk else None,
        "latest_weight": {
            "value": latest_weight.value,
            "timestamp": latest_weight.timestamp,
            "sensor_id": latest_weight.sensor_id
        } if latest_weight else None
    })

# Report Generation
def generate_report(date: datetime) -> Dict[str, Any]:
    """Generate a report for all cows for a given date.

    Args:
        date (datetime): The date for which to generate the report

    Returns:
        Dict[str, Any]: Dictionary containing the report data
    """
    end_date = date
    start_date = end_date - timedelta(days=30)

    cows = Cow.query.all()
    report = {
        "date": end_date.strftime('%Y-%m-%d'),
        "cows": []
    }

    for cow in cows:
        # Calculate average milk production
        avg_milk = db.session.query(func.avg(MilkMeasurement.value)).filter(
            MilkMeasurement.cow_id == cow.id,
            MilkMeasurement.value > 0  # Ensure only positive values are considered
        ).scalar()

        # Calculate average weight
        avg_weight = db.session.query(func.avg(WeightMeasurement.value)).filter(
            WeightMeasurement.cow_id == cow.id,
            WeightMeasurement.value > 0  # Ensure only positive values are considered
        ).scalar()

        # Get latest valid milk measurement
        latest_milk = MilkMeasurement.query.filter(
            MilkMeasurement.cow_id == cow.id,
            MilkMeasurement.value > 0
        ).order_by(MilkMeasurement.timestamp.desc()).first()

        # Get latest valid weight measurement
        latest_weight = WeightMeasurement.query.filter(
            WeightMeasurement.cow_id == cow.id,
            WeightMeasurement.value > 0
        ).order_by(WeightMeasurement.timestamp.desc()).first()

        cow_data = {
            "id": cow.id,
            "name": cow.name,
            "birthdate": cow.birthdate,
            "avg_milk_production": float(avg_milk) if avg_milk is not None else None,
            "avg_weight": float(avg_weight) if avg_weight is not None else None,
            "latest_milk": {
                "value": latest_milk.value,
                "timestamp": latest_milk.timestamp,
                "sensor_id": latest_milk.sensor_id
            } if latest_milk else None,
            "latest_weight": {
                "value": latest_weight.value,
                "timestamp": latest_weight.timestamp,
                "sensor_id": latest_weight.sensor_id
            } if latest_weight else None
        }

        report["cows"].append(cow_data)

    return report

# Add a function to detect potentially ill cows
def detect_ill_cows(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect potentially ill cows based on weight loss and milk production drop.

    Args:
        report (Dict[str, Any]): The generated report containing cow data

    Returns:
        List[Dict[str, Any]]: List of potentially ill cows with reasons
    """
    potentially_ill_cows = []
    for cow in report["cows"]:
        # Check for significant weight loss (e.g., more than 5% difference between latest and average weight)
        if cow["latest_weight"] and cow["avg_weight"] and cow["latest_weight"]["value"] > 0:
            current_weight = cow["latest_weight"]["value"]
            weight_change_percent = (current_weight - cow["avg_weight"]) / cow["avg_weight"] * 100
            if weight_change_percent < -5:
                potentially_ill_cows.append({
                    "id": cow["id"],
                    "name": cow["name"],
                    "reason": f"Significant weight loss: {weight_change_percent:.2f}% change"
                })
        
        # We can also check for sudden drops in milk production
        if cow["latest_milk"] and cow["avg_milk_production"] and cow["latest_milk"]["value"] > 0:
            current_milk = cow["latest_milk"]["value"]
            milk_change_percent = (current_milk - cow["avg_milk_production"]) / cow["avg_milk_production"] * 100
            if milk_change_percent < -20:  # Assuming a 20% drop is significant
                potentially_ill_cows.append({
                    "id": cow["id"],
                    "name": cow["name"],
                    "reason": f"Significant milk production drop: {milk_change_percent:.2f}% change"
                })

    return potentially_ill_cows

@app.route('/report', methods=['GET'])
def get_report():
    """Endpoint to retrieve the generated report.

    Returns:
        JSON response containing the report data
    """
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    report = generate_report(report_date)
    potentially_ill_cows = detect_ill_cows(report)
    report["potentially_ill_cows"] = potentially_ill_cows
    return jsonify(report)

# Database Population
def populate_db():
    """Populate the database with initial data from parquet files.

    This function reads cow, sensor, and measurement data and adds it to the database.
    """
    print("Starting database population...")
    cows_df = pd.read_parquet('cows.parquet')
    sensors_df = pd.read_parquet('sensors.parquet')
    measurements_df = pd.read_parquet('measurements.parquet')

    print(f"Loaded data: {len(cows_df)} cows, {len(sensors_df)} sensors, {len(measurements_df)} measurements")

    # Create a mapping from sensor IDs to their units
    sensor_units = sensors_df.set_index('id')['unit'].to_dict()

    print("Adding cows...")
    for _, row in cows_df.iterrows():
        cow = Cow(id=row['id'], name=row['name'], birthdate=row['birthdate'])
        db.session.add(cow)
    db.session.commit()

    print("Adding sensors...")
    for _, row in sensors_df.iterrows():
        sensor = Sensor(id=row['id'], unit=row['unit'])
        db.session.add(sensor)
    db.session.commit()

    print("Adding measurements...")
    skipped_measurements = 0
    for _, row in measurements_df.iterrows():
        if pd.isna(row['value']):
            skipped_measurements += 1
            continue
        
        unit = sensor_units.get(row['sensor_id'])
        if unit.lower() == 'l':
            measurement = MilkMeasurement(cow_id=row['cow_id'], sensor_id=row['sensor_id'], timestamp=row['timestamp'], value=row['value'])
        elif unit.lower() == 'kg':
            measurement = WeightMeasurement(cow_id=row['cow_id'], sensor_id=row['sensor_id'], timestamp=row['timestamp'], value=row['value'])
        else:
            print(f"Unknown unit {unit} for sensor {row['sensor_id']}")
            continue
        db.session.add(measurement)

    db.session.commit()
    print(f"Database populated successfully. Skipped {skipped_measurements} measurements with NaN values.")

    print(f"Total cows: {Cow.query.count()}")
    print(f"Total sensors: {Sensor.query.count()}")
    print(f"Total milk measurements: {MilkMeasurement.query.count()}")
    print(f"Total weight measurements: {WeightMeasurement.query.count()}")

# Database Initialization
def init_db():
    """Initialize the database by creating tables and populating with initial data.

    This function should be called before starting the Flask server.
    """
    print("Initializing database...")
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Error creating database tables: {e}")

        try:
            print("Populating database...")
            populate_db()
            print("Database populated successfully.")
        except Exception as e:
            print(f"Error populating database: {e}")

        # Debugging: Check if cows are added to the database
        try:
            print("Querying cows from the database...")
            cows = Cow.query.all()
            print(f"Number of cows in the database: {len(cows)}")
            for cow in cows:
                print(f"Cow ID: {cow.id}, Name: {cow.name}, Birthdate: {cow.birthdate}")
        except Exception as e:
            print(f"Error querying cows: {e}")

@app.route('/debug_db')
def debug_db():
    """Endpoint for debugging database contents.

    Returns:
        JSON response with sample data from the database
    """
    cows = Cow.query.all()
    milk_measurements = MilkMeasurement.query.limit(100).all()
    weight_measurements = WeightMeasurement.query.limit(100).all()

    debug_info = {
        "cows": [{"id": cow.id, "name": cow.name, "birthdate": cow.birthdate} for cow in cows],
        "milk_measurements": [{"id": m.id, "cow_id": m.cow_id, "timestamp": m.timestamp, "value": m.value} for m in milk_measurements],
        "weight_measurements": [{"id": m.id, "cow_id": m.cow_id, "timestamp": m.timestamp, "value": m.value} for m in weight_measurements],
        "milk_measurement_count": MilkMeasurement.query.count(),
        "weight_measurement_count": WeightMeasurement.query.count()
    }

    return jsonify(debug_info)

@app.route('/debug_measurements/<string:cow_id>')
def debug_measurements(cow_id):
    """Endpoint for debugging measurements for a specific cow.

    Args:
        cow_id (str): The ID of the cow to debug

    Returns:
        JSON response with recent measurements for the specified cow
    """
    milk_measurements = MilkMeasurement.query.filter_by(cow_id=cow_id).order_by(MilkMeasurement.timestamp.desc()).limit(5).all()
    weight_measurements = WeightMeasurement.query.filter_by(cow_id=cow_id).order_by(WeightMeasurement.timestamp.desc()).limit(5).all()

    debug_info = {
        "cow_id": cow_id,
        "milk_measurements": [{"timestamp": m.timestamp, "value": m.value} for m in milk_measurements],
        "weight_measurements": [{"timestamp": m.timestamp, "value": m.value} for m in weight_measurements]
    }

    return jsonify(debug_info)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if Cow.query.count() == 0:
            print("Database is empty. Populating...")
            populate_db()
        else:
            print("Database already populated. Skipping population.")

    print("Starting Flask server...")
    app.run(debug=True, use_reloader=False)

print("Script execution completed.")