from flask import Blueprint, jsonify, request, redirect, render_template, current_app, url_for, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required, current_user
from backend.app.models import URL, User, ClickEvent, db, CustomDomain
from backend.app.utils import generate_short_code
import validators
from datetime import datetime
import logging
import secrets
import dns.resolver

bp = Blueprint('main', __name__)

# Web Routes
@bp.route('/')
@login_required
def dashboard():
    urls = URL.query.filter_by(user_id=current_user.id)\
              .order_by(URL.created_at.desc()).all()
    verified_domains = CustomDomain.query.filter_by(
        user_id=current_user.id,
        verified=True
    ).all()
    return render_template('dashboard.html', urls=urls, verified_domains=verified_domains)

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
    data = request.get_json()
    url = data.get('url')
    domain_id = data.get('domain_id')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    if not validators.url(url):
        return jsonify({'error': 'Invalid URL'}), 400
    
    # If domain_id is provided, verify it belongs to the user and is verified
    custom_domain = None
    if domain_id:
        custom_domain = CustomDomain.query.filter_by(
            id=domain_id,
            user_id=current_user.id,
            verified=True
        ).first()
        if not custom_domain:
            return jsonify({'error': 'Invalid or unverified domain'}), 400
    
    short_code = generate_short_code()
    
    new_url = URL(
        original_url=url,
        short_code=short_code,
        user_id=current_user.id,
        domain_id=custom_domain.id if custom_domain else None
    )
    
    db.session.add(new_url)
    db.session.commit()
    
    domain = custom_domain.domain if custom_domain else request.host
    
    return jsonify({
        'short_code': short_code,
        'domain': domain
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

@bp.route('/api/domains', methods=['GET', 'POST'])
@login_required
def manage_domains():
    if request.method == 'GET':
        domains = CustomDomain.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': domain.id,
            'domain': domain.domain,
            'verified': domain.verified,
            'created_at': domain.created_at.isoformat(),
            'verification_token': domain.verification_token
        } for domain in domains])
    
    elif request.method == 'POST':
        domain = request.json.get('domain')
        
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400
            
        # Remove http:// or https:// if present
        domain = domain.replace('http://', '').replace('https://', '')
        
        # Remove trailing slash if present
        domain = domain.rstrip('/')
        
        # Check if domain already exists
        if CustomDomain.query.filter_by(domain=domain).first():
            return jsonify({'error': 'Domain already exists'}), 400
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        
        new_domain = CustomDomain(
            domain=domain,
            user_id=current_user.id,
            verification_token=verification_token
        )
        
        db.session.add(new_domain)
        db.session.commit()
        
        return jsonify({
            'id': new_domain.id,
            'domain': new_domain.domain,
            'verified': new_domain.verified,
            'created_at': new_domain.created_at.isoformat(),
            'verification_token': new_domain.verification_token
        }), 201

@bp.route('/api/domains/<int:domain_id>/verify', methods=['POST'])
@login_required
def verify_domain(domain_id):
    domain = CustomDomain.query.filter_by(
        id=domain_id, 
        user_id=current_user.id
    ).first_or_404()
    
    try:
        # Query TXT records
        answers = dns.resolver.resolve(domain.domain, 'TXT')
        
        # Check if our verification token exists in any of the TXT records
        expected_record = f'snaplink-verify={domain.verification_token}'
        
        for rdata in answers:
            for txt_string in rdata.strings:
                if txt_string.decode() == expected_record:
                    domain.verified = True
                    db.session.commit()
                    return jsonify({'status': 'verified'})
        
        return jsonify({
            'error': 'Verification record not found. Please check that you added the TXT record correctly.'
        }), 400
        
    except dns.resolver.NXDOMAIN:
        return jsonify({'error': 'Domain does not exist'}), 400
    except dns.resolver.NoAnswer:
        return jsonify({'error': 'No TXT records found'}), 400
    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 400

@bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html')