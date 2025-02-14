from setuptools import setup

setup(
    name="peek-cli",
    version="0.2",
    py_modules=["cli"],
    install_requires=[
        "click",
        "requests",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "peek=cli:cli",
        ],
    },
)
