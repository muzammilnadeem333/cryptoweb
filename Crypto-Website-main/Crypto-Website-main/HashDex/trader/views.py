from django.shortcuts import render
from django.shortcuts import render, redirect
from stellar_sdk import Asset, TransactionBuilder, Server, Keypair, Network
from django.shortcuts import redirect, render
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stellar_sdk import Server, Asset, Keypair, TransactionBuilder, Network, LiquidityPoolAsset 
from stellar_sdk import *
from django.contrib import messages


@login_required
def render_sell_offer(request):
    return render(request, 'selloffers.html')


def create_sell_offer(request):
    if request.method == 'POST':
        secret_key = request.POST.get('secret')
        amount_to_buy  =  str(request.POST.get('selling_amount')).strip()
        selling_asset_code = str(request.POST.get('selling_asset_code')).strip() 
        selling_asset_issuer = str(request.POST.get('selling_asset_issuer')).strip()
        buying_asset_code = str(request.POST.get('buying_asset_code')).strip()
        buying_asset_issuer = str(request.POST.get('buying_asset_issuer')).strip()
        demand_price = str(request.POST.get('demand_price')).strip()
        offer_id = str(request.POST.get('offer_id')).strip()
        numbers_of_offers = str(request.POST.get('how_many')).strip()
        server = str(request.POST.get('server')).strip()


        if selling_asset_code.lower() == 'xlm' :
            selling_asset = Asset.native()
        else:
            selling_asset = Asset(selling_asset_code, selling_asset_issuer)
        if buying_asset_code.lower() == 'xlm'  :
            buying_asset = Asset.native()
        else:
            buying_asset = Asset(buying_asset_code, buying_asset_issuer)

        server = Server(server)
        source_keypair = Keypair.from_secret(secret=secret_key)

        try:
            account = server.load_account(account_id=source_keypair.public_key)
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('/offers/manage_sell_offers')

        amount_to_buy  = amount_to_buy  
        price = demand_price  
        offer_id = 0  

        operations = []

        for i in range(1, int(numbers_of_offers)+1,1): 
            amount_to_buy  = amount_to_buy   
            offer_id = 0  
            manage_sell_offer_op = ManageSellOffer(
                selling=selling_asset,
                buying=buying_asset,
                amount=amount_to_buy ,
                price=price,
                offer_id=offer_id
            )
            operations.append(manage_sell_offer_op)

        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
                base_fee=100
            )
        )
        for operation in operations:
            transaction.append_operation(operation)

        transaction = transaction.set_timeout(30).build()

        transaction.sign(source_keypair)

        try:
            response = server.submit_transaction(transaction)
            if response['successful']:
                messages.success(request, "Success: Sell offer created successfully")
            else:
                messages.error(request, "Error: Transaction was not successful")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('/offers/manage_sell_offers')



def create_buy_offer(request):
    if request.method == 'POST':
        secret_key = request.POST.get('secret')
        amount_to_buy =  str(request.POST.get('buying_amount')).strip()
        selling_asset_code = str(request.POST.get('selling_asset_code')).strip() 
        selling_asset_issuer = str(request.POST.get('selling_asset_issuer')).strip()
        buying_asset_code = str(request.POST.get('buying_asset_code')).strip()
        buying_asset_issuer = str(request.POST.get('buying_asset_issuer')).strip()
        demand_price = str(request.POST.get('demand_price')).strip()
        offer_id = str(request.POST.get('offer_id')).strip()
        numbers_of_offers = str(request.POST.get('how_many')).strip()
        server = str(request.POST.get('server')).strip()


        if selling_asset_code.lower() == 'xlm' :
            selling_asset = Asset.native()
        else:
            selling_asset = Asset(selling_asset_code, selling_asset_issuer)
        if buying_asset_code.lower() == 'xlm'  :
            buying_asset = Asset.native()
        else:
            buying_asset = Asset(buying_asset_code, buying_asset_issuer)

        server = Server(server)
        source_keypair = Keypair.from_secret(secret=secret_key)

        try:
            account = server.load_account(account_id=source_keypair.public_key)
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('/offers/manage_buy_offers')

        amount_to_buy  = amount_to_buy  
        price = demand_price  
        offer_id = 0  

        operations = []

        for i in range(1, int(numbers_of_offers)+1,1): 
            amount_to_buy  = amount_to_buy   
            offer_id = 0  
            manage_buy_offer_op = ManageBuyOffer(
            selling=selling_asset,
            buying=buying_asset,
            amount=amount_to_buy,
            price=price,
            offer_id=offer_id
        )
            operations.append(manage_buy_offer_op)

        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
                base_fee=100
            )
        )
        for operation in operations:
            transaction.append_operation(operation)

        transaction = transaction.set_timeout(30).build()

        transaction.sign(source_keypair)

        try:
            response = server.submit_transaction(transaction)
            if response['successful']:
                messages.success(request, "Success: Buy offer created successfully")
            else:
                messages.error(request, "Error: Transaction was not successful")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('/offers/manage_buy_offers')

def render_buy_offer(request):
    return render(request, 'buyoffers.html')