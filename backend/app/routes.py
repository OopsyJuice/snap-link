from flask import Blueprint, jsonify, request, redirect
from backend.app.models import URL, db
from backend.app.utils import generate_short_code
import validators

bp = Blueprint('main', __name__)

@bp.route('/api/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    long_url = data.get('url')

    if not long_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    if not validators.url(long_url):
        return jsonify({'error': 'Invalid URL'}), 400

    # Check if URL already exists
    existing_url = URL.query.filter_by(original_url=long_url).first()
    if existing_url:
        return jsonify(existing_url.to_dict()), 200

    # Create new shortened URL
    short_code = generate_short_code()
    new_url = URL(original_url=long_url, short_code=short_code)
    
    db.session.add(new_url)
    db.session.commit()

    return jsonify(new_url.to_dict()), 201

@bp.route('/<short_code>')
def redirect_to_url(short_code):
    url_record = URL.query.filter_by(short_code=short_code).first_or_404()
    url_record.clicks += 1
    db.session.commit()
    return redirect(url_record.original_url)

@bp.route('/api/stats/<short_code>')
def get_url_stats(short_code):
    url_record = URL.query.filter_by(short_code=short_code).first_or_404()
    return jsonify(url_record.to_dict())