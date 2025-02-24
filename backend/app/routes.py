from flask import Blueprint, jsonify, request, redirect, render_template, current_app, url_for, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required, current_user
from backend.app.models import URL, User, ClickEvent, db
from backend.app.utils import generate_short_code
import validators
from datetime import datetime
import logging

bp = Blueprint('main', __name__)

# Web Routes
@bp.route('/')
@login_required
def dashboard():
    urls = URL.query.filter_by(user_id=current_user.id)\
              .order_by(URL.created_at.desc()).all()
    return render_template('dashboard.html', urls=urls)

@bp.route('/urls/<short_code>/stats')
@login_required
def url_stats(short_code):
    url = URL.query.filter_by(
        short_code=short_code,
        user_id=current_user.id
    ).first_or_404()
    
    clicks = ClickEvent.query.filter_by(url_id=url.id)\
              .order_by(ClickEvent.timestamp.desc()).all()
    return render_template('stats.html', url=url, clicks=clicks)

# API Routes
@bp.route('/api/shorten', methods=['POST'])
@login_required
def shorten_url():
    url = request.json.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    short_code = generate_short_code()
    new_url = URL(
        original_url=url,
        short_code=short_code,
        user_id=current_user.id
    )
    
    db.session.add(new_url)
    db.session.commit()
    
    return jsonify({
        'short_code': short_code,
        'domain': request.host
    })

@bp.route('/<short_code>')
def redirect_to_url(short_code):
    url = URL.query.filter_by(short_code=short_code, is_active=True).first()
    
    if not url:
        abort(404)
    
    url.clicks += 1
    db.session.commit()
    
    return redirect(url.original_url)

@bp.route('/api/urls')
@jwt_required()
def get_user_urls():
    current_user_id = get_jwt_identity()
    urls = URL.query.filter_by(user_id=current_user_id)\
              .order_by(URL.created_at.desc()).all()
    return jsonify([url.to_dict() for url in urls])

@bp.route('/api/urls/<short_code>')
@jwt_required()
def get_url_stats_api(short_code):
    current_user_id = get_jwt_identity()
    url = URL.query.filter_by(
        short_code=short_code,
        user_id=current_user_id
    ).first_or_404()
    
    clicks = ClickEvent.query.filter_by(url_id=url.id)\
              .order_by(ClickEvent.timestamp.desc()).all()
    
    return jsonify({
        **url.to_dict(),
        'clicks_detail': [click.to_dict() for click in clicks]
    })

@bp.route('/api/urls/<short_code>', methods=['DELETE'])
@jwt_required()
def delete_url(short_code):
    current_user_id = get_jwt_identity()
    url = URL.query.filter_by(
        short_code=short_code,
        user_id=current_user_id
    ).first_or_404()
    
    db.session.delete(url)
    db.session.commit()
    
    return jsonify({'message': 'URL deleted successfully'}), 200

@bp.route('/api/urls/<short_code>', methods=['PUT'])
@jwt_required()
def update_url(short_code):
    current_user_id = get_jwt_identity()
    url = URL.query.filter_by(
        short_code=short_code,
        user_id=current_user_id
    ).first_or_404()
    
    data = request.get_json()
    
    if 'is_active' in data:
        url.is_active = data['is_active']
    
    db.session.commit()
    return jsonify(url.to_dict())

@bp.route('/api/urls/<short_code>/geostats')
@login_required
def get_geolocation_stats(short_code):
    url = URL.query.filter_by(short_code=short_code, user_id=current_user.id).first()
    
    if not url:
        return jsonify({'error': 'URL not found'}), 404
    
    # Aggregate geolocation data
    geo_stats = db.session.query(
        ClickEvent.country_name, 
        db.func.count(ClickEvent.id).label('click_count')
    ).filter(
        ClickEvent.url_id == url.id
    ).group_by(
        ClickEvent.country_name
    ).order_by(
        db.desc('click_count')
    ).all()
    
    return jsonify({
        'geo_stats': [
            {'country': country, 'clicks': clicks} 
            for country, clicks in geo_stats
        ]
    })

@bp.route('/api/urls/<short_code>/clicks')
@login_required
def get_url_clicks(short_code):
    url = URL.query.filter_by(short_code=short_code, user_id=current_user.id).first()
    if not url:
        return jsonify({'error': 'URL not found'}), 404
        
    clicks = ClickEvent.query.filter_by(url_id=url.id).order_by(ClickEvent.timestamp.desc()).all()
    return jsonify({
        'clicks': [click.to_dict() for click in clicks]
    })

@bp.route('/api/urls/<short_code>/analytics')
@login_required
def get_url_analytics(short_code):
    url = URL.query.filter_by(short_code=short_code, user_id=current_user.id).first()
    if not url:
        return jsonify({'error': 'URL not found'}), 404

    # Get all clicks for this URL
    clicks = ClickEvent.query.filter_by(url_id=url.id).all()
    
    # Prepare analytics data
    analytics = {
        'total_clicks': len(clicks),
        'timeline_data': {},
        'devices': {},
        'browsers': {},
        'referrers': {},
        'peak_hours': [0] * 24
    }
    
    for click in clicks:
        # Timeline data
        date = click.timestamp.strftime('%Y-%m-%d')
        analytics['timeline_data'][date] = analytics['timeline_data'].get(date, 0) + 1
        
        # Device detection
        ua_string = click.user_agent
        if 'Mobile' in ua_string:
            device = 'Mobile'
        elif 'Tablet' in ua_string:
            device = 'Tablet'
        else:
            device = 'Desktop'
        analytics['devices'][device] = analytics['devices'].get(device, 0) + 1
        
        # Browser detection
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
        browser = next((b for b in browsers if b in ua_string), 'Other')
        analytics['browsers'][browser] = analytics['browsers'].get(browser, 0) + 1
        
        # Referrer tracking
        referrer = click.referrer if click.referrer else 'Direct'
        referrer = referrer.split('/')[2] if '://' in referrer else 'Direct'
        analytics['referrers'][referrer] = analytics['referrers'].get(referrer, 0) + 1
        
        # Peak hours
        hour = click.timestamp.hour
        analytics['peak_hours'][hour] += 1
    
    return jsonify(analytics)

@bp.route('/api/domains', methods=['POST'])
@login_required
def add_domain():
    domain = request.json.get('domain')
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
        
    # Generate verification token
    verification_token = token_hex(32)
    
    custom_domain = CustomDomain(
        user_id=current_user.id,
        domain=domain,
        verification_token=verification_token
    )
    
    db.session.add(custom_domain)
    db.session.commit()
    
    return jsonify({
        'domain': domain,
        'verification_token': verification_token,
        'instructions': {
            'txt_record': f'snaplink-verify={verification_token}',
            'steps': [
                'Add a TXT record to your domain DNS settings',
                'Set the host to @',
                'Set the value to the verification token',
                'Wait for DNS propagation (may take up to 24 hours)',
                'Click verify to complete the process'
            ]
        }
    })

@bp.route('/api/domains/<int:domain_id>/verify', methods=['POST'])
@login_required
def verify_domain(domain_id):
    domain = CustomDomain.query.get_or_404(domain_id)
    
    if domain.user_id != current_user.id:
        abort(403)
    
    try:
        # Check TXT records
        answers = dns.resolver.resolve(domain.domain, 'TXT')
        for rdata in answers:
            for txt_string in rdata.strings:
                if txt_string.decode() == f'snaplink-verify={domain.verification_token}':
                    domain.dns_verified = True
                    domain.verified = True
                    domain.last_dns_check = datetime.utcnow()
                    db.session.commit()
                    return jsonify({'status': 'verified'})
    except Exception as e:
        logging.error(f"DNS verification failed: {e}")
    
    return jsonify({'error': 'Verification failed. Please check DNS settings and try again.'}), 400