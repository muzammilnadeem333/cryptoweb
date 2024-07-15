# HASHDex

HASHDex is a specialized client tailored for the Stellar network exchange, providing a unique approach to trading and managing assets. Unlike conventional exchanges, HASHDex is designed for personalized usage, where users are exclusively created from the backend, ensuring a controlled and secure environment.

## Features

### Personalized Usage

- Users are created from the backend, ensuring a secure and controlled environment. Access is granted only through authorized channels.

### Multi-Account Monitoring

- Monitor the status of multiple accounts simultaneously, offering users a comprehensive overview of their assets and transactions.

### Multi-Bot Operations

- Run multiple bots simultaneously, each with distinct operations such as strict send or receive.
- Customize transaction paths by specifying custom paths or selecting from a curated list.
- Utilize multiple Horizon servers to prevent rate limiting and ensure seamless transaction processing.
- Define custom destination accounts for transactions, providing flexibility and control.

### Automated Bot Operations

- Automate bot operations to optimize liquidity pool deposits, transactions, and withdrawals for maximum profitability.
- Easily manage bots with start, stop, and delete functionalities, enhancing user convenience.
- View detailed transaction logs for each bot to track performance and troubleshoot issues effectively.
- Clone bots effortlessly to scale operations and diversify strategies with a single click.

### Liquidity Pools

- Access real-time information about liquidity pools, including vital metrics like depth and spread, refreshed every 5 seconds.
- Create, deposit, and withdraw from liquidity pools seamlessly within the HASHDex interface.
- Establish trust and calculate liquidity pool IDs accurately, with every operation related to liquidity pools fully implemented.

### Buy/Sell Offers Management

- Create and manage buy and sell offers directly on the market, empowering users to execute trades efficiently.

### Bulk Converter Functionality

- Automate the conversion of all claimable balances in your account to a specific asset, streamlining asset management tasks.

### Multiple Transaction Bots

- Configure and deploy multiple transaction bots, each tailored to execute specific strategies or operations.
- Execute complex transactions involving multiple assets or paths with ease, utilizing the flexibility and power of HASHDex.
- Monitor and manage multiple transaction bots simultaneously, allowing users to diversify their trading activities and optimize returns.

### Theme
- The Web is based on  catpuchin theme and foucused on simplicity.
- Login page
  
  ![LoginPage](https://i.imgur.com/cgGsZkP.png)

- Dashboard

  ![](https://i.imgur.com/E2axtoE.png)

- Run Bots

  ![](https://i.imgur.com/2v6ktVR.png)

  


## Getting Started

### Prerequisites

- Python 3 installed on your system.
- Django and required dependencies installed.
- Or You can install requirements through the `requirments.txt` file

### Installation

1. Clone the repository:
    
    `https://github.com/hasharmujahid/HashDex.git`
    
2. Install dependencies:
    
    `pip install -r requirments.txt`
    OR
    `pip3 install stellar_sdk aiohttp django --break-system-packages`
    
3. Apply migrations:
	```bash
	python3 manage.py makemigrations 
	python3 manage.py migrate 
	python3 manage.py makemigrations botsmanager 
	python3 manage.py migrate botsmanager
	```

### Usage

1. Run the development server:
    
    `python3 manage.py runserver`
    
2. Access HASHDex through your preferred web browser at `http://localhost:8000`.

### Deployment

- To deploy using NGINX and WSGI server, configure your NGINX server to serve your Django application and use a WSGI server like Gunicorn or uWSGI for application serving.
