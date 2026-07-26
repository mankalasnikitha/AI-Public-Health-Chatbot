# ============================================================
# app.py — HealthBot AI with User Auth + Persistent History
# Flask + Groq API + SQLite Database
# ============================================================

# ── Imports ──────────────────────────────────────────────────
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, flash
)
# Flask        → web framework
# render_template → loads HTML from templates/
# request      → reads incoming HTTP data
# jsonify      → converts dicts to JSON responses
# session      → stores temporary data per browser session
# redirect     → sends user to a different URL
# url_for      → builds URLs from function names (safer than hardcoding)
# flash        → one-time messages shown to the user (e.g. "Wrong password")

from groq import Groq
# Groq → free AI API running LLaMA 3.3 70B

from dotenv import load_dotenv
# load_dotenv → reads .env file for secret keys

import os
# os → reads environment variables

import sqlite3
# sqlite3 → Python's built-in database library
# SQLite stores everything in a single .db file — no server needed!

from werkzeug.security import generate_password_hash, check_password_hash
# generate_password_hash → converts plain password → secure hash (e.g. "abc" → "pbkdf2:sha256:...")
# check_password_hash    → safely compares a password attempt against the stored hash
# NEVER store plain-text passwords! Always hash them.

from datetime import datetime
# datetime → for timestamping messages

from functools import wraps
# wraps → used to build the login_required decorator properly


# ── Load env & create app ────────────────────────────────────
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "healthbot_super_secret_2024")

# ── Groq client ──────────────────────────────────────────────
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── System prompt ────────────────────────────────────────────
SYSTEM_PROMPT = """You are a knowledgeable and compassionate Public Health Assistant specializing in disease awareness, prevention, and general health education.

Your responsibilities:
- Provide accurate, easy-to-understand information about diseases, symptoms, and prevention
- Educate users about public health best practices
- Explain medical terms in simple, friendly language
- Always recommend consulting a real doctor for personal medical advice
- Focus on WHO-approved and evidence-based health information
- Cover topics like: infectious diseases, chronic conditions, mental health awareness, nutrition, hygiene, and vaccination

Important rules:
- Never diagnose a user's personal condition
- Always add a disclaimer to consult a healthcare professional for personal medical issues
- Be empathetic, clear, and encouraging
- Use bullet points and structured formatting for clarity when listing symptoms or steps
- Keep responses concise but informative (aim for 150-250 words unless more detail is truly needed)

You are NOT a replacement for professional medical advice. You are a public health educator."""


# ════════════════════════════════════════════════════════════
# DATABASE SETUP
# ════════════════════════════════════════════════════════════

DATABASE = "healthbot.db"
# DATABASE → the filename of our SQLite database file
# It will be created automatically in the project folder

def get_db():
    """
    Opens a connection to the SQLite database.
    Returns a connection object we can use to run SQL queries.
    """
    conn = sqlite3.connect(DATABASE)
    # sqlite3.connect() → opens (or creates) the .db file
    # If healthbot.db doesn't exist yet, SQLite creates it automatically

    conn.row_factory = sqlite3.Row
    # row_factory = sqlite3.Row → makes query results behave like dictionaries
    # Without this: row[0], row[1]  (hard to read)
    # With this:    row['username'], row['email']  (much clearer!)

    return conn


def init_db():
    """
    Creates the database tables if they don't exist yet.
    Called once when the app starts.
    """
    conn = get_db()
    cursor = conn.cursor()
    # cursor → an object we use to execute SQL commands

    # ── Table 1: users ───────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    UNIQUE NOT NULL,
            email     TEXT    UNIQUE NOT NULL,
            password  TEXT    NOT NULL,
            created_at TEXT   DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # CREATE TABLE IF NOT EXISTS → only creates if the table doesn't already exist
    # id       → auto-incrementing unique number for each user (1, 2, 3, ...)
    # username → must be unique, cannot be empty (NOT NULL)
    # email    → must be unique, cannot be empty
    # password → stores the HASHED password (never plain text!)
    # created_at → automatically set to current date/time when row is inserted

    # ── Table 2: conversations ───────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            title      TEXT    DEFAULT 'New Conversation',
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Each "conversation" is a chat session (like a thread)
    # user_id → links this conversation to a specific user
    # FOREIGN KEY → enforces that user_id must exist in the users table
    # title → auto-generated from the first message

    # ── Table 3: messages ────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            role            TEXT    NOT NULL,
            content         TEXT    NOT NULL,
            created_at      TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id),
            FOREIGN KEY (user_id)         REFERENCES users(id)
        )
    ''')
    # Each message belongs to a conversation AND a user
    # role    → 'user' or 'assistant'
    # content → the actual message text

    conn.commit()
    # commit() → saves all the CREATE TABLE changes to disk
    conn.close()
    # close() → always close the connection when done to free resources


# ════════════════════════════════════════════════════════════
# AUTH DECORATOR — Protects routes that need login
# ════════════════════════════════════════════════════════════

def login_required(f):
    """
    A decorator that protects routes.
    If a user tries to access a protected page without being logged in,
    they get redirected to the login page.

    Usage:
        @app.route('/chat')
        @login_required       ← add this line to protect the route
        def chat():
            ...
    """
    @wraps(f)
    # @wraps(f) → preserves the original function's name and docstring
    # Without this, all decorated functions would appear as 'wrapper' in debug tools

    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            # session['user_id'] is set when a user logs in
            # If it's missing, they are not logged in
            flash('Please log in to access the chatbot.', 'warning')
            return redirect(url_for('login'))
            # Redirect to the login page
        return f(*args, **kwargs)
        # If they ARE logged in, run the original route function normally
    return wrapper


# ════════════════════════════════════════════════════════════
# ROUTES — Authentication
# ════════════════════════════════════════════════════════════

@app.route('/')
def home():
    """
    Root URL — if logged in, go to chat. If not, show landing page.
    """
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return render_template('landing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    GET  → Show the registration form
    POST → Process the form submission
    """
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    # Already logged in? Go straight to chat.

    if request.method == 'POST':
        # Read the form fields sent by the browser
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # ── Validation ───────────────────────────────────────
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth.html', mode='register')

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return render_template('auth.html', mode='register')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth.html', mode='register')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth.html', mode='register')

        # ── Save to database ─────────────────────────────────
        hashed_pw = generate_password_hash(password)
        # generate_password_hash → turns "mypassword123" into something like:
        # "pbkdf2:sha256:260000$abc123..." — impossible to reverse!

        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_pw)
            )
            # INSERT INTO → adds a new row to the users table
            # (?, ?, ?) → placeholders prevent SQL injection attacks
            # Never use f-strings or .format() for SQL! Always use ?

            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            # IntegrityError → raised when UNIQUE constraint fails
            # Means username or email already exists in the database
            flash('Username or email already taken. Try another.', 'error')
            return render_template('auth.html', mode='register')
        finally:
            conn.close()
            # finally → always runs, even if an exception occurred
            # Ensures the database connection is always closed

    return render_template('auth.html', mode='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → Show the login form
    POST → Verify credentials and log in
    """
    if 'user_id' in session:
        return redirect(url_for('chat_page'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth.html', mode='login')

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        # SELECT * FROM users WHERE username = ? → finds the user row
        # fetchone() → returns just one row (or None if not found)
        conn.close()

        if user is None or not check_password_hash(user['password'], password):
            # user is None         → username doesn't exist
            # check_password_hash  → compares entered password with stored hash
            # If either fails → show a vague error (don't reveal which one failed!)
            flash('Invalid username or password.', 'error')
            return render_template('auth.html', mode='login')

        # ── Login successful — store user info in session ────
        session['user_id']  = user['id']
        session['username'] = user['username']
        # session is like a secure cookie stored in the browser
        # Flask signs it with the secret_key so it can't be tampered with

        flash(f"Welcome back, {user['username']}! 👋", 'success')
        return redirect(url_for('chat_page'))

    return render_template('auth.html', mode='login')


@app.route('/logout')
def logout():
    """
    Clears the session (logs the user out) and redirects to home.
    """
    session.clear()
    # session.clear() → removes ALL data from the session
    # The user is now effectively logged out
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ════════════════════════════════════════════════════════════
# ROUTES — Chat Page
# ════════════════════════════════════════════════════════════

@app.route('/chat')
@login_required
def chat_page():
    """
    The main chat interface. Protected by @login_required.
    """
    user_id = session['user_id']
    conn = get_db()

    # Load all conversations for this user (newest first)
    conversations = conn.execute('''
        SELECT c.id, c.title, c.updated_at,
               COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY c.updated_at DESC
    ''', (user_id,)).fetchall()
    # LEFT JOIN → includes conversations even if they have 0 messages
    # COUNT(m.id) → counts how many messages each conversation has
    # ORDER BY updated_at DESC → newest conversations first

    conn.close()

    # Start a fresh conversation if none exists
    if 'conversation_id' not in session:
        session['conversation_id'] = None

    return render_template('chat.html',
        username=session['username'],
        conversations=conversations
    )


# ════════════════════════════════════════════════════════════
# ROUTES — Chat API Endpoints
# ════════════════════════════════════════════════════════════

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """
    Receives a message, sends to Groq, saves both messages to DB,
    returns AI reply as JSON.
    """
    user_id = session['user_id']
    data    = request.get_json()
    user_message     = data.get('message', '').strip()
    conversation_id  = data.get('conversation_id')
    # conversation_id → which chat thread this message belongs to
    # If None → we need to create a new conversation first

    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    conn = get_db()

    # ── Create a new conversation if needed ──────────────────
    if not conversation_id:
        # Generate a short title from the first message
        title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        # Take first 50 chars of the user's message as the conversation title
        # Example: "What are symptoms of dengue fever?" → title as-is
        # Example: "Tell me everything about COVID-19 prevention tips" → "Tell me everything about COVID-19 prevention ti..."

        cursor = conn.execute(
            'INSERT INTO conversations (user_id, title) VALUES (?, ?)',
            (user_id, title)
        )
        conn.commit()
        conversation_id = cursor.lastrowid
        # lastrowid → the auto-generated ID of the row we just inserted
        session['conversation_id'] = conversation_id

    # ── Load existing messages for this conversation ─────────
    past_messages = conn.execute('''
        SELECT role, content FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    ''', (conversation_id,)).fetchall()
    # Fetch all messages in this conversation, oldest first
    # This gives Groq the full context of the conversation

    # Build the messages list for Groq
    chat_history = [{'role': row['role'], 'content': row['content']}
                    for row in past_messages]
    # Convert sqlite3.Row objects to plain dicts that Groq can use

    # Add the new user message
    chat_history.append({'role': 'user', 'content': user_message})

    # Keep last 20 messages to avoid token limit
    if len(chat_history) > 20:
        chat_history = chat_history[-20:]

    # Groq needs system prompt as the first message
    messages_to_send = [{'role': 'system', 'content': SYSTEM_PROMPT}] + chat_history

    # ── Call Groq API ─────────────────────────────────────────
    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages_to_send,
            max_tokens=1024,
            temperature=0.7,
        )
        ai_reply = response.choices[0].message.content

    except Exception as e:
        conn.close()
        error_msg = str(e)
        if 'invalid_api_key' in error_msg.lower() or 'authentication' in error_msg.lower():
            return jsonify({'error': 'Invalid Groq API key. Check your .env file.'}), 401
        elif 'rate_limit' in error_msg.lower():
            return jsonify({'error': 'Rate limit reached. Please wait a moment.'}), 429
        else:
            return jsonify({'error': f'AI error: {error_msg}'}), 500

    # ── Save BOTH messages to the database ───────────────────
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # strftime → formats the datetime as a readable string
    # Example: "2024-12-15 14:32:07"

    conn.execute(
        'INSERT INTO messages (conversation_id, user_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)',
        (conversation_id, user_id, 'user', user_message, now)
    )
    # Save user's message to DB

    conn.execute(
        'INSERT INTO messages (conversation_id, user_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)',
        (conversation_id, user_id, 'assistant', ai_reply, now)
    )
    # Save AI's reply to DB

    # Update conversation's updated_at timestamp
    conn.execute(
        'UPDATE conversations SET updated_at = ? WHERE id = ?',
        (now, conversation_id)
    )
    # UPDATE → modifies existing rows
    # This keeps the "most recent activity" time accurate

    conn.commit()
    conn.close()

    return jsonify({
        'reply': ai_reply,
        'conversation_id': conversation_id
    })


@app.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    """
    Returns all conversations for the logged-in user as JSON.
    Used by the sidebar to dynamically refresh.
    """
    user_id = session['user_id']
    conn = get_db()
    conversations = conn.execute('''
        SELECT c.id, c.title, c.updated_at,
               COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY c.updated_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return jsonify({'conversations': [dict(c) for c in conversations]})
    # dict(c) → converts sqlite3.Row to a plain dictionary for JSON serialization


@app.route('/api/conversations/<int:conv_id>', methods=['GET'])
@login_required
def get_conversation_messages(conv_id):
    """
    Returns all messages for a specific conversation.
    Used when the user clicks a past conversation in the sidebar.
    conv_id → the conversation ID from the URL (e.g. /api/conversations/5)
    """
    user_id = session['user_id']
    conn = get_db()

    # Security check: make sure this conversation belongs to the logged-in user
    conv = conn.execute(
        'SELECT * FROM conversations WHERE id = ? AND user_id = ?',
        (conv_id, user_id)
    ).fetchone()

    if not conv:
        conn.close()
        return jsonify({'error': 'Conversation not found'}), 404
        # 404 → HTTP "Not Found". Also prevents users from accessing other users' chats.

    messages = conn.execute('''
        SELECT role, content, created_at FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    ''', (conv_id,)).fetchall()
    conn.close()

    return jsonify({
        'conversation_id': conv_id,
        'title': conv['title'],
        'messages': [dict(m) for m in messages]
    })


@app.route('/api/conversations/new', methods=['POST'])
@login_required
def new_conversation():
    """
    Starts a brand new conversation (clears the current one from session).
    """
    session['conversation_id'] = None
    return jsonify({'status': 'ok'})


@app.route('/api/conversations/<int:conv_id>', methods=['DELETE'])
@login_required
def delete_conversation(conv_id):
    """
    Deletes a conversation and all its messages.
    """
    user_id = session['user_id']
    conn = get_db()

    # Verify ownership before deleting
    conv = conn.execute(
        'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
        (conv_id, user_id)
    ).fetchone()

    if not conv:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    conn.execute('DELETE FROM messages WHERE conversation_id = ?', (conv_id,))
    conn.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))
    # Delete messages first (they reference the conversation via foreign key)
    # Then delete the conversation itself
    conn.commit()
    conn.close()

    if session.get('conversation_id') == conv_id:
        session['conversation_id'] = None

    return jsonify({'status': 'deleted'})


# ════════════════════════════════════════════════════════════
# START APP
# ════════════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    # init_db() → creates the database tables on first run
    # Safe to call every time — uses CREATE TABLE IF NOT EXISTS

    app.run(debug=True)
