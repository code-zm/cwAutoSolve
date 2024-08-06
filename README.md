# Code Wars Auto Solver
A Python script to automate solving coding challenges on CodeWars using Selenium and OpenAI's API.

## Prerequisites
- Python 3.x
- Git
- Chrome Browser
- ChromeDriver (Compatible with your Chrome version)
- OpenAI API Key

## Installation

1. **Clone the Repository**

```sh
git clone https://github.com/zmain4/cwAutoSolver.git
cd cwAutoSolver
```

2. **Create and Activate a Virtual Environment (optional but recommended)**
```sh
python3 -m venv venv
source venv/bin/activate # On Windows, use 'venv\Scripts\activate'
```

3. **Install the Requirements**
```sh
pip install -r requirements.txt
```

## Configuration
Before running the script, you need to set up the config.txt file with your personal details and API key.

1. **Update the 'config.txt' File**

*Example 'config.txt' file:*
```plaintext
API_KEY="sk-1234567890abcdef1234567890abcdef"
EMAIL="your.email@example.com"
PASSWORD="your_codewars_password"
CHROMEDRIVER_PATH="/path/to/chromedriver"
```

## Running the Script
Once you have installed the dependencies and set up the configuration file, you can run the script:
```sh
python codewarsDriver.py
```
