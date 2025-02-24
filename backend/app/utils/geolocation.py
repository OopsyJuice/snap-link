import requests
import logging

def get_geolocation(ip_address):
    logging.info(f"Attempting to get geolocation for IP: {ip_address}")
    try:
        # Skip localhost IPs
        if ip_address in ['127.0.0.1', 'localhost', '::1']:
            logging.info("Local IP detected, skipping geolocation")
            return {
                'country_code': 'Unknown',
                'country_name': 'Unknown',
                'city': 'Unknown',
                'latitude': None,
                'longitude': None
            }

        response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
        logging.info(f"Geolocation response: {response}")
        
        if response.get('error'):
            logging.error(f"Geolocation error: {response.get('error')}")
            return {
                'country_code': 'Unknown',
                'country_name': 'Unknown',
                'city': 'Unknown',
                'latitude': None,
                'longitude': None
            }
        
        return {
            'country_code': response.get('country_code', 'Unknown'),
            'country_name': response.get('country_name', 'Unknown'),
            'city': response.get('city', 'Unknown'),
            'latitude': response.get('latitude'),
            'longitude': response.get('longitude')
        }
    except Exception as e:
        logging.error(f"Geolocation lookup failed: {e}")
        return {
            'country_code': 'Unknown',
            'country_name': 'Unknown',
            'city': 'Unknown',
            'latitude': None,
            'longitude': None
        } 