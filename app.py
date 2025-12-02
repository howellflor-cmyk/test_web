from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
import os
import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barangay.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'


UPLOAD_DIR = os.path.join(app.static_folder, 'uploads', 'elected_officials')
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')

class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_no = db.Column(db.String(50), unique=True, nullable=False)
    region = db.Column(db.String(50), nullable=True)
    province = db.Column(db.String(100), nullable=True)
    city_municipality = db.Column(db.String(150), nullable=True)
    barangay = db.Column(db.String(150), nullable=True)
    purok = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    members = db.relationship('Resident', back_populates='household', lazy='dynamic')

class Resident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    middle_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    purok = db.Column(db.String(100), nullable=False)
    voter_status = db.Column(db.String(20), nullable=False, default='Voter')
    senior_citizen = db.Column(db.String(5), nullable=False, default='No')
    date_of_birth = db.Column(db.Date, nullable=True)
    place_of_birth = db.Column(db.String(150), nullable=True)
    civil_status = db.Column(db.String(50), nullable=True)
    citizenship = db.Column(db.String(100), nullable=True)
    occupation = db.Column(db.String(150), nullable=True)
    household_id = db.Column(db.Integer, db.ForeignKey('household.id'), nullable=True)
    household = db.relationship('Household', back_populates='members')

class PendingResident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    middle_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    purok = db.Column(db.String(100), nullable=False)
    voter_status = db.Column(db.String(20), nullable=False, default='Voter')
    senior_citizen = db.Column(db.String(5), nullable=False, default='No')
    date_of_birth = db.Column(db.Date, nullable=True)
    place_of_birth = db.Column(db.String(150), nullable=True)
    civil_status = db.Column(db.String(50), nullable=True)
    citizenship = db.Column(db.String(100), nullable=True)
    occupation = db.Column(db.String(150), nullable=True)
    household_id = db.Column(db.Integer, nullable=True)
    # New household data (if creating new household)
    new_household_no = db.Column(db.String(50), nullable=True)
    new_region = db.Column(db.String(50), nullable=True)
    new_province = db.Column(db.String(100), nullable=True)
    new_city_municipality = db.Column(db.String(150), nullable=True)
    new_barangay = db.Column(db.String(150), nullable=True)
    new_purok = db.Column(db.String(50), nullable=True)
    # Tracking
    submitted_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    submitter = db.relationship('Admin', foreign_keys=[submitted_by], backref='pending_submissions')
    reviewer = db.relationship('Admin', foreign_keys=[reviewed_by], backref='reviewed_submissions')

class ElectedOfficial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    order = db.Column(db.Integer, nullable=True)
    photo_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class BarangayEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    admin = db.relationship('Admin', backref='events')


@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(int(admin_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if getattr(current_user, 'role', 'user') != 'admin':
            flash('You do not have permission.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and bcrypt.check_password_hash(admin.password, password):
            login_user(admin)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_population = Resident.query.count()
    total_males = Resident.query.filter_by(gender='Male').count()
    total_females = Resident.query.filter_by(gender='Female').count()
    total_voters = Resident.query.filter_by(voter_status='Voter').count()
    total_non_voters = Resident.query.filter_by(voter_status='Non-Voter').count()
    total_senior_citizens = Resident.query.filter_by(senior_citizen='Yes').count()

    return render_template('dashboard.html',
                           total_population=total_population,
                           total_males=total_males,
                           total_females=total_females,
                           total_voters=total_voters,
                           total_non_voters=total_non_voters,
                           total_senior_citizens=total_senior_citizens)


@app.route('/elected_officials')
@login_required
def elected_officials():
    chairman = ElectedOfficial.query.filter_by(position='Chairman').first()
    kagawads = ElectedOfficial.query.filter_by(position='Kagawad').order_by(ElectedOfficial.order.is_(None), ElectedOfficial.order).all()
    return render_template('elected_officials.html', chairman=chairman, kagawads=kagawads)

@app.route('/elected_officials/add', methods=['GET', 'POST'])
@admin_required
def add_elected_official():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        position = request.form.get('position')
        order_raw = request.form.get('order')
        file = request.files.get('photo')

        if not name or position not in ('Chairman', 'Kagawad'):
            flash('Invalid name or position.', 'warning')
            return redirect(url_for('add_elected_official'))

        if position == 'Chairman':
            if ElectedOfficial.query.filter_by(position='Chairman').first():
                flash('Chairman already exists.', 'warning')
                return redirect(url_for('elected_officials'))
            official = ElectedOfficial(name=name, position='Chairman')
        else:
            count = ElectedOfficial.query.filter_by(position='Kagawad').count()
            if count >= 7:
                flash('Maximum 7 Kagawad allowed.', 'warning')
                return redirect(url_for('elected_officials'))
            order = int(order_raw) if order_raw else (count + 1)
            official = ElectedOfficial(name=name, position='Kagawad', order=order)

        if file and file.filename and allowed_file(file.filename):
            filename = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_DIR, filename))
            official.photo_filename = filename

        db.session.add(official)
        db.session.commit()
        flash(f'{position} added.', 'success')
        return redirect(url_for('elected_officials'))

    return render_template('add_edit_elected_official.html', action='add')

@app.route('/elected_officials/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_elected_official(id):
    official = ElectedOfficial.query.get_or_404(id)
    
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        position = request.form.get('position')
        order_raw = request.form.get('order')
        file = request.files.get('photo')

        if not name or position not in ('Chairman', 'Kagawad'):
            flash('Invalid name or position.', 'warning')
            return redirect(url_for('edit_elected_official', id=id))

        if position == 'Chairman':
            existing = ElectedOfficial.query.filter(ElectedOfficial.position=='Chairman', ElectedOfficial.id != official.id).first()
            if existing:
                flash('Another Chairman exists.', 'warning')
                return redirect(url_for('elected_officials'))
            official.position = 'Chairman'
            official.order = None
        else:
            official.position = 'Kagawad'
            official.order = int(order_raw) if order_raw else None

        official.name = name

        if file and file.filename and allowed_file(file.filename):
            if official.photo_filename:
                old_path = os.path.join(UPLOAD_DIR, official.photo_filename)
                if os.path.exists(old_path):
                    try: os.remove(old_path)
                    except: pass
            filename = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_DIR, filename))
            official.photo_filename = filename

        db.session.commit()
        flash('Official updated.', 'success')
        return redirect(url_for('elected_officials'))

    return render_template('add_edit_elected_official.html', action='edit', official=official)

@app.route('/elected_officials/delete/<int:id>', methods=['POST'])
@admin_required
def delete_elected_official(id):
    official = ElectedOfficial.query.get_or_404(id)
    if official.photo_filename:
        p = os.path.join(UPLOAD_DIR, official.photo_filename)
        if os.path.exists(p):
            try: os.remove(p)
            except: pass
    db.session.delete(official)
    db.session.commit()
    flash('Official removed.', 'success')
    return redirect(url_for('elected_officials'))


@app.route('/residents')
@login_required
def residents():
    search = request.args.get('search', '').strip()
    query = Resident.query
    
    if search:
        query = query.filter(Resident.first_name.ilike(f'{search}%'))
    
    residents_list = query.order_by(Resident.first_name).all()
    return render_template('residents.html', residents=residents_list)

@app.route('/add_resident', methods=['GET', 'POST'])
@login_required  # Changed from @admin_required to @login_required
def add_resident():
    if request.method == 'POST':
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        gender = request.form.get('gender')
        age = request.form.get('age', '').strip()
        purok = request.form.get('purok', '').strip()
        voter_status = request.form.get('voter_status')
        senior_citizen = request.form.get('senior_citizen')
        date_of_birth_str = request.form.get('date_of_birth', '').strip()
        place_of_birth = request.form.get('place_of_birth', '').strip()
        civil_status = request.form.get('civil_status', '').strip()
        citizenship = request.form.get('citizenship', '').strip()
        occupation = request.form.get('occupation', '').strip()
        household_select = request.form.get('household_select')

        if not (last_name and first_name and middle_name and gender and age and purok and voter_status and senior_citizen):
            flash('Fill all required fields.', 'warning')
            return redirect(url_for('add_resident'))

        try:
            age = int(age)
            if age < 0:
                raise ValueError
        except ValueError:
            flash('Age must be positive.', 'warning')
            return redirect(url_for('add_resident'))

        dob = None
        if date_of_birth_str:
            try:
                dob = datetime.datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'warning')
                return redirect(url_for('add_resident'))

        # If user is admin, add directly to residents
        if current_user.role == 'admin':
            household_id = None
            
            # Handle household selection
            if household_select == 'new':
                new_household_no = request.form.get('new_household_no', '').strip()
                new_region = request.form.get('new_region', '').strip()
                new_province = request.form.get('new_province', '').strip()
                new_city_municipality = request.form.get('new_city_municipality', '').strip()
                new_barangay = request.form.get('new_barangay', '').strip()
                new_purok_hh = request.form.get('new_purok', '').strip()
                
                if not new_household_no:
                    flash('Household number is required when creating new household.', 'warning')
                    return redirect(url_for('add_resident'))
                
                existing_household = Household.query.filter_by(household_no=new_household_no).first()
                if existing_household:
                    flash('Household number already exists.', 'warning')
                    return redirect(url_for('add_resident'))
                
                new_household = Household(
                    household_no=new_household_no,
                    region=new_region or None,
                    province=new_province or None,
                    city_municipality=new_city_municipality or None,
                    barangay=new_barangay or None,
                    purok=new_purok_hh or None
                )
                db.session.add(new_household)
                db.session.flush()
                household_id = new_household.id
                
            elif household_select and household_select != 'none':
                try:
                    household_id = int(household_select)
                except (TypeError, ValueError):
                    household_id = None

            resident = Resident(
                last_name=last_name, first_name=first_name, middle_name=middle_name,
                gender=gender, age=age, purok=purok, voter_status=voter_status,
                senior_citizen=senior_citizen, date_of_birth=dob, place_of_birth=place_of_birth or None,
                civil_status=civil_status or None, citizenship=citizenship or None,
                occupation=occupation or None, household_id=household_id
            )
            db.session.add(resident)
            db.session.commit()
            flash('Resident added successfully.', 'success')
            return redirect(url_for('residents'))
        
        # If user is not admin, submit for approval
        else:
            household_id = None
            new_household_data = {}
            
            if household_select == 'new':
                new_household_data = {
                    'new_household_no': request.form.get('new_household_no', '').strip(),
                    'new_region': request.form.get('new_region', '').strip(),
                    'new_province': request.form.get('new_province', '').strip(),
                    'new_city_municipality': request.form.get('new_city_municipality', '').strip(),
                    'new_barangay': request.form.get('new_barangay', '').strip(),
                    'new_purok': request.form.get('new_purok', '').strip()
                }
                
                if not new_household_data['new_household_no']:
                    flash('Household number is required when creating new household.', 'warning')
                    return redirect(url_for('add_resident'))
                    
            elif household_select and household_select != 'none':
                try:
                    household_id = int(household_select)
                except (TypeError, ValueError):
                    household_id = None
            
            pending = PendingResident(
                last_name=last_name, first_name=first_name, middle_name=middle_name,
                gender=gender, age=age, purok=purok, voter_status=voter_status,
                senior_citizen=senior_citizen, date_of_birth=dob, place_of_birth=place_of_birth or None,
                civil_status=civil_status or None, citizenship=citizenship or None,
                occupation=occupation or None, household_id=household_id,
                submitted_by=current_user.id, status='pending',
                **new_household_data
            )
            db.session.add(pending)
            db.session.commit()
            flash('Resident submitted for approval. Admin will review shortly.', 'info')
            return redirect(url_for('pending_residents'))

    households = Household.query.order_by(Household.household_no).all()
    return render_template('add_resident.html', households=households)

@app.route('/pending_residents')
@login_required
def pending_residents():
    if current_user.role == 'admin':
        # Admins see all pending residents
        pending = PendingResident.query.filter_by(status='pending').order_by(PendingResident.submitted_at.desc()).all()
    else:
        # Regular users see only their submissions
        pending = PendingResident.query.filter_by(submitted_by=current_user.id).order_by(PendingResident.submitted_at.desc()).all()
    
    return render_template('pending_residents.html', pending_residents=pending)


# New route: Approve/Reject pending resident (admin only)
@app.route('/review_resident/<int:id>/<action>', methods=['POST'])
@admin_required
def review_resident(id, action):
    pending = PendingResident.query.get_or_404(id)
    
    if action == 'approve':
        # Create household if needed
        household_id = pending.household_id
        
        if pending.new_household_no:
            # Check if household already exists
            existing = Household.query.filter_by(household_no=pending.new_household_no).first()
            if existing:
                household_id = existing.id
            else:
                new_household = Household(
                    household_no=pending.new_household_no,
                    region=pending.new_region or None,
                    province=pending.new_province or None,
                    city_municipality=pending.new_city_municipality or None,
                    barangay=pending.new_barangay or None,
                    purok=pending.new_purok or None
                )
                db.session.add(new_household)
                db.session.flush()
                household_id = new_household.id
        
        # Create the resident
        resident = Resident(
            last_name=pending.last_name,
            first_name=pending.first_name,
            middle_name=pending.middle_name,
            gender=pending.gender,
            age=pending.age,
            purok=pending.purok,
            voter_status=pending.voter_status,
            senior_citizen=pending.senior_citizen,
            date_of_birth=pending.date_of_birth,
            place_of_birth=pending.place_of_birth,
            civil_status=pending.civil_status,
            citizenship=pending.citizenship,
            occupation=pending.occupation,
            household_id=household_id
        )
        db.session.add(resident)
        
        # Update pending record
        pending.status = 'approved'
        pending.reviewed_by = current_user.id
        pending.reviewed_at = datetime.datetime.utcnow()
        
        db.session.commit()
        flash('Resident approved and added to the system.', 'success')
        
    elif action == 'reject':
        pending.status = 'rejected'
        pending.reviewed_by = current_user.id
        pending.reviewed_at = datetime.datetime.utcnow()
        db.session.commit()
        flash('Resident submission rejected.', 'info')
    
    return redirect(url_for('pending_residents'))


@app.route('/edit_resident/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_resident(id):
    resident = Resident.query.get_or_404(id)
    
    if request.method == 'POST':
        resident.last_name = request.form.get('last_name', '').strip()
        resident.first_name = request.form.get('first_name', '').strip()
        resident.middle_name = request.form.get('middle_name', '').strip()
        resident.gender = request.form.get('gender')
        
        try:
            resident.age = int(request.form.get('age', 0))
        except ValueError:
            flash('Invalid age.', 'warning')
            return redirect(url_for('edit_resident', id=id))
            
        resident.purok = request.form.get('purok', '').strip()
        resident.voter_status = request.form.get('voter_status')
        resident.senior_citizen = request.form.get('senior_citizen')
        resident.place_of_birth = request.form.get('place_of_birth', '').strip() or None
        resident.civil_status = request.form.get('civil_status', '').strip() or None
        resident.citizenship = request.form.get('citizenship', '').strip() or None
        resident.occupation = request.form.get('occupation', '').strip() or None

        dob_str = request.form.get('date_of_birth', '').strip()
        if dob_str:
            try:
                resident.date_of_birth = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'warning')
                return redirect(url_for('edit_resident', id=id))
        else:
            resident.date_of_birth = None

        household_select = request.form.get('household_select')
        
        if household_select == 'new':
            new_household_no = request.form.get('new_household_no', '').strip()
            new_region = request.form.get('new_region', '').strip()
            new_province = request.form.get('new_province', '').strip()
            new_city_municipality = request.form.get('new_city_municipality', '').strip()
            new_barangay = request.form.get('new_barangay', '').strip()
            new_purok_hh = request.form.get('new_purok', '').strip()
            
            if not new_household_no:
                flash('Household number is required when creating new household.', 'warning')
                return redirect(url_for('edit_resident', id=id))
            
            existing_household = Household.query.filter_by(household_no=new_household_no).first()
            if existing_household:
                flash('Household number already exists.', 'warning')
                return redirect(url_for('edit_resident', id=id))
            
            new_household = Household(
                household_no=new_household_no,
                region=new_region or None,
                province=new_province or None,
                city_municipality=new_city_municipality or None,
                barangay=new_barangay or None,
                purok=new_purok_hh or None
            )
            db.session.add(new_household)
            db.session.flush()
            resident.household_id = new_household.id
            
        elif household_select and household_select != 'none':
            try:
                resident.household_id = int(household_select)
            except (TypeError, ValueError):
                resident.household_id = None
        else:
            resident.household_id = None

        db.session.commit()
        flash('Resident updated successfully.', 'success')
        return redirect(url_for('residents'))

    households = Household.query.order_by(Household.household_no).all()
    return render_template('edit_resident.html', resident=resident, households=households)

@app.route('/delete_resident/<int:id>', methods=['POST'])
@admin_required
def delete_resident(id):
    resident = Resident.query.get_or_404(id)
    db.session.delete(resident)
    db.session.commit()
    flash('Resident deleted.', 'success')
    return redirect(url_for('residents'))

@app.route('/resident_info/<int:id>')
@login_required
def resident_info(id):
    resident = Resident.query.get_or_404(id)
    return render_template('resident_info.html', resident=resident)


@app.route('/household_list')
@login_required
def household_list():
    households = Household.query.order_by(Household.household_no).all()
    return render_template('household_list.html', households=households)

@app.route('/household/<int:id>')
@login_required
def household_detail(id):
    household = Household.query.get_or_404(id)
    members = household.members.order_by(Resident.last_name, Resident.first_name).all()
    return render_template('household_detail.html', household=household, members=members)


@app.route('/system_settings', methods=['GET', 'POST'])
@admin_required
def system_settings():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            current_pwd = request.form.get('current_password')
            new_pwd = request.form.get('new_password')
            confirm_pwd = request.form.get('confirm_password')

            if not (current_pwd and new_pwd and confirm_pwd):
                flash('Fill all password fields.', 'warning')
                return redirect(url_for('system_settings'))

            if not bcrypt.check_password_hash(current_user.password, current_pwd):
                flash('Current password incorrect.', 'danger')
                return redirect(url_for('system_settings'))

            if new_pwd != confirm_pwd:
                flash('Passwords do not match.', 'warning')
                return redirect(url_for('system_settings'))

            if len(new_pwd) < 6:
                flash('Password must be 6+ characters.', 'warning')
                return redirect(url_for('system_settings'))

            current_user.password = bcrypt.generate_password_hash(new_pwd).decode('utf-8')
            db.session.commit()
            flash('Password changed.', 'success')
            return redirect(url_for('system_settings'))

        elif action == 'create_user':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', 'user')

            if not (username and password):
                flash('Username and password required.', 'warning')
                return redirect(url_for('system_settings'))

            if len(password) < 6:
                flash('Password must be 6+ characters.', 'warning')
                return redirect(url_for('system_settings'))

            if Admin.query.filter_by(username=username).first():
                flash('Username exists.', 'danger')
                return redirect(url_for('system_settings'))

            user = Admin(username=username, password=bcrypt.generate_password_hash(password).decode('utf-8'), role=role)
            db.session.add(user)
            db.session.commit()
            flash(f'User "{username}" created.', 'success')
            return redirect(url_for('system_settings'))

    all_users = Admin.query.all()
    return render_template('system_settings.html', all_users=all_users)

@app.route('/system_settings/delete_user/<int:id>', methods=['POST'])
@admin_required
def delete_user(id):
    if id == current_user.id:
        flash('Cannot delete own account.', 'warning')
        return redirect(url_for('system_settings'))

    user = Admin.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', 'success')
    return redirect(url_for('system_settings'))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)

