from flask import Flask, request, jsonify, render_template_string
import psycopg2
import os
from datetime import datetime, timezone
import json

app = Flask(__name__)

# HTML Dashboard Template
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Meter Management Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: #333;
        }
        .header {
            background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px);
            padding: 1rem 2rem; box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            position: sticky; top: 0; z-index: 100;
        }
        .header h1 { color: #2c3e50; display: flex; align-items: center; gap: 10px; }
        .status-badge {
            background: #27ae60; color: white; padding: 4px 12px;
            border-radius: 20px; font-size: 0.8rem; font-weight: 500;
        }
        .container {
            max-width: 1400px; margin: 0 auto; padding: 2rem;
            display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;
        }
        .card {
            background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px);
            border-radius: 16px; padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .card h2 { color: #2c3e50; margin-bottom: 1rem; display: flex; align-items: center; gap: 8px; }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem; margin-bottom: 1rem;
        }
        .stat-box {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white; padding: 1rem; border-radius: 12px; text-align: center;
        }
        .stat-number { font-size: 2rem; font-weight: bold; display: block; }
        .stat-label { font-size: 0.9rem; opacity: 0.9; }
        .form-group { margin-bottom: 1rem; }
        .form-group label {
            display: block; margin-bottom: 0.5rem; font-weight: 500; color: #2c3e50;
        }
        .form-group select, .form-group input {
            width: 100%; padding: 0.75rem; border: 2px solid #e0e6ed;
            border-radius: 8px; font-size: 1rem; transition: border-color 0.3s;
        }
        .form-group select:focus, .form-group input:focus {
            outline: none; border-color: #3498db;
        }
        .btn {
            background: linear-gradient(135deg, #3498db, #2980b9); color: white;
            border: none; padding: 0.75rem 1.5rem; border-radius: 8px;
            font-size: 1rem; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
            font-weight: 500;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
        }
        .table {
            width: 100%; border-collapse: collapse; margin-top: 1rem;
        }
        .table th, .table td {
            padding: 0.75rem; text-align: left; border-bottom: 1px solid #e0e6ed;
        }
        .table th { background: #f8f9fa; font-weight: 600; color: #2c3e50; }
        .table tr:hover { background: #f8f9fa; }
        .utility-badge {
            padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 500;
        }
        .utility-electric { background: #fff3cd; color: #856404; }
        .utility-gas { background: #d1ecf1; color: #0c5460; }
        .utility-water { background: #cff4fc; color: #055160; }
        .alert { padding: 1rem; border-radius: 8px; margin-bottom: 1rem; font-weight: 500; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .full-width { grid-column: 1 / -1; }
        .meter-reading {
            background: #f8f9fa; padding: 0.5rem; border-radius: 6px;
            margin-bottom: 0.5rem; border-left: 4px solid #3498db;
        }
        .api-info {
            background: #e3f2fd; padding: 1rem; border-radius: 8px;
            border-left: 4px solid #2196f3; margin-bottom: 1rem;
        }
        @media (max-width: 768px) {
            .container { grid-template-columns: 1fr; padding: 1rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ Smart Meter Management Dashboard <span class="status-badge">Live</span></h1>
    </div>
    <div class="container">
        <div class="card">
            <h2>📊 System Statistics</h2>
            <div class="stats-grid">
                <div class="stat-box"><span class="stat-number" id="customerCount">-</span><span class="stat-label">Customers</span></div>
                <div class="stat-box"><span class="stat-number" id="meterCount">-</span><span class="stat-label">Meters</span></div>
                <div class="stat-box"><span class="stat-number" id="readingCount">-</span><span class="stat-label">Readings</span></div>
            </div>
            <p><strong>Database:</strong> <span id="dbVersion">Loading...</span></p>
        </div>
        <div class="card">
            <h2>📝 Submit Meter Reading</h2>
            <div id="submitAlert"></div>
            <form id="readingForm">
                <div class="form-group">
                    <label for="meterSelect">Select Meter:</label>
                    <select id="meterSelect" required><option value="">Loading meters...</option></select>
                </div>
                <div class="form-group">
                    <label for="readingValue">Reading Value:</label>
                    <input type="number" id="readingValue" step="0.001" required placeholder="Enter meter reading">
                </div>
                <div class="form-group">
                    <label for="readingDate">Reading Date:</label>
                    <input type="datetime-local" id="readingDate" required>
                </div>
                <div class="form-group">
                    <label for="temperature">Temperature (°C):</label>
                    <input type="number" id="temperature" step="0.1" placeholder="Optional">
                </div>
                <button type="submit" class="btn">Submit Reading</button>
            </form>
        </div>
        <div class="card">
            <h2>👥 Customers</h2>
            <div id="customersTable">Loading customers...</div>
        </div>
        <div class="card">
            <h2>⚡ Active Meters</h2>
            <div id="metersTable">Loading meters...</div>
        </div>
        <div class="card full-width">
            <h2>📈 Recent Meter Readings</h2>
            <div id="readingsSection"><p>Select a meter to view readings.</p></div>
        </div>
        <div class="card full-width">
            <h2>🔧 API Information</h2>
            <div class="api-info">
                <p><strong>API Base URL:</strong> <code>{{ request.url_root }}</code></p>
                <p><strong>Available Endpoints:</strong></p>
                <ul>
                    <li><code>GET /api/v1/customers</code> - List all customers</li>
                    <li><code>GET /api/v1/meters</code> - List all meters</li>
                    <li><code>POST /api/v1/readings</code> - Submit meter reading</li>
                    <li><code>GET /api/v1/readings/{meter_id}</code> - Get meter history</li>
                    <li><code>GET /health</code> - Health check</li>
                </ul>
            </div>
        </div>
    </div>
    <script>
        const API_BASE = window.location.origin;
        let meters = [], customers = [];
        
        document.addEventListener("DOMContentLoaded", function() {
            loadDashboard(); setupEventListeners(); setDefaultDateTime();
        });
        
        function setDefaultDateTime() {
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            document.getElementById("readingDate").value = now.toISOString().slice(0, 16);
        }
        
        function setupEventListeners() {
            document.getElementById("readingForm").addEventListener("submit", submitReading);
            document.getElementById("meterSelect").addEventListener("change", loadMeterReadings);
        }
        
        async function loadDashboard() {
            try {
                const [statsData, customersData, metersData] = await Promise.all([
                    fetch(`${API_BASE}/api/v1/test-db`).then(r => r.json()),
                    fetch(`${API_BASE}/api/v1/customers`).then(r => r.json()),
                    fetch(`${API_BASE}/api/v1/meters`).then(r => r.json())
                ]);
                
                document.getElementById("customerCount").textContent = statsData.data_summary.customers;
                document.getElementById("meterCount").textContent = statsData.data_summary.meters;
                document.getElementById("readingCount").textContent = statsData.data_summary.readings;
                document.getElementById("dbVersion").textContent = statsData.postgres_version.split(" ").slice(0, 2).join(" ");
                
                customers = customersData.customers; meters = metersData.meters;
                updateCustomersTable(); updateMetersTable(); updateMeterSelect();
            } catch (error) {
                console.error("Error loading dashboard:", error);
            }
        }
        
        function updateCustomersTable() {
            const html = `<table class="table"><thead><tr><th>Customer</th><th>Type</th><th>Address</th></tr></thead><tbody>${customers.map(customer => `<tr><td><strong>${customer.customer_name}</strong><br><small>${customer.account_number}</small></td><td><span class="utility-badge utility-${customer.utility_type}">${customer.utility_type}</span></td><td>${customer.service_address}</td></tr>`).join("")}</tbody></table>`;
            document.getElementById("customersTable").innerHTML = html;
        }
        
        function updateMetersTable() {
            const html = `<table class="table"><thead><tr><th>Meter ID</th><th>Type</th><th>Manufacturer</th></tr></thead><tbody>${meters.map(meter => `<tr><td><strong>${meter.meter_id}</strong></td><td><span class="utility-badge utility-${meter.meter_type}">${meter.meter_type}</span></td><td>${meter.manufacturer} ${meter.model}</td></tr>`).join("")}</tbody></table>`;
            document.getElementById("metersTable").innerHTML = html;
        }
        
        function updateMeterSelect() {
            const select = document.getElementById("meterSelect");
            select.innerHTML = `<option value="">Select a meter...</option>${meters.map(meter => `<option value="${meter.meter_id}" data-customer="${meter.customer_id}">${meter.meter_id} - ${meter.customer_name} (${meter.meter_type})</option>`).join("")}`;
        }
        
        async function submitReading(event) {
            event.preventDefault();
            const form = event.target; const submitBtn = form.querySelector("button[type=submit]");
            const alertDiv = document.getElementById("submitAlert");
            const selectedOption = document.getElementById("meterSelect").selectedOptions[0];
            const meterId = selectedOption.value; const customerId = selectedOption.dataset.customer;
            
            const readingData = {
                meter_id: meterId, customer_id: customerId,
                reading_value: parseFloat(document.getElementById("readingValue").value),
                reading_date: new Date(document.getElementById("readingDate").value).toISOString(),
                reading_type: "manual"
            };
            
            const temperature = document.getElementById("temperature").value;
            if (temperature) readingData.temperature = parseFloat(temperature);
            
            try {
                submitBtn.textContent = "Submitting..."; submitBtn.disabled = true;
                const response = await fetch(`${API_BASE}/api/v1/readings`, {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(readingData)
                });
                const result = await response.json();
                
                if (response.ok) {
                    alertDiv.innerHTML = `<div class="alert alert-success">✅ Reading submitted successfully! Reading ID: ${result.reading_id}</div>`;
                    form.reset(); setDefaultDateTime(); await loadDashboard(); await loadMeterReadings();
                } else {
                    alertDiv.innerHTML = `<div class="alert alert-error">❌ Error: ${result.error}</div>`;
                }
            } catch (error) {
                alertDiv.innerHTML = `<div class="alert alert-error">❌ Network error: Could not submit reading</div>`;
            } finally {
                submitBtn.textContent = "Submit Reading"; submitBtn.disabled = false;
            }
        }
        
        async function loadMeterReadings() {
            const meterId = document.getElementById("meterSelect").value;
            const readingsSection = document.getElementById("readingsSection");
            if (!meterId) { readingsSection.innerHTML = "<p>Select a meter to view readings.</p>"; return; }
            
            try {
                readingsSection.innerHTML = "<p>Loading readings...</p>";
                const response = await fetch(`${API_BASE}/api/v1/readings/${meterId}`);
                const data = await response.json();
                
                if (data.readings && data.readings.length > 0) {
                    const html = `<h3>📊 ${data.meter_info.meter_id} - ${data.meter_info.manufacturer} ${data.meter_info.model}</h3><p><strong>Customer:</strong> ${data.meter_info.customer_id} | <strong>Type:</strong> ${data.meter_info.meter_type}</p><div style="max-height: 400px; overflow-y: auto;">${data.readings.map(reading => `<div class="meter-reading"><strong>${reading.reading_value.toLocaleString()}</strong> ${data.meter_info.meter_type === "electric" ? "kWh" : data.meter_info.meter_type === "gas" ? "m³" : "L"}<span style="float: right; color: #666;">${new Date(reading.reading_date).toLocaleString()}</span><br><small>Type: ${reading.reading_type} | Quality: ${reading.quality_code}${reading.temperature ? ` | Temp: ${reading.temperature}°C` : ""}</small></div>`).join("")}</div>`;
                    readingsSection.innerHTML = html;
                } else {
                    readingsSection.innerHTML = "<p>No readings found for this meter.</p>";
                }
            } catch (error) {
                readingsSection.innerHTML = "<p>Error loading readings.</p>";
            }
        }
    </script>
</body>
</html>'''

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME', 'postgres'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f'DB error: {e}')
        return None

def init_database():
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Create customers table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id VARCHAR(50) PRIMARY KEY,
                account_number VARCHAR(50) UNIQUE NOT NULL,
                customer_name VARCHAR(100) NOT NULL,
                service_address TEXT NOT NULL,
                utility_type VARCHAR(20) NOT NULL CHECK (utility_type IN ('electric', 'gas', 'water')),
                rate_class VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Create meters table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS meters (
                meter_id VARCHAR(50) PRIMARY KEY,
                customer_id VARCHAR(50) REFERENCES customers(customer_id),
                meter_type VARCHAR(20) NOT NULL,
                manufacturer VARCHAR(50),
                model VARCHAR(50),
                install_date DATE,
                last_reading_date TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Create meter_readings table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS meter_readings (
                reading_id SERIAL PRIMARY KEY,
                meter_id VARCHAR(50) REFERENCES meters(meter_id),
                customer_id VARCHAR(50) REFERENCES customers(customer_id),
                reading_value DECIMAL(12,3) NOT NULL,
                reading_date TIMESTAMP NOT NULL,
                reading_type VARCHAR(20) DEFAULT 'automatic',
                quality_code VARCHAR(10) DEFAULT 'good',
                temperature DECIMAL(5,2),
                voltage DECIMAL(5,2),
                signal_strength INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meter_id, reading_date)
            );
        ''')
        
        # Create indexes for performance
        cur.execute('CREATE INDEX IF NOT EXISTS idx_readings_meter_date ON meter_readings(meter_id, reading_date);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_readings_customer ON meter_readings(customer_id);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_readings_date ON meter_readings(reading_date);')
        
        # Insert sample data
        cur.execute('''
            INSERT INTO customers (customer_id, account_number, customer_name, service_address, utility_type, rate_class)
            VALUES 
                ('CUST-001', 'ACC-123456', 'Toronto Hydro Customer', '123 Main St, Toronto, ON', 'electric', 'residential'),
                ('CUST-002', 'ACC-789012', 'Enbridge Gas Customer', '456 Oak Ave, Toronto, ON', 'gas', 'commercial'),
                ('CUST-003', 'ACC-345678', 'City of Toronto Water', '789 Pine Rd, Toronto, ON', 'water', 'residential')
            ON CONFLICT (customer_id) DO NOTHING;
        ''')
        
        cur.execute('''
            INSERT INTO meters (meter_id, customer_id, meter_type, manufacturer, model, install_date, status)
            VALUES 
                ('EM-HYDRO-001234', 'CUST-001', 'electric', 'Itron', 'OpenWay CENTRON II', '2023-01-15', 'active'),
                ('GM-ENBRIDGE-005678', 'CUST-002', 'gas', 'Sensus', 'iPerl', '2022-06-10', 'active'),
                ('WM-TORONTO-009876', 'CUST-003', 'water', 'Neptune', 'E-Coder R900i', '2023-03-22', 'active')
            ON CONFLICT (meter_id) DO NOTHING;
        ''')
        
        conn.commit()
        print('✅ Database initialized with tables and sample data')
        return True
        
    except Exception as e:
        print(f'Init error: {e}')
        conn.rollback()
        return False
    finally:
        conn.close()

# WEB DASHBOARD ROUTE
@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/health')
def health():
    db_status = 'connected' if get_db_connection() else 'disconnected'
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'service': 'Smart Meter Reading API with Web Dashboard',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/debug-env')
def debug_env():
    return jsonify({
        'DB_HOST': os.environ.get('DB_HOST', 'NOT_SET'),
        'DB_NAME': os.environ.get('DB_NAME', 'NOT_SET'),
        'DB_USER': os.environ.get('DB_USER', 'NOT_SET'),
        'DB_PASSWORD': 'SET' if os.environ.get('DB_PASSWORD') else 'NOT_SET',
        'all_env_vars': list(os.environ.keys())
    })



@app.route('/api/v1/test-db')
def test_db():
    conn = get_db_connection()
    if not conn:
        return jsonify({'database': 'error', 'message': 'Connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT version()')
        version = cur.fetchone()
        
        # Get table counts
        cur.execute('SELECT COUNT(*) FROM customers')
        customers = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM meters')
        meters = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM meter_readings')
        readings = cur.fetchone()[0]
        
        conn.close()
        return jsonify({
            'database': 'connected',
            'postgres_version': version[0],
            'data_summary': {
                'customers': customers,
                'meters': meters,
                'readings': readings
            }
        })
    except Exception as e:
        return jsonify({'database': 'error', 'message': str(e)}), 500

@app.route('/api/v1/customers')
def get_customers():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT customer_id, account_number, customer_name, service_address, utility_type, rate_class FROM customers ORDER BY customer_name')
        customers = cur.fetchall()
        
        customer_list = []
        for row in customers:
            customer_list.append({
                'customer_id': row[0],
                'account_number': row[1],
                'customer_name': row[2],
                'service_address': row[3],
                'utility_type': row[4],
                'rate_class': row[5]
            })
        
        conn.close()
        return jsonify({
            'customers': customer_list,
            'count': len(customer_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/meters')
def get_meters():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT m.meter_id, m.customer_id, m.meter_type, m.manufacturer, m.model, 
                   m.install_date, m.last_reading_date, m.status, c.customer_name
            FROM meters m
            JOIN customers c ON m.customer_id = c.customer_id
            ORDER BY m.meter_id
        ''')
        meters = cur.fetchall()
        
        meter_list = []
        for row in meters:
            meter_list.append({
                'meter_id': row[0],
                'customer_id': row[1],
                'meter_type': row[2],
                'manufacturer': row[3],
                'model': row[4],
                'install_date': row[5].isoformat() if row[5] else None,
                'last_reading_date': row[6].isoformat() if row[6] else None,
                'status': row[7],
                'customer_name': row[8]
            })
        
        conn.close()
        return jsonify({
            'meters': meter_list,
            'count': len(meter_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/readings', methods=['POST'])
def submit_reading():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['meter_id', 'customer_id', 'reading_value']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields', 
                'missing': missing_fields,
                'required': required_fields
            }), 400
        
        # Validate data types and ranges
        try:
            reading_value = float(data['reading_value'])
            if reading_value < 0:
                return jsonify({'error': 'Reading value cannot be negative'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid reading value - must be a number'}), 400
        
        # Parse reading date
        if 'reading_date' in data:
            try:
                reading_date = datetime.fromisoformat(data['reading_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use ISO 8601 (e.g., 2025-06-03T05:00:00Z)'}), 400
        else:
            reading_date = datetime.now(timezone.utc)
        
        # Insert into database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor()
            
            # Validate meter exists
            cur.execute('SELECT customer_id, meter_type FROM meters WHERE meter_id = %s AND status = %s', (data['meter_id'], 'active'))
            meter = cur.fetchone()
            if not meter:
                return jsonify({'error': f'Meter {data["meter_id"]} not found or inactive'}), 404
            
            # Validate customer matches meter
            if meter[0] != data['customer_id']:
                return jsonify({'error': f'Customer {data["customer_id"]} does not match meter {data["meter_id"]}'}), 400
            
            # Insert the reading
            cur.execute('''
                INSERT INTO meter_readings 
                (meter_id, customer_id, reading_value, reading_date, reading_type, 
                 quality_code, temperature, voltage, signal_strength)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING reading_id, created_at;
            ''', (
                data['meter_id'],
                data['customer_id'],
                reading_value,
                reading_date,
                data.get('reading_type', 'automatic'),
                data.get('quality_code', 'good'),
                data.get('temperature'),
                data.get('voltage'),
                data.get('signal_strength')
            ))
            
            reading_id, created_at = cur.fetchone()
            
            # Update meter's last reading date
            cur.execute('''
                UPDATE meters 
                SET last_reading_date = %s 
                WHERE meter_id = %s;
            ''', (reading_date, data['meter_id']))
            
            conn.commit()
            
            return jsonify({
                'message': f'Reading recorded successfully for {meter[1]} meter',
                'reading_id': reading_id,
                'meter_id': data['meter_id'],
                'customer_id': data['customer_id'],
                'reading_value': reading_value,
                'reading_date': reading_date.isoformat(),
                'meter_type': meter[1],
                'timestamp': created_at.isoformat()
            }), 201
            
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if 'unique' in str(e).lower():
                return jsonify({'error': 'Duplicate reading for this meter and timestamp'}), 409
            return jsonify({'error': 'Data integrity error'}), 400
        except psycopg2.Error as e:
            conn.rollback()
            return jsonify({'error': f'Database operation failed: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/v1/readings/<meter_id>')
def get_readings(meter_id):
    # Query parameters
    limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 records
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        
        # Validate meter exists
        cur.execute('SELECT customer_id, meter_type, manufacturer, model FROM meters WHERE meter_id = %s', (meter_id,))
        meter = cur.fetchone()
        if not meter:
            return jsonify({'error': f'Meter {meter_id} not found'}), 404
        
        # Build query with optional date filtering
        query = '''
            SELECT reading_id, meter_id, customer_id, reading_value, 
                   reading_date, reading_type, quality_code, 
                   temperature, voltage, signal_strength, created_at
            FROM meter_readings 
            WHERE meter_id = %s
        '''
        params = [meter_id]
        
        if start_date:
            query += ' AND reading_date >= %s'
            params.append(start_date)
        
        if end_date:
            query += ' AND reading_date <= %s'
            params.append(end_date)
        
        query += ' ORDER BY reading_date DESC LIMIT %s;'
        params.append(limit)
        
        cur.execute(query, params)
        readings = cur.fetchall()
        
        # Convert to JSON-serializable format
        readings_list = []
        for reading in readings:
            readings_list.append({
                'reading_id': reading[0],
                'meter_id': reading[1],
                'customer_id': reading[2],
                'reading_value': float(reading[3]),
                'reading_date': reading[4].isoformat(),
                'reading_type': reading[5],
                'quality_code': reading[6],
                'temperature': float(reading[7]) if reading[7] else None,
                'voltage': float(reading[8]) if reading[8] else None,
                'signal_strength': reading[9],
                'created_at': reading[10].isoformat()
            })
        
        conn.close()
        return jsonify({
            'meter_info': {
                'meter_id': meter_id,
                'customer_id': meter[0],
                'meter_type': meter[1],
                'manufacturer': meter[2],
                'model': meter[3]
            },
            'readings': readings_list,
            'reading_count': len(readings_list),
            'query_params': {
                'limit': limit,
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    print('Starting Smart Meter API with Web Dashboard on port 8000...')
    init_database()
    app.run(host='0.0.0.0', port=8000, debug=True)
