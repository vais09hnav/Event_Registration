from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL


app = Flask(__name__)
app.secret_key = '123456'



# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  
app.config['MYSQL_DB'] = 'event_registration'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful! Please proceed to login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()
        if user and user[3] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('events'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/events')
def events():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM events")
    events = cur.fetchall()
    cur.close()
    if not events:
        flash('No events available at the moment.', 'info')
    return render_template('events.html', events=events)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT events.id, events.name, events.description, events.date, 
               GROUP_CONCAT(register.name) AS registered_users
        FROM events
        LEFT JOIN register ON events.id = register.event_id
        GROUP BY events.id
    """)
    events = cur.fetchall()
    cur.close()
    return render_template('admin.html', events=events)

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_description = request.form['event_description']
        event_date = request.form['event_date']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO events (name, description, date) VALUES (%s, %s, %s)",
                    (event_name, event_description, event_date))
        mysql.connection.commit()
        cur.close()
        flash('Event added successfully!', 'success')
        return redirect(url_for('admin'))
    return render_template('add_event.html')

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM events WHERE id=%s", (event_id,))
    event = cur.fetchone()
    cur.close()
    
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_description = request.form['event_description']
        event_date = request.form['event_date']
        
        cur = mysql.connection.cursor()
        cur.execute("""UPDATE events SET name=%s, description=%s, date=%s WHERE id=%s""",
                    (event_name, event_description, event_date, event_id))
        mysql.connection.commit()
        cur.close()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('edit_event.html', event_id=event_id, event=event)

@app.route('/delete_event/<int:event_id>', methods=['GET'])
def delete_event(event_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM events WHERE id=%s", (event_id,))
    mysql.connection.commit()
    cur.close()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin'))


@app.route('/register/<int:event_id>', methods=['GET', 'POST'])
def register(event_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to login first to register for an event.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        additional_info = request.form.get('additional_info')

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO register (user_id, event_id, name, contact, additional_info)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, event_id, name, contact, additional_info))
        mysql.connection.commit()
        cur.close()

        flash('Successfully registered for the event!', 'success')
        return redirect(url_for('events'))
    return render_template('register.html', event_id=event_id)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
