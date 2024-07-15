from django.shortcuts import redirect, render
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import requests
from stellar_sdk import Server, Asset, Keypair, TransactionBuilder, Network, LiquidityPoolAsset 
from stellar_sdk import *
from django.contrib import messages
from stellar_sdk.exceptions import *
from django.http import HttpResponse  


@login_required
def liquidity_pool_render(request):
    return render(request, 'liquidity-interface.html')



def get_liquidity_pool(request):
    if request.method == 'POST':

        asset_code_a = request.POST.get('asset1')
        asset_issuer_a = request.POST.get('asset1_issuer')

        asset_code_b = request.POST.get('asset2')
        asset_issuer_b = request.POST.get('asset2_issuer')
        horizon_url = "https://horizon.stellar.org"

        request_url = f"{horizon_url}/liquidity_pools?order=asc&limit=1&" \
                     f"reserves={asset_code_a}:{asset_issuer_a},{asset_code_b}:{asset_issuer_b}"
        if str(asset_code_a).lower() == 'xlm':
            asset_code_a = 'native'
            asset_issuer_a = ""
            request_url = f"{horizon_url}/liquidity_pools?order=asc&limit=1&" \
                     f"reserves={asset_code_a},{asset_code_b}:{asset_issuer_b}"
            print(request_url)
            
        if str(asset_code_b).lower() == 'xlm':
            asset_code_b = 'native'
            asset_issuer_b = ""
            request_url = f"{horizon_url}/liquidity_pools?order=asc&limit=1&" \
                     f"reserves={asset_code_a}:{asset_issuer_a},{asset_code_b}"

        
            

        print(request_url)
        response = requests.get(request_url)
        print(response)

        context = {
            'liquidity_pool_data': None,
            'error_message': None,
        }


        if response.status_code == 200:

            data = response.json()
            if data["_embedded"]["records"]:
          
                liquidity_pool_id = data["_embedded"]["records"][0]["id"]

   
                liquidity_pool_url = f"{horizon_url}/liquidity_pools/{liquidity_pool_id}"
                response = requests.get(liquidity_pool_url)

                if response.status_code == 200:
                    liquidity_pool_data = response.json()
                    context['liquidity_pool_data'] = liquidity_pool_data
                else:
                    context['error_message'] = f"Error retrieving liquidity pool details: {response.status_code}"
            else:
                context['error_message'] = "No liquidity pools found for the specified assets."
        else:
            context['error_message'] = f"Error: {response.status_code}"

    return render(request, 'liquidity_pool.html', context)

@login_required
def deposit_interface(request):
    return render(request, 'deposite.html')


from django.contrib import messages 

def establish_trustline_and_deposit(request):
    if request.method == 'POST':
        secret = request.POST.get('secret')
        asset_code_A = request.POST.get('asset_a_code')
        asset_issuer_A = request.POST.get('asset_a_issuer')
        asset_code_B = request.POST.get('asset_b_code')
        asset_issuer_B = request.POST.get('asset_b_issuer')
        max_amount_a = request.POST.get('max_amount_asset_a')
        max_amount_b = request.POST.get('max_amount_asset_b')
        min_amount = request.POST.get('min_price')
        max_amount = request.POST.get('max_price')

        try:
            liquidity_pool_id = calculate_liquidity_pool_id(asset_code_a=asset_code_A, asset_issuer_a=asset_issuer_A, asset_code_b=asset_code_B, asset_issuer_b=asset_issuer_B)
        except BadRequestError as e:
            error_message = str(e)
            messages.error(request, error_message)  
            return redirect('/liquidity/deposit/')

        stellar_server = Server("https://horizon.stellar.org")

        source_keypair = Keypair.from_secret(secret)
        source_account = stellar_server.load_account(source_keypair.public_key)

        source_account = stellar_server.load_account(source_keypair.public_key)

        deposit_tx = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_liquidity_pool_deposit_op(
                liquidity_pool_id=liquidity_pool_id,
                max_amount_a=str(max_amount_a),
                max_amount_b=str(max_amount_b),
                min_price=str(min_amount),  
                max_price=str(max_amount),  
            )
            .build()
        )

        deposit_tx.sign(source_keypair)

        try:
            stellar_server.submit_transaction(deposit_tx)
            messages.success(request, "Deposited")
        except BadRequestError as e:
            error_message = str(e)
            messages.error(request, error_message)  
            return redirect('/liquidity/deposit/')

        return redirect('/liquidity/deposit/')

    else:
        return redirect('/liquidity/deposit/')

def establish_pool_share(secret, asset_code_A, asset_issuer_A, asset_code_B, asset_issuer_B):
    try:
        stellar_server = Server("https://horizon.stellar.org")
        # Load source account
        source_keypair = Keypair.from_secret(secret)
        source_account = stellar_server.load_account(source_keypair.public_key)
        if str(asset_code_A).lower() == 'xlm':
            asset_a = Asset.native()
        else:
            asset_a = Asset(asset_code_A, asset_issuer_A)
        if str(asset_code_B).lower() == 'xlm':
            asset_b = Asset.native()
        else:
            asset_b = Asset(asset_code_B, asset_issuer_B)

        pool_share_asset = LiquidityPoolAsset(
            asset_a=asset_a,  
            asset_b=asset_b,  
        )
        trustline_tx = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_change_trust_op(
                asset=pool_share_asset,
                limit="100000",  
            )
            .build()
        )
        trustline_tx.sign(source_keypair)
        response = stellar_server.submit_transaction(trustline_tx)
        return response
    except BadRequestError as e:
        raise e

def calculate_liquidity_pool_id(asset_code_a, asset_issuer_a, asset_code_b, asset_issuer_b):
    horizon_url = "https://horizon.stellar.org"

    try:
        request_url = f"{horizon_url}/liquidity_pools?order=asc&limit=1&" \
                     f"reserves={asset_code_a}:{asset_issuer_a},{asset_code_b}:{asset_issuer_b}"

        if str(asset_code_a).lower() == 'xlm':
            asset_code_a = 'native'
            asset_issuer_a = ""
            request_url = f"{horizon_url}/liquidity_pools?order=asc&limit=1&" \
                         f"reserves={asset_code_a},{asset_code_b}:{asset_issuer_b}"

        if str(asset_code_b).lower() == 'xlm':
            asset_code_b = 'native'
            asset_issuer_b = ""
            request_url = f"{horizon_url}/liquidity_pools?order=asc&limit=1&" \
                         f"reserves={asset_code_a}:{asset_issuer_a},{asset_code_b}"
        print(request_url)
        response = requests.get(request_url)

        if response.status_code == 200:
            data = response.json()
            if data["_embedded"]["records"]:
                liquidity_pool_id = data["_embedded"]["records"][0]["id"]
                return liquidity_pool_id
            else:
                return None  
        else:
            raise BadRequestError("Error occurred")
    except BadRequestError as e:
        raise e

def withdraw(request):
    return render(request, 'withdraw.html')




def withdraw_from_liquidity_pool(request):
    if request.method == 'POST':
        secret = request.POST.get('secret')
        liquidity_pool_id = request.POST.get('liquidity_pool_id')
        total_shares = request.POST.get('total_shares')
        amount_a = request.POST.get('amount_asset_a')
        amount_b = request.POST.get('amount_asset_b')

        stellar_server = Server("https://horizon.stellar.org")

        source_keypair = Keypair.from_secret(secret)
        source_account = stellar_server.load_account(source_keypair.public_key)

        withdraw_tx = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_liquidity_pool_withdraw_op(
                liquidity_pool_id=liquidity_pool_id,
                amount=str(total_shares),
                min_amount_a=str(amount_a),
                min_amount_b=str(amount_b)
            )
            .build()
        )

        withdraw_tx.sign(source_keypair)

        try:
            stellar_server.submit_transaction(withdraw_tx)
            messages.success(request, "Withdrawn successfully")
        except BadRequestError as e:
            error_message = str(e)
            messages.error(request, error_message)

        return redirect('/liquidity/withdraw/')

    else:
        return redirect('/liquidity/withdraw/')
    

def calculate_id(request):
    return render(request , 'calculate_liquidity_pool_id.html')

def calculate_liquidity_pool_id_view(request):
    if request.method == 'POST':
        asset_code_a = request.POST.get('asset_code_a')
        asset_issuer_a = request.POST.get('asset_issuer_a')
        asset_code_b = request.POST.get('asset_code_b')
        asset_issuer_b =request.POST.get('asset_issuer_b')

        liquidity_pool_id = calculate_liquidity_pool_id(
            asset_code_a, asset_issuer_a, asset_code_b, asset_issuer_b
        )

        if liquidity_pool_id:
            messages.success(request, f'Liquidity Pool ID: {liquidity_pool_id}')
        else:
            messages.error(request, 'No liquidity pool found for the specified assets')

        return redirect('/liquidity/calculateID/')  

    return redirect('/liquidity/calculateID/')  
            

def establish_pool_share_trust(request):

    return render(request, 'establish_pool_share.html')


def establish_pool_share_trust_view(request):
    if request.method == 'POST':
        secret = str(request.POST.get('secret')).strip()
        asset_code_a = request.POST.get('asset_code_a')
        asset_issuer_a = request.POST.get('asset_issuer_a')
        asset_code_b = request.POST.get('asset_code_b')
        asset_issuer_b =request.POST.get('asset_issuer_b')
        try:
            establish_pool_share(secret=secret,asset_code_A=asset_code_a,asset_issuer_A=asset_issuer_a,asset_code_B=asset_code_b,asset_issuer_B=asset_issuer_b)
            messages.success(request, f'Established Trust')
        except BadRequestError as e:
            messages.success(request, f'ERROR : {e}')

        return redirect('/liquidity/establish_pool_share/')
    else:
        return redirect('/liquidity/establish_pool_share/')
