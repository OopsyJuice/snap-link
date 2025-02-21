import string
import random
from backend.app.models import URL

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        # Make sure code doesn't already exist
        if not URL.query.filter_by(short_code=code).first():
            return code