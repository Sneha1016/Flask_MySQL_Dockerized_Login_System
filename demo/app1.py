# app.py - Main Flask Application File
# This is the core application file that handles all routes and business logic

# Import Flask class to create web application instance
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Import MySQL connector to interact with MySQL database
import mysql.connector

# Import werkzeug security functions for password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# Import os module to generate secret key
import os

# Create Flask application instance
# __name__ helps Flask determine root path of application
app = Flask(__name__)

# Set secret key for session management (keeps user data secure)
# In production, use environment variable instead of hardcoded value
app.secret_key = os.urandom(24)  # Generates random 24-byte secret key

# Database configuration dictionary
# Contains all credentials needed to connect to MySQL database
db_config = {
    'host': 'localhost',        # MySQL server address (localhost means same machine)
    'user': 'root',             # MySQL username (change to your username)
    'password': 'root', # MySQL password (change to your password)
    'database': 'flask_auth_db' # Name of database we'll create
}

# Function to get database connection
# Returns a connection object that allows us to execute SQL queries
def get_db_connection():
    # Establish connection to MySQL database using credentials from db_config
    connection = mysql.connector.connect(**db_config)
    return connection

# Function to initialize database and create users table
# This should be run once when setting up the application
def init_db():
    # Connect to MySQL server without specifying database
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password']
    )
    # Create cursor object to execute SQL commands
    cursor = connection.cursor()
    
    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
    
    # Select the database to use
    cursor.execute(f"USE {db_config['database']}")
    
    # Create users table with all necessary columns
    # id: Primary key, auto-incremented unique identifier for each user
    # username: Stores user's username, must be unique, cannot be null
    # email: Stores user's email, must be unique, cannot be null
    # password: Stores hashed password for security, cannot be null
    # created_at: Timestamp of when user registered, defaults to current time
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Commit changes to database (save the table creation)
    connection.commit()
    
    # Close cursor and connection to free up resources
    cursor.close()
    connection.close()
    
    print("Database initialized successfully!")

# Route for home page (/)
# Methods parameter specifies which HTTP methods are allowed (GET and POST)
@app.route('/')
def index():
    # Check if user is logged in by checking if 'user_id' exists in session
    if 'user_id' in session:
        # If logged in, render home page and pass username to template
        return render_template('home.html', username=session['username'])
    # If not logged in, redirect to login page
    return redirect(url_for('login'))

# Route for user registration page
# Handles both displaying the form (GET) and processing registration (POST)
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if request method is POST (form submission)
    if request.method == 'POST':
        # Get form data from the registration form
        # request.form is a dictionary containing all form inputs
        username = request.form['username']  # Get username from form
        email = request.form['email']        # Get email from form
        password = request.form['password']  # Get password from form
        
        # Hash the password using pbkdf2:sha256 algorithm
        # Never store plain text passwords - always hash them!
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Try to insert new user into database
        try:
            # SQL INSERT statement to add new user
            # %s are placeholders that will be replaced with actual values
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                (username, email, hashed_password)
            )
            # Commit the transaction to save data to database
            connection.commit()
            
            # Display success message to user
            # flash() stores message in session to display on next page load
            flash('Registration successful! Please login.', 'success')
            
            # Redirect to login page after successful registration
            return redirect(url_for('login'))
            
        # Catch exception if username or email already exists (UNIQUE constraint)
        except mysql.connector.IntegrityError:
            # Display error message if username/email already taken
            flash('Username or email already exists!', 'danger')
            
        # Finally block always executes - clean up resources
        finally:
            # Close cursor and connection
            cursor.close()
            connection.close()
    
    # If GET request, just display the registration form
    return render_template('register.html')

# Route for user login page
# Handles both displaying login form (GET) and processing login (POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if request method is POST (form submission)
    if request.method == 'POST':
        # Get username and password from login form
        username = request.form['username']
        password = request.form['password']
        
        # Get database connection
        connection = get_db_connection()
        # Use dictionary cursor to get results as dictionaries instead of tuples
        cursor = connection.cursor(dictionary=True)
        
        # Query database to find user with given username
        # %s is placeholder for safe parameter substitution (prevents SQL injection)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        
        # Fetch one user record from query result
        # Returns None if no user found with that username
        user = cursor.fetchone()
        
        # Close database resources
        cursor.close()
        connection.close()
        
        # Check if user exists AND password matches hashed password in database
        # check_password_hash compares plain password with hashed password
        if user and check_password_hash(user['password'], password):
            # Login successful - create session variables
            # Session is a dictionary that stores data on server side
            session['user_id'] = user['id']           # Store user ID in session
            session['username'] = user['username']     # Store username in session
            
            # Display success message
            flash('Login successful!', 'success')
            
            # Redirect to home page
            return redirect(url_for('index'))
        else:
            # Login failed - display error message
            flash('Invalid username or password!', 'danger')
    
    # If GET request, display login form
    return render_template('login.html')

# Route for user logout
# Only allows GET method
@app.route('/logout')
def logout():
    # Remove all session variables to log user out
    # pop() removes specified key from dictionary
    session.pop('user_id', None)      # Remove user_id from session
    session.pop('username', None)     # Remove username from session
    
    # Display logout message
    flash('You have been logged out.', 'info')
    
    # Redirect to login page
    return redirect(url_for('login'))

# Route for dashboard (protected page - requires login)
@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'user_id' not in session:
        # If not logged in, show error and redirect to login
        flash('Please login to access dashboard.', 'warning')
        return redirect(url_for('login'))
    
    # Get database connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch current user's details from database
    cursor.execute('SELECT id, username, email, created_at FROM users WHERE id = %s', 
                   (session['user_id'],))
    user = cursor.fetchone()
    
    # Close database resources
    cursor.close()
    connection.close()
    
    # Render dashboard page with user information
    return render_template('dashboard.html', user=user)

# Main execution block
# Only runs when script is executed directly (not imported)
if __name__ == '__main__':
    # Initialize database and create tables
    init_db()
    
    # Run Flask development server
    # debug=True enables auto-reload and detailed error messages
    # In production, set debug=False
    app.run(debug=True)