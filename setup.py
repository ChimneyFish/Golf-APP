from setuptools import setup, find_packages

setup(
    name='ai caddy',
    version='1.0',
    description='A Range finder, scorekeeper,shot distance calculator, next club suggestion engine',
    author='Jim',
    author_email='ChimneyFish69@google.com',
    url='https://github.com/ChimneyFish/Golf-APP',  # Replace with your project URL
    packages=find_packages(),
    install_requires=[
        'folium',
        'geopy',
        'requests',
        'pynmea2',
        'PyQt5',
        'gpsd-py3',
        'pyserial'
    ],
    entry_points={
        'console_scripts': [
            'Golf-APP=main:main',
        ],
    },
)
