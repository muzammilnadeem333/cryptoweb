import asyncio
from django.contrib.auth.decorators import login_required
import datetime
from datetime import datetime
import aiohttp
import multiprocessing
from django.http import JsonResponse
from django.shortcuts import redirect, render
from stellar_sdk import Keypair
import asyncio
import requests
from stellar_sdk import (
    PathPaymentStrictSend,
    Server,
    Keypair,
    TransactionBuilder,
    Asset,
    Network,
    ClaimClaimableBalance,
    
)

global horizon_url
horizon_url = 'https://horizon.stellar.org'


def format_datetime(timestamp):
    dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%H:%M:%S, %d %b %Y')


async def get_account_data(session, secret_key):
    global horizon_url
    secret_key = str(secret_key)
    if secret_key.startswith('S') and len(secret_key) >= 56:
        keypair = Keypair.from_secret(secret_key)
        account_public_key = keypair.public_key
    else:
        return {
            'account_public_key': 'Wrong Secret Key',
            'account_secret_key': 'Wrong Secret Key',
            'payments': 'Wrong Secret Key',
            'balances': 'Wrong Secret Key',
            'claimable_balances': 'Wrong Secret Key'
        }

    async with session.get(f'{horizon_url}/accounts/{account_public_key}/payments?order=desc&limit=7') as response:
        payments = await response.json()
        payment_info = []
        embedded_records = payments.get('_embedded', {}).get('records', [])
        for payment in embedded_records:
            destination_asset_amount = payment.get('amount', 'N/A')
            source_asset_amount = payment.get('source_amount', 'N/A')

            destination_asset_type = payment.get('asset_type')
            source_asset_type = payment.get('source_asset_type')

            destination_asset_code = 'N/A'  # Initialize with default value
            source_asset_code = 'N/A'  # Initialize with default value

            if destination_asset_type == 'native':
                destination_asset_code = 'XLM'
            elif str(destination_asset_type).startswith('credit_alphanum'):
                destination_asset_code = payment.get('asset_code')

            if source_asset_type == 'native':
                source_asset_code = 'XLM'
            elif str(source_asset_type).startswith('credit_alphanum'):
                source_asset_code = payment.get('source_asset_code')

            payment_data = {
                'id': payment.get('id', 'N/A'),
                'amount': destination_asset_amount,
                'source_asset_code': source_asset_code,
                'source_asset_amount': source_asset_amount,
                'destination_asset_code': destination_asset_code,
                'destination_asset_amount': destination_asset_amount,
                'created_at': format_datetime(payment.get('created_at', 'N/A'))
            }
            payment_info.append(payment_data)

    async with session.get(f'{horizon_url}/accounts/{account_public_key}') as response:
        account_details = await response.json()
        balance_info = []
        if 'balances' in account_details:
            balances = account_details['balances']
            for balance in balances:
                asset_type = balance.get('asset_type')
                if asset_type == 'native':
                    asset_code = 'XLM'
                elif asset_type == 'credit_alphanum4':
                    asset_code = balance.get('asset_code')
                else:
                    asset_code = 'N/A'
                if asset_code != 'N/A':
                    balance_data = {
                        'asset': asset_code,
                        'balance': balance['balance']
                    }
                    balance_info.append(balance_data)
                else:
                    pass
        else:
            balance_info.append({'asset': 'N/A', 'balance': 'N/A'})

    async with session.get(f'{horizon_url}/claimable_balances?claimant={account_public_key}&order=desc') as response:
        claimable_balances = await response.json()
        claimable_info = []
        for claimable_balance in claimable_balances['_embedded']['records']:
            asset = claimable_balance['asset']
            asset_code, issuer = asset.split(':')
            if asset_code is None:
                asset_code = 'XLM'
            claimable_data = {
                'amount': claimable_balance['amount'],
                'asset_code': asset_code,
                'issuer': issuer
            }
            claimable_info.append(claimable_data)
    return {
        'account_public_key': keypair.public_key,
        'account_secret_key': secret_key,
        'payments': payment_info,
        'balances': balance_info,
        'claimable_balances': claimable_info

    }


async def check(request):
    if request.method == 'POST':
        secret_keys = request.POST.get('accounts')  # SEcrets
        secret_keys = secret_keys.splitlines()
        print(secret_keys) # REMOVE THIS
        async with aiohttp.ClientSession() as SESSION:
            tasks = [get_account_data(SESSION, key) for key in secret_keys]
            results = await asyncio.gather(*tasks)
            return render(request, 'account_results.html', {'results': results})
    elif request.method == 'GET':
        return render(request, 'checkaccounts.html')


def get_claimable_balances(secret_key):
    horizon_url = "https://horizon.stellar.org"  
    secret_key = str(secret_key)

    if secret_key.startswith('S'):
        keypair = Keypair.from_secret(secret_key)
        account_public_key = keypair.public_key
    else:
        return {
            'account_public_key': 'Wrong Secret Key',
            'claimable_balances': 'Wrong Secret Key'
        }

    # Fetch claimable balances
    claimable_balances_url = f'{horizon_url}/claimable_balances?claimant={account_public_key}&limit=200&order=desc'
    claimable_balances_response = requests.get(claimable_balances_url)
    claimable_balances_data = claimable_balances_response.json().get('_embedded', {}).get('records', [])

    claimable_info = []
    for claimable_balance in claimable_balances_data:
        asset = claimable_balance['asset']
        asset_code, issuer = asset.split(':')
        claimable_data = {
            'id': claimable_balance['id'],  # ID is important
            'amount': claimable_balance['amount'],
            'asset_code': asset_code,
            'issuer': issuer
        }
        claimable_info.append(claimable_data)

    return {
        'account_public_key': keypair.public_key,
        'claimable_balances': claimable_info
    }


def claim_claimable_balance(server, source_keypair, balance_id):
    try:
        claim_op = ClaimClaimableBalance(balance_id)
        transaction = TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
        )\
            .append_operation(claim_op)\
            .build()

        transaction.sign(source_keypair)
        server.submit_transaction(transaction)

        return True
    except Exception as e:
        print(f"Error claiming balance: {str(e)}")
        return False

def get_optimal_path(server, source_asset, dest_asset, send_amount):    
    try:
        paths = server.strict_send_paths(
            source_asset=source_asset,
            source_amount=send_amount,
            destination=[dest_asset],
        ).call()
        
        if "_embedded" in paths and "records" in paths["_embedded"]:
            first_path = paths["_embedded"]["records"][0]
            optimal_path = []
            for item in first_path["path"]:
                if item["asset_type"] == "native":
                    optimal_path.append(Asset.native())
                else:
                    optimal_path.append(Asset(item["asset_code"], item["asset_issuer"]))
            return optimal_path
        else:
            return []

    except Exception as e:
        print(e)
        return []

def process_claimable_balances(secret_key, destination_asset_code, destination_asset_issuer):
    horizon_url = "https://horizon.stellar.org"  # URL
    server = Server(horizon_url)

    account_data = get_claimable_balances(secret_key)
    source_keypair = Keypair.from_secret(secret_key)

    global source_account
    source_account = server.load_account(source_keypair.public_key)
    public_key = source_keypair.public_key

    claimable_balances = account_data["claimable_balances"]

    if not claimable_balances:
        return "No claimable balances to process."

    try:
        for claimable_balance in claimable_balances:
            asset_code = claimable_balance["asset_code"]
            issuer = claimable_balance["issuer"]
            claimable_balance_id = claimable_balance["id"]
            claimed_balance_amount = claimable_balance["amount"]

            if str(destination_asset_code).lower() != "xlm":
                destination_asset = Asset(destination_asset_code, destination_asset_issuer)
            else:
                destination_asset = Asset.native()

            asset = Asset(asset_code, issuer)

            # optimal path fininging
            optimal_path = get_optimal_path(server, asset, destination_asset, str(claimed_balance_amount))
            
            if not optimal_path:
                print(f"No optimal path found for {asset_code}:{issuer} to {destination_asset_code}:{destination_asset_issuer}. Skipping.")
                continue

            # trustline 
            trust_transaction = (
                TransactionBuilder(
                    source_account=source_account,
                    network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
                )
                .append_change_trust_op(asset)
                .build()
            )
            trust_transaction.sign(source_keypair)
            server.submit_transaction(trust_transaction)
            print(f"Trust line created for asset {asset_code}:{issuer}.")

            # Claim the balance
            if not claim_claimable_balance(server, source_keypair, claimable_balance_id):
                return "Failed to claim a balance."

            source_asset = asset
            if str(destination_asset_code).lower() != 'xlm':
                dest_asset = Asset(destination_asset_code, destination_asset_issuer)
            else:
                dest_asset = Asset.native()
            payment_op = PathPaymentStrictSend(
                send_asset=source_asset,
                send_amount=str(claimed_balance_amount),
                destination="", # ADD DEST ACCOUNT
                dest_asset=dest_asset,
                dest_min="0.0000001",  # Adjust the minimum amount as needed
                path=optimal_path,
            )

            transaction = TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
            ) \
                .append_operation(payment_op) \
                .build()

            transaction.sign(source_keypair)
            server.submit_transaction(transaction)
            print(f"Swapped {claimed_balance_amount} {asset_code} for {destination_asset_code} using the optimal path: {optimal_path}")

            transaction = TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE
                ) \
                .append_change_trust_op(asset,limit="0") \
                .build()

            transaction.sign(source_keypair)
            server.submit_transaction(transaction)
            print(f"Trust line for asset {asset_code}:{issuer} removed.")

        return "Claimed and swapped all balances successfully."

    except Exception as e:
        return f"Error processing claimable balances: {str(e)}"

import multiprocessing

def process_claimable_balances_view(request):
    if request.method == "POST":
        secret_key = request.POST.get("secret_key")
        print(secret_key)
        destination_asset_code = request.POST.get("destination_asset_code")
        destination_asset_issuer = request.POST.get("destination_asset_issuer")

        if not secret_key or not destination_asset_code or not destination_asset_issuer:
            return JsonResponse({"message": "Invalid input. Please provide all required parameters."}, status=400)
        claim_process = multiprocessing.Process(target=process_claimable_balances,args=(secret_key, destination_asset_code, destination_asset_issuer))
        claim_process.start()

        return  redirect('/account_checker/claim_balances/')
    else:
        return JsonResponse({"message": "Invalid request method."}, status=400)


@login_required
def claim_balance(request):
    return render(request,'bulkclaim.html')
