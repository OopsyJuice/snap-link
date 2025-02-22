from flask import Blueprint, jsonify, request, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.models import URL, User, db
from backend.app.utils import generate_short_code
import validators

bp = Blueprint('main', __name__)

@bp.route('/api/shorten', methods=['POST'])
@jwt_required()  # This makes the endpoint require authentication
def shorten_url():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    long_url = data.get('url')

    if not long_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    if not validators.url(long_url):
        return jsonify({'error': 'Invalid URL format'}), 400

    # Check if URL already exists for this user
    existing_url = URL.query.filter_by(
        original_url=long_url,
        user_id=current_user_id
    ).first()
    
    if existing_url:
        return jsonify(existing_url.to_dict()), 200

    # Create new shortened URL
    short_code = generate_short_code()
    new_url = URL(
        original_url=long_url,
        short_code=short_code,
        user_id=current_user_id
    )
    
    db.session.add(new_url)
    db.session.commit()

    return jsonify(new_url.to_dict()), 201

@bp.route('/<short_code>')
def redirect_to_url(short_code):
    url_record = URL.query.filter_by(short_code=short_code).first_or_404()
    url_record.clicks += 1
    db.session.commit()
    return redirect(url_record.original_url)

@bp.route('/api/urls')
@jwt_required()
def get_user_urls():
    current_user_id = get_jwt_identity()
    urls = URL.query.filter_by(user_id=current_user_id).order_by(URL.created_at.desc()).all()
    return jsonify([url.to_dict() for url in urls])

@bp.route('/api/stats/<short_code>')
@jwt_required()
def get_url_stats(short_code):
    current_user_id = get_jwt_identity()
    url_record = URL.query.filter_by(
        short_code=short_code,
        user_id=current_user_id
    ).first_or_404()
    return jsonify(url_record.to_dict())