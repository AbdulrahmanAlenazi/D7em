from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from functools import wraps
import re
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'
login_manager.login_message_category = 'error'

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

# Category Model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    name_ar = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    icon = db.Column(db.String(10), default='')

# Transaction Model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    description = db.Column(db.String(255), default='')
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True, cascade='all, delete-orphan'))
    category = db.relationship('Category')

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

# Create tables and seed categories
with app.app_context():
    db.create_all()
    if Category.query.count() == 0:
        defaults = [
            Category(name='Salary', name_ar='راتب', type='income', icon='💰'),
            Category(name='Freelance', name_ar='عمل حر', type='income', icon='💻'),
            Category(name='Investment', name_ar='استثمار', type='income', icon='📈'),
            Category(name='Other Income', name_ar='دخل آخر', type='income', icon='💵'),
            Category(name='Food', name_ar='طعام', type='expense', icon='🍕'),
            Category(name='Transport', name_ar='مواصلات', type='expense', icon='🚗'),
            Category(name='Housing', name_ar='سكن', type='expense', icon='🏠'),
            Category(name='Bills', name_ar='فواتير', type='expense', icon='📄'),
            Category(name='Shopping', name_ar='تسوق', type='expense', icon='🛍'),
            Category(name='Health', name_ar='صحة', type='expense', icon='🏥'),
            Category(name='Education', name_ar='تعليم', type='expense', icon='📚'),
            Category(name='Entertainment', name_ar='ترفيه', type='expense', icon='🎬'),
            Category(name='Other Expense', name_ar='مصروف آخر', type='expense', icon='📦'),
        ]
        db.session.add_all(defaults)
        db.session.commit()

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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = normalize_email(request.form.get('email'))
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        if not name or len(name) < 2:
            flash('الاسم يجب أن يكون حرفين على الأقل', 'error')
            return render_template('profile.html')

        if not email or not validate_email(email):
            flash('يرجى إدخال بريد إلكتروني صحيح', 'error')
            return render_template('profile.html')

        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != current_user.id:
            flash('البريد الإلكتروني مستخدم من قبل مستخدم آخر', 'error')
            return render_template('profile.html')

        current_user.name = name
        current_user.email = email

        if new_password:
            if not current_password or not current_user.check_password(current_password):
                flash('كلمة المرور الحالية غير صحيحة', 'error')
                return render_template('profile.html')
            is_valid, error_msg = validate_password(new_password)
            if not is_valid:
                flash(error_msg, 'error')
                return render_template('profile.html')
            current_user.set_password(new_password)

        db.session.commit()
        flash('تم تحديث بياناتك بنجاح', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html')

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

# Tracker Routes
@app.route('/tracker')
@login_required
def tracker():
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    filter_type = request.args.get('type')
    filter_category = request.args.get('category')

    query = Transaction.query.filter_by(user_id=current_user.id)

    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)
    if filter_type in ('income', 'expense'):
        query = query.filter(Transaction.type == filter_type)
    if filter_category:
        query = query.filter(Transaction.category_id == int(filter_category))

    transactions = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()
    categories = Category.query.all()

    total_income = sum(float(t.amount) for t in transactions if t.type == 'income')
    total_expense = sum(float(t.amount) for t in transactions if t.type == 'expense')
    balance = total_income - total_expense

    return render_template('tracker.html',
        transactions=transactions,
        categories=categories,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance)

@app.route('/tracker/add', methods=['POST'])
@login_required
def add_transaction():
    amount = request.form.get('amount', type=float)
    tx_type = request.form.get('type')
    category_id = request.form.get('category_id', type=int)
    description = request.form.get('description', '').strip()
    date_str = request.form.get('date')

    if not amount or amount <= 0:
        flash('يرجى إدخال مبلغ صحيح', 'error')
        return redirect(url_for('tracker'))
    if tx_type not in ('income', 'expense'):
        flash('نوع المعاملة غير صحيح', 'error')
        return redirect(url_for('tracker'))
    if not category_id:
        flash('يرجى اختيار التصنيف', 'error')
        return redirect(url_for('tracker'))

    try:
        tx_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        tx_date = date.today()

    transaction = Transaction(
        user_id=current_user.id,
        amount=amount,
        type=tx_type,
        category_id=category_id,
        description=description,
        date=tx_date
    )
    db.session.add(transaction)
    db.session.commit()
    flash('تمت إضافة المعاملة بنجاح', 'success')
    return redirect(url_for('tracker'))

@app.route('/tracker/edit/<int:tx_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(tx_id):
    transaction = Transaction.query.get_or_404(tx_id)
    if transaction.user_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذه المعاملة', 'error')
        return redirect(url_for('tracker'))

    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        tx_type = request.form.get('type')
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()
        date_str = request.form.get('date')

        if not amount or amount <= 0:
            flash('يرجى إدخال مبلغ صحيح', 'error')
            return render_template('edit_transaction.html', transaction=transaction, categories=Category.query.all())
        if tx_type not in ('income', 'expense'):
            flash('نوع المعاملة غير صحيح', 'error')
            return render_template('edit_transaction.html', transaction=transaction, categories=Category.query.all())

        try:
            tx_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else transaction.date
        except ValueError:
            tx_date = transaction.date

        transaction.amount = amount
        transaction.type = tx_type
        transaction.category_id = category_id
        transaction.description = description
        transaction.date = tx_date
        db.session.commit()
        flash('تم تحديث المعاملة بنجاح', 'success')
        return redirect(url_for('tracker'))

    categories = Category.query.all()
    return render_template('edit_transaction.html', transaction=transaction, categories=categories)

@app.route('/tracker/delete/<int:tx_id>', methods=['POST'])
@login_required
def delete_transaction(tx_id):
    transaction = Transaction.query.get_or_404(tx_id)
    if transaction.user_id != current_user.id:
        flash('ليس لديك صلاحية لحذف هذه المعاملة', 'error')
        return redirect(url_for('tracker'))

    db.session.delete(transaction)
    db.session.commit()
    flash('تم حذف المعاملة', 'success')
    return redirect(url_for('tracker'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
