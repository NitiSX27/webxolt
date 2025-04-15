from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
from forum import db
from forum.models import User
from forum.forms import RegistrationForm, LoginForm, NewThreadForm, ReplyForm

bp = Blueprint('forum', __name__)

@bp.route('/')
def home():
    print("Home route accessed")  # Debugging line
    categories = [{'_id': str(cat['_id']), 'name': cat['name']} for cat in db.categories.find()]
    
    # Get recent threads (limit to 10)
    recent_threads = list(db.threads.find().sort('created_at', -1).limit(10))
    
    # If user is logged in, get threads they've commented on
    user_threads = []
    if current_user.is_authenticated:
        user_replies = db.replies.find({'author': ObjectId(current_user.id)})
        thread_ids = {reply['thread'] for reply in user_replies}
        user_threads = list(db.threads.find({'_id': {'$in': list(thread_ids)}}).sort('created_at', -1).limit(5))
    
    # Process thread data for template
    processed_threads = []
    for thread in recent_threads:
        thread['_id'] = str(thread['_id'])
        thread['author'] = db.users.find_one({'_id': thread['author']})['username']
        thread['reply_count'] = db.replies.count_documents({'thread': ObjectId(thread['_id'])})
        processed_threads.append(thread)
    
    processed_user_threads = []
    for thread in user_threads:
        thread['_id'] = str(thread['_id'])
        thread['author'] = db.users.find_one({'_id': thread['author']})['username']
        thread['reply_count'] = db.replies.count_documents({'thread': ObjectId(thread['_id'])})
        processed_user_threads.append(thread)
    
    return render_template(
        'home.html', 
        categories=categories,
        recent_threads=processed_threads,
        user_threads=processed_user_threads
    )

from flask import session
import random
import smtplib
from email.mime.text import MIMEText

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        if db.users.find_one({'username': username}):
            flash('Username already exists')
            return redirect(url_for('forum.register'))
        if db.users.find_one({'email': email}):
            flash('Email already registered')
            return redirect(url_for('forum.register'))
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        # Store user data and OTP in session temporarily
        session['registration_data'] = {
            'username': username,
            'email': email,
            'password': generate_password_hash(form.password.data),
            'otp': otp
        }
        # Send OTP email
        send_otp_email(email, otp)
        flash('An OTP has been sent to your email. Please verify to complete registration.')
        return redirect(url_for('forum.verify_otp'))
    return render_template('register.html', form=form)

@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'registration_data' not in session:
        flash('No registration data found. Please register again.')
        return redirect(url_for('forum.register'))
    if request.method == 'POST':
        input_otp = request.form.get('otp')
        registration_data = session.get('registration_data')
        if input_otp == registration_data.get('otp'):
            # Insert user into db with is_verified True
            db.users.insert_one({
                'username': registration_data['username'],
                'email': registration_data['email'],
                'password': registration_data['password'],
                'is_verified': True
            })
            session.pop('registration_data', None)
            flash('Registration successful! Please log in.')
            return redirect(url_for('forum.login'))
        else:
            flash('Invalid OTP. Please try again.')
    return render_template('verify_otp.html')

def send_otp_email(to_email, otp):
    """
    Sends an OTP email to the specified email address using configured SMTP.
    """
    import smtplib
    from email.mime.text import MIMEText

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = '2022.nitish.bhosle@ves.ac.in'
    smtp_password = 'dljlajiixyfxvdrx'  # App password without spaces

    subject = 'Your OTP for Forum Registration'
    body = f'Your OTP for registration is: {otp}'

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_username
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, [to_email], msg.as_string())
        server.quit()
    except Exception as e:
        print(f'Failed to send email: {e}')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_data = db.users.find_one({'username': form.username.data})
        if user_data and check_password_hash(user_data['password'], form.password.data):
            user = User(user_data)
            login_user(user)
            flash('Logged in successfully')
            return redirect(url_for('forum.home'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('forum.home'))

@bp.route('/category/<category_id>')
def category(category_id):
    category = db.categories.find_one({'_id': ObjectId(category_id)})
    if not category:
        flash('Category not found')
        return redirect(url_for('forum.home'))
    threads = db.threads.find({'category': ObjectId(category_id)}).sort('created_at', -1)
    threads_list = [
        {**thread, '_id': str(thread['_id']), 'author': db.users.find_one({'_id': thread['author']})['username']}
        for thread in threads
    ]
    return render_template('category.html', category={'_id': str(category['_id']), 'name': category['name']}, threads=threads_list)

@bp.route('/thread/new/<category_id>', methods=['GET', 'POST'])
@login_required
def new_thread(category_id):
    category = db.categories.find_one({'_id': ObjectId(category_id)})
    if not category:
        flash('Category not found')
        return redirect(url_for('forum.home'))
    form = NewThreadForm()
    if form.validate_on_submit():
        thread_id = db.threads.insert_one({
            'title': form.title.data,
            'content': form.content.data,
            'author': ObjectId(current_user.id),
            'category': ObjectId(category_id),
            'created_at': datetime.utcnow()
        }).inserted_id
        flash('Thread created successfully')
        return redirect(url_for('forum.thread', thread_id=str(thread_id)))
    return render_template('new_thread.html', form=form, category={'_id': str(category['_id']), 'name': category['name']})

@bp.route('/thread/<thread_id>')
def thread(thread_id):
    thread = db.threads.find_one({'_id': ObjectId(thread_id)})
    if not thread:
        flash('Thread not found')
        return redirect(url_for('forum.home'))
    thread['_id'] = str(thread['_id'])
    author = db.users.find_one({'_id': thread['author']})['username']
    # Initialize likes and dislikes if not present
    thread['likes'] = thread.get('likes', 0)
    thread['dislikes'] = thread.get('dislikes', 0)
    replies = db.replies.find({'thread': ObjectId(thread_id)}).sort('created_at', 1)
    replies_list = []
    for reply in replies:
        reply['_id'] = str(reply['_id'])
        reply['author'] = db.users.find_one({'_id': reply['author']})['username']
        reply['likes'] = reply.get('likes', 0)
        reply['dislikes'] = reply.get('dislikes', 0)
        replies_list.append(reply)
    form = ReplyForm()
    return render_template('thread.html', thread=thread, author=author, replies=replies_list, form=form)

@bp.route('/thread/<thread_id>/like', methods=['POST'])
@login_required
def like_thread(thread_id):
    user_id = ObjectId(current_user.id)
    thread = db.threads.find_one({'_id': ObjectId(thread_id)})
    if not thread:
        return {'error': 'Thread not found'}, 404

    liked_by = thread.get('liked_by', [])
    disliked_by = thread.get('disliked_by', [])

    if user_id in liked_by:
        # User already liked, do nothing or optionally remove like
        return {'likes': thread.get('likes', 0)}
    else:
        update_ops = {'$inc': {'likes': 1}}
        if user_id in disliked_by:
            update_ops['$inc']['dislikes'] = -1
            update_ops['$pull'] = {'disliked_by': user_id}
        update_ops.setdefault('$addToSet', {})['liked_by'] = user_id
        db.threads.update_one({'_id': ObjectId(thread_id)}, update_ops)

    updated_thread = db.threads.find_one({'_id': ObjectId(thread_id)})
    return {'likes': updated_thread.get('likes', 0)}

@bp.route('/thread/<thread_id>/dislike', methods=['POST'])
@login_required
def dislike_thread(thread_id):
    user_id = ObjectId(current_user.id)
    thread = db.threads.find_one({'_id': ObjectId(thread_id)})
    if not thread:
        return {'error': 'Thread not found'}, 404

    liked_by = thread.get('liked_by', [])
    disliked_by = thread.get('disliked_by', [])

    if user_id in disliked_by:
        # User already disliked, do nothing or optionally remove dislike
        return {'dislikes': thread.get('dislikes', 0)}
    else:
        update_ops = {'$inc': {'dislikes': 1}}
        if user_id in liked_by:
            update_ops['$inc']['likes'] = -1
            update_ops['$pull'] = {'liked_by': user_id}
        update_ops.setdefault('$addToSet', {})['disliked_by'] = user_id
        db.threads.update_one({'_id': ObjectId(thread_id)}, update_ops)

    updated_thread = db.threads.find_one({'_id': ObjectId(thread_id)})
    return {'dislikes': updated_thread.get('dislikes', 0)}

@bp.route('/reply/<reply_id>/like', methods=['POST'])
@login_required
def like_reply(reply_id):
    user_id = ObjectId(current_user.id)
    reply = db.replies.find_one({'_id': ObjectId(reply_id)})
    if not reply:
        return {'error': 'Reply not found'}, 404

    liked_by = reply.get('liked_by', [])
    disliked_by = reply.get('disliked_by', [])

    if user_id in liked_by:
        return {'likes': reply.get('likes', 0)}
    else:
        update_ops = {'$inc': {'likes': 1}}
        if user_id in disliked_by:
            update_ops['$inc']['dislikes'] = -1
            update_ops['$pull'] = {'disliked_by': user_id}
        update_ops.setdefault('$addToSet', {})['liked_by'] = user_id
        db.replies.update_one({'_id': ObjectId(reply_id)}, update_ops)

    updated_reply = db.replies.find_one({'_id': ObjectId(reply_id)})
    return {'likes': updated_reply.get('likes', 0)}

@bp.route('/reply/<reply_id>/dislike', methods=['POST'])
@login_required
def dislike_reply(reply_id):
    user_id = ObjectId(current_user.id)
    reply = db.replies.find_one({'_id': ObjectId(reply_id)})
    if not reply:
        return {'error': 'Reply not found'}, 404

    liked_by = reply.get('liked_by', [])
    disliked_by = reply.get('disliked_by', [])

    if user_id in disliked_by:
        return {'dislikes': reply.get('dislikes', 0)}
    else:
        update_ops = {'$inc': {'dislikes': 1}}
        if user_id in liked_by:
            update_ops['$inc']['likes'] = -1
            update_ops['$pull'] = {'liked_by': user_id}
        update_ops.setdefault('$addToSet', {})['disliked_by'] = user_id
        db.replies.update_one({'_id': ObjectId(reply_id)}, update_ops)

    updated_reply = db.replies.find_one({'_id': ObjectId(reply_id)})
    return {'dislikes': updated_reply.get('dislikes', 0)}

@bp.route('/thread/<thread_id>/reply', methods=['GET', 'POST'])
@login_required
def reply(thread_id):
    thread = db.threads.find_one({'_id': ObjectId(thread_id)})
    if not thread:
        flash('Thread not found')
        return redirect(url_for('forum.home'))
    form = ReplyForm()
    if form.validate_on_submit():
        db.replies.insert_one({
            'thread': ObjectId(thread_id),
            'author': ObjectId(current_user.id),
            'content': form.content.data,
            'created_at': datetime.utcnow()
        })
        flash('Reply posted successfully')
        return redirect(url_for('forum.thread', thread_id=thread_id))
    return render_template('reply.html', form=form, thread={'_id': str(thread['_id']), 'title': thread['title']})
