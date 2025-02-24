from setuptools import setup, find_packages

setup(
    name="snap-link",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'Flask==3.0.2',
        'Flask-SQLAlchemy==3.1.1',
        'python-dotenv==1.0.1',
        'validators==0.22.0',
        'flask-cors==4.0.0',
        'Flask-JWT-Extended==4.6.0',
        'Flask-Login==0.6.3',
        'email-validator==2.1.1',
        'Flask-Migrate==4.0.5'
    ]
) 