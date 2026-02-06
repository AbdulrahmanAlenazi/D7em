from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import re
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def normalize_email(email):
    """Normalize email to lowercase for consistent storage and lookup"""
    return email.strip().lower() if email else None

def validate_email(email):
    """Validate email format"""
    return EMAIL_REGEX.match(email) is not None

def validate_password(password):
    """Validate password strength: min 8 chars, 1 letter, 1 number"""
    if len(password) < 8:
        return False, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل'
    if not re.search(r'[a-zA-Z]', password):
        return False, 'كلمة المرور يجب أن تحتوي على حرف واحد على الأقل'
    if not re.search(r'\d', password):
        return False, 'كلمة المرور يجب أن تحتوي على رقم واحد على الأقل'
    return True, None

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('calculator'))
    
    if request.method == 'POST':
        email = normalize_email(request.form.get('email'))
        password = request.form.get('password')
        
        if not email or not password:
            flash('يرجى ملء جميع الحقول', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(next_page or url_for('calculator'))
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('calculator'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = normalize_email(request.form.get('email'))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not name or len(name) < 2:
            flash('الاسم يجب أن يكون حرفين على الأقل', 'error')
            return render_template('signup.html')
        
        if not email or not validate_email(email):
            flash('يرجى إدخال بريد إلكتروني صحيح', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'error')
            return render_template('signup.html')
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني مستخدم بالفعل', 'error')
            return render_template('signup.html')
        
        # First user becomes admin
        is_first_user = User.query.count() == 0
        
        user = User(name=name, email=email, is_admin=is_first_user)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user, remember=True)
        flash('تم إنشاء الحساب بنجاح!', 'success')
        return redirect(url_for('calculator'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

# Dashboard Routes
@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    stats = {
        'total_users': User.query.count(),
        'admin_count': User.query.filter_by(is_admin=True).count(),
        'today_signups': User.query.filter(
            User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
    }
    return render_template('dashboard.html', users=users, stats=stats)

@app.route('/dashboard/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = normalize_email(request.form.get('email'))
        new_password = request.form.get('new_password', '')
        is_admin = request.form.get('is_admin') == 'on'
        
        # Validation
        if not name or len(name) < 2:
            flash('الاسم يجب أن يكون حرفين على الأقل', 'error')
            return render_template('edit_user.html', user=user)
        
        if not email or not validate_email(email):
            flash('يرجى إدخال بريد إلكتروني صحيح', 'error')
            return render_template('edit_user.html', user=user)
        
        # Check if email is taken by another user
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user_id:
            flash('البريد الإلكتروني مستخدم من قبل مستخدم آخر', 'error')
            return render_template('edit_user.html', user=user)
        
        # Can't remove own admin status
        if user_id == current_user.id and not is_admin:
            flash('لا يمكنك إزالة صلاحيات المسؤول من نفسك', 'error')
            return render_template('edit_user.html', user=user)
        
        # Update user
        user.name = name
        user.email = email
        user.is_admin = is_admin
        
        # Update password if provided
        if new_password:
            is_valid, error_msg = validate_password(new_password)
            if not is_valid:
                flash(error_msg, 'error')
                return render_template('edit_user.html', user=user)
            user.set_password(new_password)
        
        db.session.commit()
        flash(f'تم تحديث بيانات {user.name} بنجاح', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_user.html', user=user)

@app.route('/dashboard/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'تم حذف المستخدم {user.name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        flash('لا يمكنك تغيير صلاحياتك الخاصة', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    status = 'مسؤول' if user.is_admin else 'مستخدم عادي'
    flash(f'تم تغيير {user.name} إلى {status}', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
