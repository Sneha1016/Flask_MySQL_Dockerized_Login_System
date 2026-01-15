# app.py - Flask Application for Docker Environment
# This version reads database configuration from environment variables

# Import Flask framework components
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Import MySQL connector for database operations
import mysql.connector
from mysql.connector import Error

# Import password hashing functions for security
from werkzeug.security import generate_password_hash, check_password_hash

# Import os module to read environment variables
import os

# Import time module for retry logic
import time

# Create Flask application instance
app = Flask(__name__)

# Set secret key from environment variable or use default
# In production, always use environment variable
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')

# Database configuration from environment variables
# Docker Compose passes these variables to the container
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'db'),  # 'db' is the service name in docker-compose
    'database': os.environ.get('DB_NAME', 'flask_auth_db'),
    'user': os.environ.get('DB_USER', 'flask_user'),
    'password': os.environ.get('DB_PASSWORD', 'flask_password'),
    'port': int(os.environ.get('DB_PORT', '3306'))
}

# Function to get database connection with retry logic
# MySQL container may take time to start, so we retry connection
def get_db_connection(max_retries=5, retry_delay=5):
    """
    Establish connection to MySQL database with retry logic.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Seconds to wait between retries
    
    Returns:
        MySQL connection object or None if connection fails
    """
    # Try to connect multiple times
    for attempt in range(max_retries):
        try:
            # Attempt to establish connection
            connection = mysql.connector.connect(**DB_CONFIG)
            
            # If successful, print message and return connection
            if connection.is_connected():
                print(f"Successfully connected to MySQL database")
                return connection
                
        except Error as e:
            # If connection fails, print error and retry
            print(f"Connection attempt {attempt + 1} failed: {e}")
            
            # If not last attempt, wait before retrying
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                # If all attempts fail, print final error
                print("Max retries reached. Could not connect to database.")
                return None
    
    return None

# Route for home page
@app.route('/')
def index():
    """
    Home page route - redirects to login if not authenticated,
    shows welcome page if authenticated
    """
    # Check if user is logged in by checking session
    if 'user_id' in session:
        # User is logged in, show home page
        return render_template('home.html', username=session['username'])
    
    # User not logged in, redirect to login page
    return redirect(url_for('login'))

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration route - handles both displaying form and processing registration
    GET: Display registration form
    POST: Process registration and save to database
    """
    # If POST request, process form submission
    if request.method == 'POST':
        # Extract form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password for security
        # Never store plain text passwords in database
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Get database connection
        connection = get_db_connection()
        
        # Check if connection was successful
        if connection is None:
            flash('Database connection failed. Please try again later.', 'danger')
            return render_template('register.html')
        
        try:
            # Create cursor to execute queries
            cursor = connection.cursor()
            
            # SQL query to insert new user
            # Uses parameterized query to prevent SQL injection
            query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            values = (username, email, hashed_password)
            
            # Execute the query
            cursor.execute(query, values)
            
            # Commit transaction to save changes
            connection.commit()
            
            # Show success message
            flash('Registration successful! Please login.', 'success')
            
            # Redirect to login page
            return redirect(url_for('login'))
            
        except mysql.connector.IntegrityError as e:
            # Handle duplicate username or email error
            # This occurs when UNIQUE constraint is violated
            flash('Username or email already exists!', 'danger')
            
        except Error as e:
            # Handle other database errors
            print(f"Database error: {e}")
            flash('An error occurred. Please try again.', 'danger')
            
        finally:
            # Always close cursor and connection to free resources
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    # If GET request or after error, show registration form
    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required!', 'danger')
            return render_template('login.html')

        connection = get_db_connection()

        if connection is None:
            flash('Database connection failed. Please try again later.', 'danger')
            return render_template('login.html')

        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['email'] = user['email']

                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password!', 'danger')

        except Error as e:
            print(f"Database error: {e}")
            flash('An error occurred. Please try again.', 'danger')

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    return render_template('login.html')


# Route for user logout
@app.route('/logout')
def logout():
    """
    Logout route - clears session and redirects to login
    """
    # Remove all session variables
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('email', None)
    
    # Show logout message
    flash('You have been logged out.', 'info')
    
    # Redirect to login page
    return redirect(url_for('login'))

# Route for dashboard (protected route)
@app.route('/dashboard')
def dashboard():
    """
    Dashboard route - requires authentication
    Shows user profile information
    """
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to access dashboard.', 'warning')
        return redirect(url_for('login'))
    
    # Get database connection
    connection = get_db_connection()
    
    # Check if connection was successful
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Create cursor
        cursor = connection.cursor(dictionary=True)
        
        # Query to get user details
        query = "SELECT id, username, email, created_at FROM users WHERE id = %s"
        cursor.execute(query, (session['user_id'],))
        
        # Fetch user data
        user = cursor.fetchone()
        
        # Render dashboard with user data
        return render_template('dashboard.html', user=user)
        
    except Error as e:
        # Handle database errors
        print(f"Database error: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('index'))
        
    finally:
        # Always close cursor and connection
        if connection.is_connected():
            cursor.close()
            connection.close()

# Health check endpoint for Docker
@app.route('/health')
def health():
    """
    Health check endpoint - used by Docker to verify app is running
    Returns JSON with status
    """
    return {'status': 'healthy', 'service': 'flask-app'}, 200

# Main execution block
if __name__ == '__main__':
    # Print startup message
    print("Starting Flask application...")
    print(f"Database host: {DB_CONFIG['host']}")
    print(f"Database name: {DB_CONFIG['database']}")
    
    # Wait a moment for database to be ready
    time.sleep(2)
    
    # Test database connection
    test_conn = get_db_connection()
    if test_conn:
        print("Database connection successful!")
        test_conn.close()
    else:
        print("Warning: Could not connect to database on startup")
    
    # Run Flask application
    # host='0.0.0.0' makes it accessible from outside container
    # port=5000 is the default Flask port
    # debug=True enables auto-reload and detailed errors (disable in production)
    app.run(host='0.0.0.0', port=5000, debug=True)