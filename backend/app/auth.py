from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_login import login_user, logout_user, login_required, current_user
from backend.app.models import User, db
from datetime import timedelta

bp = Blueprint('auth', __name__)

# Web routes
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@bp.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([email, password, confirm_password]):
        flash('All fields are required', 'error')
        return redirect(url_for('auth.login'))
        
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('auth.login'))
        
    if User.query.filter_by(email=email).first():
        flash('Email already registered', 'error')
        return redirect(url_for('auth.login'))
    
    user = User(email=email)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    flash('Registration successful!', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# API routes
@bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )
        return jsonify({
            'access_token': access_token,
            'user': {
                'email': user.email,
                'tier': user.tier
            }
        })
    
    return jsonify({'error': 'Invalid email or password'}), 401

@bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(email=data['email'])
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(days=7)
    )
    
    return jsonify({
        'message': 'User created successfully',
        'access_token': access_token
    }), 201

@bp.route('/api/me', methods=['GET'])
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'email': user.email,
        'tier': user.tier,
        'created_at': user.created_at.isoformat()
    })