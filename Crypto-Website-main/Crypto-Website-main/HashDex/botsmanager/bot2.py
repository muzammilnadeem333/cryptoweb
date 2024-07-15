import datetime
import json
import logging
import os
import time
from stellar_sdk.exceptions import *
from stellar_sdk import Server, Keypair, Network, TransactionBuilder, Asset
from stellar_sdk.client.requests_client import RequestsClient
from stellar_sdk import *

client = RequestsClient(num_retries=0, post_timeout=16)
class MultiOperationBot:
    def __init__(self, pub_secret_key,use_dest,server_site,source_asset,destination_asset,uuid,mode,liquidity_pool_id):
        self.pub_secret_key = pub_secret_key
        self.destination_account_id = ''
        self.use_dest = use_dest
        self.BASE_FEE = 10000
        self.horizon_servers = ['https://horizon.stellar.org/', 'https://horizon.stellar.lobstr.co','https://horizon.publicnode.org/',
                                'https://h.fchain.io/', 'http://144.91.100.250:8000/', 'http://149.102.142.236:8000/']
        self.server_site = server_site
        self.server = Server(horizon_url=self.server_site, client=client)
        self.passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        self.source_asset = source_asset
        self.destination_asset = destination_asset
        self.keypair = Keypair.from_secret(self.pub_secret_key)
        self.name = "Bot"
        self.uuid = uuid
        self.mode = mode
        self.liquidity_pool_id = liquidity_pool_id


    def deposit_into_liquidity_pool(self, liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price):
        operation = LiquidityPoolDeposit(
                liquidity_pool_id=liquidity_pool_id,
                max_amount_a=str(max_amount_a),
                max_amount_b=str(max_amount_b),
                min_price=str(min_price),
                max_price=str(max_price),

        )
        
        #transaction.sign(self.keypair)
        #response = self.server.submit_transaction(transaction)
        return operation

    def withdraw_from_liquidity_pool(self, liquidity_pool_id, total_shares, min_amount_a, min_amount_b):
        # Create and submit the liquidity pool withdraw operation
        operation= LiquidityPoolWithdraw(
                liquidity_pool_id=liquidity_pool_id,
                amount=str(total_shares),
                min_amount_a=str(min_amount_a),
                min_amount_b=str(min_amount_b),
            )
        
        return operation
    

    def get_optimal_path_receive(self, dest_amount):

        paths = self.server.strict_receive_paths(
            destination_asset=self.destination_asset,
            destination_amount=dest_amount,
            source=[self.source_asset],
        ).call()
        first_path = paths['_embedded']['records'][0]
        optimal_path = []
        for item in first_path['path']:
            if item['asset_type'] == 'native':
                optimal_path.append(Asset.native())
            else:
                optimal_path.append(Asset(item['asset_code'], item['asset_issuer']))
        return optimal_path

    def get_optimal_path_send(self, send_amount):
        self.server = Server(horizon_url=self.server_site, client=client)


        paths = self.server.strict_send_paths(
            source_asset=self.source_asset,
            source_amount=send_amount,
            destination=[self.destination_asset],
        ).call()
        #('5th')
        first_path = paths['_embedded']['records'][0]
        optimal_path = []
        for item in first_path['path']:
            if item['asset_type'] == 'native':
                optimal_path.append(Asset.native())
            else:
                optimal_path.append(Asset(item['asset_code'], item['asset_issuer']))
        return optimal_path
    

    def path_payment_send_trade(self, send_amount, dest_min):
        if self.use_dest == 'true':
            self.destination_account_id = 'GCEVTSXRYPVZHH2Q3Y63JPS6UZXHKTOIN2QOSRDV3WI35ACQNUYO3LHD'
        else:
            self.destination_account_id = self.keypair.public_key
            #(self.destination_account_id)


        optimal_path = self.get_optimal_path_send(send_amount)
        account = self.server.load_account(account_id=self.keypair.public_key)

        operation = PathPaymentStrictSend(
                destination=self.destination_account_id,  # sending to ourselves
                send_asset=self.source_asset,
                send_amount=send_amount,
                dest_asset=self.destination_asset,
                dest_min=dest_min,
                path=optimal_path,
        )

        # Sign and submit the transaction
        #('[X]: Submitting Using Path Payment Strict Send : ')
        
        return operation
    
    def trade_path_payment_strict_receive(self, dest_amount, send_max_amount):

        if self.use_dest == 'true':
            self.destination_account_id = 'GCEVTSXRYPVZHH2Q3Y63JPS6UZXHKTOIN2QOSRDV3WI35ACQNUYO3LHD'
        else:
            self.destination_account_id = self.keypair.public_key

        optimal_path = self.get_optimal_path_receive(dest_amount)
        
        operation = PathPaymentStrictReceive(
                destination=self.destination_account_id,
                dest_asset=self.destination_asset,
                dest_amount=dest_amount,
                send_asset=self.source_asset,
                send_max=send_max_amount,  # Use the provided send_max_amount
                path=optimal_path,
            )
        #('Submitting using Strict Recieve')
        
        return operation
    
    def trade_path_payment_strict_receive_custom(self, custom_path, dest_amount, send_max_amount):

        if self.use_dest == 'true':
            self.destination_account_id = 'GCEVTSXRYPVZHH2Q3Y63JPS6UZXHKTOIN2QOSRDV3WI35ACQNUYO3LHD'
        else:
            self.destination_account_id = self.keypair.public_key

        optimal_path = custom_path

        operation = PathPaymentStrictReceive(
                destination=self.destination_account_id,
                dest_asset=self.destination_asset,
                dest_amount=dest_amount,
                send_asset=self.source_asset,
                send_max=send_max_amount,  # Use the provided send_max_amount
                path=optimal_path,
            )

        #('Submitting using Custom Strict Recieve')
        
        #("Successfully Submitted")
        return operation

    def path_payment_send_trade_custom(self, custom_path, send_amount, dest_min):
        if self.use_dest == 'true':
            self.destination_account_id = 'GCEVTSXRYPVZHH2Q3Y63JPS6UZXHKTOIN2QOSRDV3WI35ACQNUYO3LHD'
        else:
            self.destination_account_id = self.keypair.public_key

        optimal_path = custom_path

        operation = PathPaymentStrictSend(
                destination=self.destination_account_id,  # sending to ourselves
                send_asset=self.source_asset,
                send_amount=send_amount,
                dest_asset=self.destination_asset,
                dest_min=dest_min,
                path=optimal_path,
            )
        
        return operation
    
    def create_trade_transaction(self):
        source_account = self.server.load_account(account_id=self.keypair.public_key)
        transaction = TransactionBuilder(
            source_account=source_account,
            network_passphrase=self.passphrase,
            base_fee=self.BASE_FEE,
        )
        return transaction

    def append_operation(self, transaction, operation):
        return transaction.append_operation(operation)

    def submit_transaction(self, transaction):
        transaction = transaction.build()
        transaction.sign(self.keypair)
        response = self.server.submit_transaction(transaction)
        return response


def multi_try_trade_path_payment_send(new_bot, send_amount, dest_min, delay, liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price, total_shares, min_amount_a, min_amount_b):
    log_directory = 'logs'
    uuid = str(new_bot.uuid)
    # Ensure the log directory exists, creating it if necessary
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    file_name = f'{uuid}.log'
    log_filename = os.path.join(log_directory, file_name)
    if not os.path.isfile(log_filename):
        open(log_filename, 'w').close()
    # Use the UUID as the logger name consistently
    logger = logging.getLogger(uuid)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    while True:
        # Move the current_time assignment outside of the try block
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(int(delay))
        try:
            transaction = new_bot.create_trade_transaction()
            # Append operations to the transaction
            transaction = new_bot.append_operation(
                transaction, new_bot.deposit_into_liquidity_pool(liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price)
            )
            transaction = new_bot.append_operation(
                transaction, new_bot.path_payment_send_trade(send_amount, dest_min)
            )
            transaction = new_bot.append_operation(
                transaction, new_bot.withdraw_from_liquidity_pool(liquidity_pool_id, total_shares, min_amount_a, min_amount_b)
            )
            # Submit the transaction with all operations
            response = new_bot.submit_transaction(transaction)
            if response and response.get('successful') is True:
                logger.info(
                    f"Time: {current_time}, Amount: {send_amount}, Hash: {response['hash'][-5:]}, Status: Success, Error: None"
                )
            else:
                error_string = None
                if response:
                    error_string = json.dumps(response.get('extras', {}).get('result_codes', ''))
                logger.error(
                    f"Time: {current_time}, Amount: {send_amount}, Hash: None, Status: Failed, Error: {error_string}"
                )
            # Log the 'operations' field from the response
            if response and 'extras' in response and 'result_codes' in response['extras']:
                operations = response['extras']['result_codes'].get('operations', [])
                logger.info(f"Operations: {operations}")
        except Exception as e:
            error_string = str(e)
            if 'read timeout' in error_string:
                error_string = 'Timed out'
            logger.error(
                f"Time: {current_time}, Amount: {send_amount}, Hash: None, Status: Failed, Error: {error_string}"
            )
def multi_try_trade_path_payment_send_custom(new_bot,custom_path, send_amount, dest_min, delay, liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price, total_shares, min_amount_a, min_amount_b):
    log_directory = 'logs'
    uuid = str(new_bot.uuid)
    # Ensure the log directory exists, creating it if necessary
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    file_name = f'{uuid}.log'
    log_filename = os.path.join(log_directory, file_name)
    if not os.path.isfile(log_filename):
        open(log_filename, 'w').close()
    # Use the UUID as the logger name consistently
    logger = logging.getLogger(uuid)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    while True:
        # Move the current_time assignment outside of the try block
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(int(delay))
        try:
            transaction = new_bot.create_trade_transaction()
            # Append operations to the transaction
            transaction = new_bot.append_operation(
                transaction, new_bot.deposit_into_liquidity_pool(liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price)
            )
            transaction = new_bot.append_operation(
                transaction, new_bot.path_payment_send_trade_custom(custom_path=custom_path,send_amount=send_amount, dest_min=dest_min)
            )
            transaction = new_bot.append_operation(
                transaction, new_bot.withdraw_from_liquidity_pool(liquidity_pool_id, total_shares, min_amount_a, min_amount_b)
            )
            # Submit the transaction with all operations
            response = new_bot.submit_transaction(transaction)
            if response and response.get('successful') is True:
                logger.info(
                    f"Time: {current_time}, Amount: {send_amount}, Hash: {response['hash'][-5:]}, Status: Success, Error: None"
                )
            else:
                error_string = None
                if response:
                    error_string = json.dumps(response.get('extras', {}).get('result_codes', ''))
                logger.error(
                    f"Time: {current_time}, Amount: {send_amount}, Hash: None, Status: Failed, Error: {error_string}"
                )
            # Log the 'operations' field from the response
            if response and 'extras' in response and 'result_codes' in response['extras']:
                operations = response['extras']['result_codes'].get('operations', [])
                logger.info(f"Operations: {operations}")
        except Exception as e:
            error_string = str(e)
            if 'read timeout' in error_string:
                error_string = 'Timed out'
            logger.error(
                f"Time: {current_time}, Amount: {send_amount}, Hash: None, Status: Failed, Error: {error_string}"
            )
def multi_try_trade_path_payment_receive(new_bot,  dest_ammount, max_send_amount, delay, liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price, total_shares, min_amount_a, min_amount_b):
    log_directory = 'logs'
    uuid = str(new_bot.uuid)
    
    # Ensure the log directory exists, creating it if necessary
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    file_name = f'{uuid}.log'
    log_filename = os.path.join(log_directory, file_name)
    if not os.path.isfile(log_filename):
        open(log_filename, 'w').close()
    # Use the UUID as the logger name consistently
    logger = logging.getLogger(uuid)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    while True:
        # Move the current_time assignment outside of the try block
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(int(delay))
        try:
            transaction = new_bot.create_trade_transaction()
            # Append operations to the transaction
            transaction = new_bot.append_operation(
                transaction, new_bot.deposit_into_liquidity_pool(liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price)
            )
            transaction = new_bot.append_operation(
                transaction, new_bot.trade_path_payment_strict_receive(dest_amount=dest_ammount,send_max_amount= max_send_amount)
            )
            transaction = new_bot.append_operation(
                transaction, new_bot.withdraw_from_liquidity_pool(liquidity_pool_id, total_shares, min_amount_a, min_amount_b)
            )
            # Submit the transaction with all operations
            response = new_bot.submit_transaction(transaction)
            if response and response.get('successful') is True:
                logger.info(
                    f"Time: {current_time}, Amount: {dest_ammount}, Hash: {response['hash'][-5:]}, Status: Success, Error: None"
                )
            else:
                error_string = None
                if response:
                    error_string = json.dumps(response.get('extras', {}).get('result_codes', ''))
                logger.error(
                    f"Time: {current_time}, Amount: {dest_ammount}, Hash: None, Status: Failed, Error: {error_string}"
                )
            # Log the 'operations' field from the response
            if response and 'extras' in response and 'result_codes' in response['extras']:
                operations = response['extras']['result_codes'].get('operations', [])
                logger.info(f"Operations: {operations}")
        except Exception as e:
            error_string = str(e)
            if 'read timeout' in error_string:
                error_string = 'Timed out'
            logger.error(
                f"Time: {current_time}, Amount: {dest_ammount}, Hash: None, Status: Failed, Error: {error_string}"
            )
def multi_try_trade_path_payment_receive_custom(new_bot,custom_path,dest_amount, max_send_amount,  delay, liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price, total_shares, min_amount_a, min_amount_b):
    log_directory = 'logs'
    uuid = str(new_bot.uuid)
    # Ensure the log directory exists, creating it if necessary
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    file_name = f'{uuid}.log'
    log_filename = os.path.join(log_directory, file_name)
    if not os.path.isfile(log_filename):
        open(log_filename, 'w').close()
    # Use the UUID as the logger name consistently
    logger = logging.getLogger(uuid)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    while True:
        # Move the current_time assignment outside of the try block
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(int(delay))
        try:
            transaction = new_bot.create_trade_transaction()
            # Append operations to the transaction
            transaction = new_bot.append_operation(
                transaction, new_bot.deposit_into_liquidity_pool(liquidity_pool_id, max_amount_a, max_amount_b, min_price, max_price)
            )
            transaction = new_bot.append_operation(
                transaction, new_bot.trade_path_payment_strict_receive_custom(custom_path=custom_path,dest_amount=dest_amount, send_max_amount=max_send_amount)
            )
            transaction = new_bot.append_operation(
                transaction, new_bot.withdraw_from_liquidity_pool(liquidity_pool_id, total_shares, min_amount_a, min_amount_b)
            )
            # Submit the transaction with all operations
            response = new_bot.submit_transaction(transaction)
            if response and response.get('successful') is True:
                logger.info(
                    f"Time: {current_time}, Amount: {dest_amount}, Hash: {response['hash'][-5:]}, Status: Success, Error: None"
                )
            else:
                error_string = None
                if response:
                    error_string = json.dumps(response.get('extras', {}).get('result_codes', ''))
                logger.error(
                    f"Time: {current_time}, Amount: {dest_amount}, Hash: None, Status: Failed, Error: {error_string}"
                )
            # Log the 'operations' field from the response
            if response and 'extras' in response and 'result_codes' in response['extras']:
                operations = response['extras']['result_codes'].get('operations', [])
                logger.info(f"Operations: {operations}")
        except Exception as e:
            error_string = str(e)
            if 'read timeout' in error_string:
                error_string = 'Timed out'
            logger.error(
                f"Time: {current_time}, Amount: {dest_amount}, Hash: None, Status: Failed, Error: {error_string}"
            )