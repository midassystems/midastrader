from setuptools import setup, find_packages

# Read requirements.txt and use its contents as the install_requires list
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='midas_python',  # Your package name
    version='0.1.0',  # Version number
    author='Anthony Baxter', 
    author_email='anthony_baxter819@gmail.com',  
    description="A comprehensive suite designed for advanced financial analysis and trading, this package combines a robust management tool for Django Rest Framework (DRF) API backends with powerful financial data retrieval capabilities, ensuring efficient integration and manipulation of financial datasets. It includes an event-driven backtesting and live trading library tailored for compatibility with the Interactive Brokers API, supporting the development, testing, and deployment of complex trading strategies with real-time data and execution. Additionally, the suite features an efficient, vectorized backtesting library optimized for quantitative analysis, providing advanced tools for high-speed, precise evaluation of trading strategies. This all-in-one toolkit is ideal for financial analysts, quantitative researchers, and traders seeking a reliable, integrated platform for comprehensive financial management and strategy development.", # Short description
    long_description=open('README.md').read(),  # Detailed description from README.md
    long_description_content_type='text/markdown',  # Specifies the long desc is in Markdown
    url='https://github.com/anthonyb8/MidasPython.git',  # Project home page or repository URL
    packages=find_packages(),  # Automatically discover all packages and subpackages
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Example classifier, adjust as needed
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',  # Minimum Python version requirement
)