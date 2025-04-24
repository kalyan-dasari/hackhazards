from flask import Flask, render_template, request, redirect, session, jsonify
from models import db, User, SessionRequest
from groq_integration import suggest_mentors
import os
from flask import flash
import pusher
from datetime import datetime



# Pusher configuration (using environment variables for security)
import pusher

pusher_client = pusher.Pusher(
  app_id='1976201',
  key='e50f48ab5a8e8aa12a48',
  secret='43cf4dad511a347a50db',
  cluster='ap2',
  ssl=True
)


app = Flask(__name__)
app.secret_key = "supersecret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check if email is already registered
        if User.query.filter_by(email=request.form['email']).first():
            return render_template('register.html', error="Email already registered")

        # Proceed to create new user
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=request.form['password'],
            role=request.form['role'],
            skills=request.form['skills'],
            bio=request.form['bio']
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'],
                                    password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    user = User.query.get(session['user_id'])

    if user.role == 'mentor':
        # Mentor sees their received requests
        requests = SessionRequest.query.filter_by(mentor_id=user.id).all()
        return render_template('dashboard.html', user=user, requests=requests)

    else:
        # Learner sees suggested mentors (optional: filter by search)
        query = request.args.get('q', '')
        mentors = User.query.filter_by(role='mentor').all()
        if query:
            mentors = [m for m in mentors if query.lower() in m.skills.lower()]
        suggested = suggest_mentors(user.skills, mentors)
        return render_template('dashboard.html', user=user, suggested=suggested)


# When learner books a session
@app.route('/request_session/<int:mentor_id>', methods=['POST'])
def request_session(mentor_id):
    if 'user_id' not in session:
        return redirect('/login')

    topic = request.form['topic']
    message = request.form['message']
    learner = User.query.get(session['user_id'])

    session_req = SessionRequest(
        learner_id=learner.id,
        mentor_id=mentor_id,
        topic=topic,
        message=message
    )
    db.session.add(session_req)
    db.session.commit()

    flash('Session request sent to the mentor!')
    return redirect('/dashboard')

# When mentor accepts/declines
@app.route('/approve_session/<int:request_id>', methods=['POST'])
def approve_session(request_id):
    action = request.form.get('action')
    req = SessionRequest.query.get(request_id)
    if action == 'accept':
        req.status = 'accepted'
        flash('You accepted the session request.')
    elif action == 'decline':
        req.status = 'declined'
        flash('You declined the session request.')
    db.session.commit()
    return redirect('/dashboard')


# Route to handle sending messages
@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        message = request.form['message']
        user = User.query.get(session['user_id'])
        channel = f'learning_channel_{user.id}'  # Example: dynamic channel based on the user

        pusher_client.trigger(channel, 'new_message', {
            'message': message,
            'user': user.username,  # Use the dynamic username
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        return jsonify({'status': 'Message Sent'})
    except Exception as e:
        return jsonify({'status': 'Error', 'message': str(e)})

# Route to handle session booking
@app.route('/book_session', methods=['POST'])
def book_session():
    try:
        session_details = request.form['session_details']
        mentor_id = request.form['mentor_id']
        user = User.query.get(session['user_id'])  # Current learner

        # Dynamically set the channel based on mentor_id
        pusher_client.trigger(f'mentor_{mentor_id}_channel', 'session_booked', {
            'session_details': session_details,
            'learner': user.username  # Dynamically use the learner's username
        })
        return jsonify({'status': 'Session Booked'})
    except Exception as e:
        return jsonify({'status': 'Error', 'message': str(e)})

# Route to handle updating mentor status
@app.route('/update_mentor_status', methods=['POST'])
def update_mentor_status():
    try:
        status = request.form['status']  # 'available' or 'booked'
        mentor_id = request.form['mentor_id']

        # Dynamically use the mentor's ID to trigger the event
        pusher_client.trigger(f'mentor_{mentor_id}_status_channel', 'status_updated', {
            'status': status
        })
        return jsonify({'status': 'Status Updated'})
    except Exception as e:
        return jsonify({'status': 'Error', 'message': str(e)})
    
@app.route('/session_history')
def session_history():
    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if user.role == 'mentor':
        sessions = SessionRequest.query.filter_by(mentor_id=user.id).filter(SessionRequest.status != 'pending').all()
    else:
        sessions = SessionRequest.query.filter_by(learner_id=user.id).filter(SessionRequest.status != 'pending').all()

    return render_template('session_history.html', user=user, sessions=sessions)


@app.route('/respond_session/<int:req_id>', methods=['POST'])
def respond_session(req_id):
    action = request.form['action']
    req = SessionRequest.query.get(req_id)
    req.status = action
    db.session.commit()
    return redirect('/dashboard')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
