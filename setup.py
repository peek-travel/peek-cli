from setuptools import setup, find_packages

setup(
    name='peek-cli',
    version='0.1',
    py_modules=['cli'],
    install_requires=[
        'click',
        'requests',
        'python-dotenv',
    ],
    entry_points={
        'console_scripts': [
            'peek=cli:cli',
        ],
    },
)