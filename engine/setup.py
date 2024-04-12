from setuptools import setup, find_packages

# Read requirements.txt and use its contents as the install_requires list
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='midas',  # Your package name
    version='0.1.0',  # Version number
    author='Anthony Baxter', 
    author_email='anthony_baxter819@gmail.com',  
    description='A comprehensive, event-driven backtesting and live trading library tailored for use with the Interactive Brokers API (ibapi). Engineered for traders and quantitative analysts, this package facilitates the development, testing, and deployment of complex trading strategies with an emphasis on real-time data and execution.', # Short description
    long_description=open('README.md').read(),  # Detailed description from README.md
    long_description_content_type='text/markdown',  # Specifies the long desc is in Markdown
    url='https://github.com/anthonyb8/midas-python.git',  # Project home page or repository URL
    packages=find_packages(),  # Automatically discover all packages and subpackages
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Example classifier, adjust as needed
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',  # Minimum Python version requirement
)