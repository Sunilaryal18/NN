# Cow Farm Management System

## Overview
This project is a Flask-based API for managing a cow farm. It allows for tracking cows, their milk production, and weight measurements. The system can generate reports on cow health and productivity.

## Features
- Add and retrieve cow information
- Record milk production and weight measurements
- Generate daily reports on cow health and productivity
- Detect potentially ill cows based on weight loss and milk production drop

## Requirements
- Python 3.8+
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/cow-farm-management.git
   cd cow-farm-management
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root directory.
2. Add the following content to the `.env` file:
   ```
   DATABASE_URL=sqlite:///farm.db
   ```

## Running the Application

1. Ensure you're in the project directory and your virtual environment is activated.

2. Run the Flask application:
   ```
   python minimal_app.py
   ```

3. The server will start, typically on `http://127.0.0.1:5000/`.

## API Endpoints

- `GET /cows`: Retrieve all cows
- `POST /cows`: Add a new cow
- `POST /cows/<id>`: Create a new cow with a specific ID
- `GET /cows/<id>`: Get details of a specific cow
- `POST /sensors`: Add a new sensor
- `POST /measurements`: Add a new measurement (milk production or weight)
- `GET /report`: Generate and retrieve a report

## Data Population

The application includes a function to populate the database with initial data from parquet files. This is automatically run when the application starts.

## Running Tests

To run the unit tests:

1. Ensure you're in the project directory and your virtual environment is activated.
2. Run the following command:
   ```
   python -m unittest test_minimal_app.py
   ```

## Troubleshooting

- If you encounter any database-related issues, try deleting the `farm.db` file and restart the application. It will create a new database and populate it with initial data.
- Ensure all required packages are installed by running `pip install -r requirements.txt` again.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
