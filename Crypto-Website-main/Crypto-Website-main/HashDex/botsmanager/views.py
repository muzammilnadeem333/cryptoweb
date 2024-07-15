import multiprocessing
import os
import signal
import requests 
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import random
from .bot2 import MultiOperationBot , multi_try_trade_path_payment_receive , multi_try_trade_path_payment_receive_custom , multi_try_trade_path_payment_send ,multi_try_trade_path_payment_send_custom
from django.http import HttpResponse
from .models import BotConfiguration
from .models import MultiOperationConfiguration 
from .bot import Bot, try_custom_path_payment_recieve, try_custom_path_payment_send, try_trade_path_payment_send, try_trade_path_payment_recieve
import uuid
from stellar_sdk import Asset
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from stellar_sdk.exceptions import *
from liquiditypool.views import calculate_liquidity_pool_id



global bot_processess 
global multi_trans_bots_processes

bot_processess = {}
multi_trans_bots_processes = {}

global horizon_servers
horizon_servers = ['https://horizon.stellar.org/','https://horizon.publicnode.org/', 'https://horizon.stellar.lobstr.co', 'https://h.fchain.io/','http://149.102.142.236:8000/','http://144.91.100.250:8000/']

@login_required
def run_bot(request):
    return render(request, 'runbot.html')

@login_required
def run_bot2(request):
    return render(requests, 'run_bot_with_list_paths.html')


@login_required
def get_running_bots(request):
    if request.method == 'POST':
        secret_key = request.POST.get('secret_key')
        all_bots = BotConfiguration.objects.filter(pub_secret_key=secret_key)
    else:
        all_bots = BotConfiguration.objects.all()
    return render(request, 'all_bots.html', {'all_bots': all_bots})






def handler(request):
    if request.method == 'POST':
        mode = request.POST.get('mode')
        amount_1 = str(request.POST.get('amount1')).strip()
        amount_2 = str(request.POST.get('amount2')).strip()
        server_site = str(request.POST.get('server_index')).strip()
        pub_secret_key = str(request.POST.get('pub_secret_key')).strip()
        source_code = str(request.POST.get('source_code')).strip()
        source_issuer = str(request.POST.get('source_issuer')).strip()
        dest_code = str(request.POST.get('dest_code')).strip()
        delay = str(request.POST.get('delay')).strip()
        dest_issuer = str(request.POST.get('dest_issuer')).strip()
        dest_account = str(request.POST.get('dest_account')).strip()
        enable_custom_path = request.POST.get('enable_custom_path')
        global bot_processess # dictiannary for threads keys are bot's uuid
        custom_paths = []
        




        if source_code.lower() == 'xlm' :
            source_asset = Asset.native()
            print(source_asset)
        else:
            source_asset = Asset(source_code, source_issuer)
        if dest_code.lower() == 'xlm'  :
            destination_asset = Asset.native()
        else:
            destination_asset = Asset(dest_code, dest_issuer)

        new_bot = Bot(pub_secret_key=pub_secret_key,use_dest=dest_account,server_site=server_site,source_asset=source_asset,destination_asset=destination_asset,uuid=uuid.uuid4(),mode=mode)
        
        if enable_custom_path == 'true':
            custom_path_directory = "paths"
            os.makedirs(custom_path_directory, exist_ok=True)
            with open(os.path.join(custom_path_directory, f"{new_bot.uuid}-path.txt"), "w") as path_file:
                custom_paths = []  # Clear the list for each run
                for i in range(1, 6):  # Check up to 5 paths
                    path_code = request.POST.get(f'path{i}_code')
                    path_issuer = request.POST.get(f'path{i}_issuer')
                    if path_code and path_issuer != None:
                        path_issuer = path_issuer.strip()
                        path_code = path_code.strip()
                        if path_code and path_issuer:
                            if path_code.lower() == 'xlm' or path_issuer.lower() == 'n':
                                custom_paths.append(Asset.native())
                                path_file.write(f"{path_code},{path_issuer}\n")
                            else:
                                custom_paths.append(Asset(path_code, path_issuer))
                                path_file.write(f"{path_code},{path_issuer}\n")
        else:
            enable_custom_path = 'false'

        bot_config = BotConfiguration(
            uuid=new_bot.uuid,
            mode=mode,
            pub_secret_key=pub_secret_key,
            from_asset_code=source_code,
            from_asset_issuer=source_issuer,
            dest_asset_code=dest_code,
            dest_asset_issuer=dest_issuer,
            destination_account=dest_account,
            delay = delay,
            amount1=amount_1,
            amount2=amount_2,
            custom_path=enable_custom_path,
        )
        bot_config.save()
        

        def starter_func(instance=new_bot, amount1=amount_1, amount2=amount_2, enable_custom_path=enable_custom_path,custom_paths=custom_paths,delay=delay):

            if instance.mode == 'strict-send' and enable_custom_path == 'false':
                process = multiprocessing.Process(target=try_trade_path_payment_send, args=(instance, amount1, amount2,delay))
                process.start()
                bot_processess[str(new_bot.uuid)] = process.pid

            if instance.mode == 'strict-send' and enable_custom_path == 'true':
                process = multiprocessing.Process(target=try_custom_path_payment_send,args=(instance, amount1, amount2, custom_paths,delay))
                process.start()
                bot_processess[str(new_bot.uuid)] = process.pid


            if instance.mode == 'strict-receive' and enable_custom_path == 'false':
                process = multiprocessing.Process(target=try_trade_path_payment_recieve, args=(instance, amount1, amount2, delay))
                process.start()
                bot_processess[str(new_bot.uuid)] = process.pid


            if instance.mode == 'strict-receive' and enable_custom_path == 'true':
                print(delay)
                process = multiprocessing.Process(target=try_custom_path_payment_recieve,args=(instance, amount1, amount2,custom_paths,delay))
                process.start()
                bot_processess[str(new_bot.uuid)] = process.pid

            else:
                return 'Invalid Configs'

        try:
            starter_func(new_bot, amount_1, amount_2, enable_custom_path, custom_paths)
        except Exception as e:
            print('this is exception', e)

    content = "Hello, World!"
    return redirect('/run_bot/')




def view_logs(request, bot_uuid):
    if request.method == 'GET':
        try:
            # Filtering The Bot Based On the Id
            bot = BotConfiguration.objects.filter(uuid=bot_uuid).first()

            if bot is not None:
                log_file_path = os.path.join('logs', f'{bot_uuid}.log')
                if os.path.exists(log_file_path):
                    with open(log_file_path, 'r') as file:
                        content = file.read()
                        context = {
                            "bot": bot,
                            "logs": content
                        }
                else:
                    content = 'Logs Are Not Present At The Moment. Check Again in a Few Minutes'
                    context = {
                        "bot": bot,
                        "logs": content
                    }

                return render(request, 'presenting_log.html', context)
            else:
                # If bot doesnot Exisit
                return HttpResponse('Bot Configuration Not Found', content_type="text/plain")

        except Exception as e:
            return HttpResponse(content=e, content_type="text/plain")
    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")





# COULD BE DONE THROUGH MANAGING CONTAINERS. :) 

def starter_function(uuid,pub_secret_key,use_dest,server_site,amount1,amount2,source_asset,destination_asset,mode,enable_custom_path,delay):
    if enable_custom_path == 'true':
        path_file=os.path.join('paths',f'{uuid}-path.txt')
        with open(path_file, "r") as file:
                lines = file.readlines()
                if 0 < len(lines) <= 6:
                    optimal_path = []
                    for line in lines:
                        asset_code, asset_issuer = line.strip().split(",")
                        if asset_code == "XLM" or asset_code == "native":
                            optimal_path.append(Asset.native())
                            custom = optimal_path
                        else:
                            optimal_path.append(Asset(asset_code, asset_issuer))
                            custom = optimal_path
    newbot=Bot(pub_secret_key=pub_secret_key,use_dest=use_dest,server_site=server_site,source_asset=source_asset,destination_asset=destination_asset,uuid=uuid,mode=mode)
    instance=newbot
    if instance.mode == 'strict-send' and enable_custom_path == 'false':
        process = multiprocessing.Process(target=try_trade_path_payment_send, args=(instance, amount1, amount2, delay))
        process.start()
        bot_processess[str(instance.uuid)] = process.pid

    if instance.mode == 'strict-send' and enable_custom_path == 'true':
        process = multiprocessing.Process(target=try_custom_path_payment_send,args=(instance, amount1, amount2, custom,delay))
        process.start()
        bot_processess[str(instance.uuid)] = process.pid

    if instance.mode == 'strict-receive' and enable_custom_path == 'false':
        process = multiprocessing.Process(target=try_trade_path_payment_recieve, args=(instance, amount1, amount2,delay))
        process.start()

        bot_processess[str(instance.uuid)] = process.pid
        print(bot_processess)

    if instance.mode == 'strict-receive' and enable_custom_path == 'true':
        process = multiprocessing.Process(target=try_custom_path_payment_recieve,
                                          args=(instance, amount1, amount2, custom,delay))
        process.start()
        bot_processess[str(instance.uuid)] = process.pid

    else:
        return 'Invalid Configs'




def start_bot(request):
    connection.connect()
    if request.method == 'POST':
        bot_uuid = request.POST.get('bot_uuid')
        if str(bot_uuid) not in bot_processess:
            try:
                bot_object = BotConfiguration.objects.filter(uuid=bot_uuid).first()
                print(bot_object.from_asset_code)
                print(bot_object.from_asset_issuer)
                if bot_object.from_asset_code.lower() == 'xlm':
                    source_asset = Asset.native()
                else:
                    source_asset = Asset(bot_object.from_asset_code, bot_object.from_asset_issuer)
                if bot_object.dest_asset_code.lower() == 'xlm':
                    destination_asset = Asset.native()
                else:
                    destination_asset = Asset(bot_object.dest_asset_code, bot_object.dest_asset_issuer)
                rand =random.randint(0,5)
                server_site= horizon_servers[rand]

                print(bot_object.from_asset_code)
                print(bot_object.from_asset_issuer)
                delay = bot_object.delay

                starter_function(uuid=bot_uuid,pub_secret_key=bot_object.pub_secret_key,use_dest=bot_object.destination_account,server_site=server_site,amount1=bot_object.amount1,amount2=bot_object.amount2,source_asset=source_asset,destination_asset=destination_asset,mode=bot_object.mode,enable_custom_path=bot_object.custom_path,delay=delay)
                messages.success(request, f"Bot with UUID {bot_uuid} has been started successfully.")
            except Exception as e:
                messages.error(request, f"Failed to start bot with UUID {bot_uuid}. Error: {str(e)}")
        else:
            messages.warning(request, f"Bot with UUID {bot_uuid} is already running.")

        # Redirect to the 'all_bots' 
        return redirect('/run_bot/get_running_bots')
    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")

def render_clone(request):
    return render(request, 'clone_bot.html')

def clone_bot(request):
    connection.connect()
    if request.method == 'POST':
        bot_uuid = request.POST.get('bot_uuid')
        amount1 = request.POST.get('amount1')
        amount2 = request.POST.get('amount2')
        mode = request.POST.get('mode')
        print(mode)
        times = request.POST.get('times')
        for i in range(1, int(times)+1 , 1):
            try:
                bot_object = BotConfiguration.objects.filter(uuid=bot_uuid).first()
                if bot_object.from_asset_code.lower() == 'xlm':
                    source_asset = Asset.native()
                else:
                    source_asset = Asset(bot_object.from_asset_code, bot_object.from_asset_issuer)
                if bot_object.dest_asset_code.lower() == 'xlm':
                    destination_asset = Asset.native()
                else:
                    destination_asset = Asset(bot_object.dest_asset_code, bot_object.dest_asset_issuer)
                rand =random.randint(0,5)
                server_site= horizon_servers[rand]
                new_uuid = uuid.uuid4()
                bot_config = BotConfiguration(
                uuid=new_uuid,
                mode=mode,
                pub_secret_key=bot_object.pub_secret_key,
                from_asset_code=bot_object.from_asset_code,
                from_asset_issuer=bot_object.from_asset_issuer,
                dest_asset_code=bot_object.dest_asset_code,
                dest_asset_issuer=bot_object.dest_asset_issuer,
                destination_account=bot_object.destination_account,
                amount1=amount1,
                amount2=amount2,
                custom_path=bot_object.custom_path,
                )
                bot_config.save()
                print('saved successfully')
                if bot_object.custom_path == 'true':
                    path_file=os.path.join('paths',f'{bot_uuid}-path.txt')
                    new_log_file = os.path.join('paths',f'{new_uuid}-path.txt')
                    with open(path_file,'rb') as real:
                        with open(new_log_file, 'wb') as clone:
                            clone.write(real.read())

                starter_function(uuid=new_uuid,pub_secret_key=bot_object.pub_secret_key,delay=bot_object.delay,use_dest=bot_object.destination_account,server_site=server_site,amount1=amount1,amount2=amount2,source_asset=source_asset,destination_asset=destination_asset,mode=mode,enable_custom_path=bot_object.custom_path)
                messages.success(request, f"Bot with UUID {bot_uuid} has been cloned successfully.")
            except Exception as e:
                messages.error(request, f"Failed to Clone bot with UUID {bot_uuid}. Error: {str(e)}")
            messages.success(request, f"Bots has been cloned successfully.")    

            
        return redirect('/run_bot/get_running_bots')
    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")


def stop_bot(request):
    if request.method == 'POST':
        bot_uuid = request.POST.get('bot_uuid')
        print(bot_processess)
        
        if str(bot_uuid) in bot_processess:
            print('here')
            try:
                pid = bot_processess[str(bot_uuid)]
                print(pid)
                kill(pid)
                del bot_processess[str(bot_uuid)]
                messages.success(request, f"Bot with UUID {bot_uuid} has been stopped successfully.")
                return redirect('/run_bot/get_running_bots')
            except Exception as e:
                messages.error(request, f"Failed to stop bot with UUID {bot_uuid}. Error: {str(e)}")
            return redirect('/run_bot/get_running_bots')
        else:
            messages.warning(request, f"Bot with UUID {bot_uuid} is not running.")
        return redirect('/run_bot/get_running_bots')
    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")

    

def kill(pid):
    os.kill(pid, signal.SIGTERM)


def delete_bot(request):
    if request.method == 'POST':
        bot_uuid = request.POST.get('bot_uuid')

        # Check instance is running 
        if str(bot_uuid) in bot_processess:
            try:
                process = bot_processess[str(bot_uuid)]
                kill(process)  # Terminate the bot process
                del bot_processess[str(bot_uuid)]  # Removing the id frm the dictionary
            except Exception as e:
                messages.error(request, f'Error stopping bot: {str(e)}')

        #Delete Logs
        log_path_file=os.path.join('logs',f'{bot_uuid}.log')
        if os.path.exists(log_path_file):
            os.remove(log_path_file)
        else:
            pass    


        path_file=os.path.join('paths',f'{bot_uuid}-path.txt')
        if os.path.exists(path_file):
            os.remove(path_file)
        else:
            pass
        
        try:
            bot = BotConfiguration.objects.get(uuid=bot_uuid)
            bot.delete()
            messages.success(request, f'Bot with UUID {bot_uuid} has been deleted successfully.')
        except BotConfiguration.DoesNotExist:
            messages.warning(request, f'Bot with UUID {bot_uuid} not found in the database.')
        except Exception as e:
            messages.error(request, f'Error deleting bot: {str(e)}')

        return redirect('/run_bot/get_running_bots')  

    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")











# ---------------------------------------------------- PATHS -------------------------------------------------#

def get_asset_type(asset_code):
    if str(asset_code).lower() == 'xlm':
        return 'native'
    if len(asset_code) <= 4 and str(asset_code).lower() != 'xlm':
        return 'credit_alphanum4'
    if len(asset_code) > 4 :
        return 'credit_alphanum12'

def fetch_paths(request):
    if request.method == 'POST':
        mode = request.POST.get('mode')
        amount_1 = str(request.POST.get('amount1')).strip()
        amount_2 = str(request.POST.get('amount2')).strip()
        source_code = str(request.POST.get('source_code')).strip()
        source_issuer = str(request.POST.get('source_issuer')).strip()
        dest_code = str(request.POST.get('dest_code')).strip()
        dest_issuer = str(request.POST.get('dest_issuer')).strip()
        source_asset_type = get_asset_type(source_code)
        destination_asset_type = get_asset_type(dest_code)

        # Define the URL based on mode and asset types
        if mode == 'strict-send':
            if source_asset_type == 'native':
                url = f'https://horizon.stellar.org/paths/strict-send?destination_assets={dest_code}:{dest_issuer}&source_asset_type=native&source_amount={amount_1}'
            elif destination_asset_type == 'native':
                url = f'https://horizon.stellar.org/paths/strict-send?destination_assets={destination_asset_type}&source_asset_type={source_asset_type}&source_asset_issuer={source_issuer}&source_asset_code={source_code}&source_amount={amount_1}'
            else:
                url = f'https://horizon.stellar.org/paths/strict-send?destination_assets={dest_code}:{dest_issuer}&source_asset_type={source_asset_type}&source_asset_issuer={source_issuer}&source_asset_code={source_code}&source_amount={amount_1}'
        elif mode == 'strict-receive':
            if source_asset_type == 'native':
                url = f'https://horizon.stellar.org/paths/strict-receive?source_assets=native&destination_asset_type={destination_asset_type}&destination_asset_issuer={dest_issuer}&destination_asset_code={dest_code}&destination_amount={amount_1}'
            elif destination_asset_type == 'native':
                url = f'https://horizon.stellar.org/paths/strict-receive?source_assets={source_code}:{source_issuer}&destination_asset_type=native&destination_amount={amount_1}'
            else:
                url = f'https://horizon.stellar.org/paths/strict-receive?source_assets={source_code}:{source_issuer}&destination_asset_type={destination_asset_type}&destination_asset_issuer={dest_issuer}&destination_asset_code={dest_code}&destination_amount={amount_1}'

        try:
            # Make the request to Stellar Horizon
            print(url)
            response = requests.get(url)
            response_data = response.json()
            paths = response_data.get('_embedded', {}).get('records', [])
            data_to_return = { # Extracting paths
                'paths': paths,
            }
            print(data_to_return)
            return JsonResponse(data_to_return)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)






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
                    return None  # No liquidity pools found 
            else:
                raise BadRequestError("Error occurred")
    except BadRequestError as e:
        raise e

@login_required
def multi_transaction_bot_interface_view(request):
    return render(request , 'multibots_interface.html')


def handler_multi_transaction_bots(request):
    if request.method == 'POST':
        deposit_liquidity_pool_secret = str(request.POST.get('secret')).strip()
        deposit_liquidity_asset_a = str(request.POST.get('asset_a_code')).strip()
        deposit_liquidity_asset_a_issuer = str(request.POST.get('asset_a_issuer')).strip()
        deposit_liquidity_asset_b = str(request.POST.get('asset_b_code')).strip()
        deposit_liquidity_asset_b_issuer = str(request.POST.get('asset_b_issuer')).strip()
        deposit_liquidity_asset_a_max_amount = str(request.POST.get('max_amount_asset_a')).strip()
        deposit_liquidity_asset_b_max_amount = str(request.POST.get('max_amount_asset_b')).strip()
        deposit_liquidity_min_price = str(request.POST.get('min_price')).strip()
        deposit_liquidity_max_price = str(request.POST.get('max_price')).strip()
        # Trade Prams
        mode = request.POST.get('mode')
        amount_1 = str(request.POST.get('amount1')).strip()
        amount_2 = str(request.POST.get('amount2')).strip()
        server_site = str(request.POST.get('server_index')).strip()
        pub_secret_key = str(request.POST.get('pub_secret_key')).strip()
        source_code = str(request.POST.get('source_code')).strip()
        source_issuer = str(request.POST.get('source_issuer')).strip()
        dest_code = str(request.POST.get('dest_code')).strip()
        dest_issuer = str(request.POST.get('dest_issuer')).strip()
        dest_account = str(request.POST.get('dest_account')).strip()
        delay = str(request.POST.get('delay')).strip()
        enable_custom_path = request.POST.get('enable_custom_path')
        # Withdraw Liquidity
        withdraw_liquidity_Amount = str(request.POST.get('total_shares')).strip()
        withdraw_min_amount_A = str(request.POST.get('amount_asset_a')).strip()
        withdraw_min_amount_B = str(request.POST.get('amount_asset_b')).strip()



        global multi_trans_bots_processes # dictiannary for threads keys are bot's uuid
        custom_paths = []


        if source_code.lower() == 'xlm' :
            source_asset = Asset.native()
            print(source_asset)
        else:
            source_asset = Asset(source_code, source_issuer)
        if dest_code.lower() == 'xlm'  :
            destination_asset = Asset.native()
        else:
            destination_asset = Asset(dest_code, dest_issuer)

        liquidity_pool_id = calculate_liquidity_pool_id(asset_code_a=deposit_liquidity_asset_a,asset_issuer_a=deposit_liquidity_asset_a_issuer,asset_code_b=deposit_liquidity_asset_b,asset_issuer_b=deposit_liquidity_asset_b_issuer)


        new_bot = MultiOperationBot(pub_secret_key=pub_secret_key,use_dest=dest_account,server_site=server_site,source_asset=source_asset,destination_asset=destination_asset,uuid=uuid.uuid4(),mode=mode,liquidity_pool_id=liquidity_pool_id)
        
        if enable_custom_path == 'true':
            custom_path_directory = "paths"
            os.makedirs(custom_path_directory, exist_ok=True)
            with open(os.path.join(custom_path_directory, f"{new_bot.uuid}-path.txt"), "w") as path_file:
                custom_paths = []  # Clear the list for each run
                for i in range(1, 6):  # Check up to 5 paths
                    path_code = request.POST.get(f'path{i}_code')
                    path_issuer = request.POST.get(f'path{i}_issuer')
                    if path_code and path_issuer != None:
                        path_issuer = path_issuer.strip()
                        path_code = path_code.strip()
                        if path_code and path_issuer:
                            if path_code.lower() == 'xlm' or path_issuer.lower() == 'n':
                                custom_paths.append(Asset.native())
                                path_file.write(f"{path_code},{path_issuer}\n")
                            else:
                                custom_paths.append(Asset(path_code, path_issuer))
                                path_file.write(f"{path_code},{path_issuer}\n")
        else:
            enable_custom_path = 'false'
        
        
        def starter_func(instance=new_bot,delay=delay, amount1=amount_1, amount2=amount_2, enable_custom_path=enable_custom_path,custom_paths=custom_paths,liquidity_pool_id=liquidity_pool_id, deposit_Max_Amount_A= deposit_liquidity_asset_a_max_amount,deposit_Max_Amount_B = deposit_liquidity_asset_b_max_amount, deposit_Min_Price=deposit_liquidity_min_price, deposit_Max_Price=deposit_liquidity_max_price, withdraw_liquidity_Amount=withdraw_liquidity_Amount,withdraw_min_amount_A=withdraw_min_amount_A,withdraw_min_amount_B=withdraw_min_amount_B ):

            if instance.mode == 'strict-send' and enable_custom_path == 'false':
                process = multiprocessing.Process(target=multi_try_trade_path_payment_send, args=(instance, amount1, amount2,delay,liquidity_pool_id,deposit_Max_Amount_A,deposit_Max_Amount_B,deposit_Min_Price,deposit_Max_Price,withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B))
                process.start()
                multi_trans_bots_processes[str(new_bot.uuid)] = process.pid

            if instance.mode == 'strict-send' and enable_custom_path == 'true':
                process = multiprocessing.Process(target=multi_try_trade_path_payment_send_custom,args=(instance, custom_paths, amount1, amount2,delay,liquidity_pool_id,deposit_Max_Amount_A,deposit_Max_Amount_B,deposit_Min_Price,deposit_Max_Price,withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B))
                process.start()
                multi_trans_bots_processes[str(new_bot.uuid)] = process.pid


            if instance.mode == 'strict-receive' and enable_custom_path == 'false':
                process = multiprocessing.Process(target=multi_try_trade_path_payment_receive, args=(instance, amount1, amount2,delay,liquidity_pool_id,deposit_Max_Amount_A,deposit_Max_Amount_B,deposit_Min_Price,deposit_Max_Price,withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B))
                process.start()
                multi_trans_bots_processes[str(new_bot.uuid)] = process.pid


            if instance.mode == 'strict-receive' and enable_custom_path == 'true':
                print(delay)
                process = multiprocessing.Process(target=multi_try_trade_path_payment_receive_custom,args=(instance, custom_paths, amount1, amount2,delay,liquidity_pool_id,deposit_Max_Amount_A,deposit_Max_Amount_B,deposit_Min_Price,deposit_Max_Price,withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B))
                process.start()
                multi_trans_bots_processes[str(new_bot.uuid)] = process.pid

            else:
                return 'Invalid Configs'

        try:
            starter_func(instance=new_bot, delay=delay, amount1=amount_1, amount2=amount_2, enable_custom_path=enable_custom_path,custom_paths=custom_paths,liquidity_pool_id=liquidity_pool_id, deposit_Max_Amount_A= deposit_liquidity_asset_a_max_amount,deposit_Max_Amount_B = deposit_liquidity_asset_b_max_amount, deposit_Min_Price=deposit_liquidity_min_price, deposit_Max_Price=deposit_liquidity_max_price, withdraw_liquidity_Amount=withdraw_liquidity_Amount,withdraw_min_amount_A=withdraw_min_amount_A,withdraw_min_amount_B=withdraw_min_amount_B )
        except Exception as e:
            print('this is exception', e)
        
        bot_config = MultiOperationConfiguration(
            deposit_liquidity_pool_secret= deposit_liquidity_pool_secret,
            deposit_liquidity_asset_a = deposit_liquidity_asset_a,
            deposit_liquidity_asset_a_issuer = deposit_liquidity_asset_a_issuer,
            deposit_liquidity_asset_b = deposit_liquidity_asset_b,
            deposit_liquidity_asset_b_issuer = deposit_liquidity_asset_b_issuer,
            deposit_liquidity_asset_a_max_amount = deposit_liquidity_asset_a_max_amount,
            deposit_liquidity_asset_b_max_amount = deposit_liquidity_asset_b_max_amount,
            deposit_liquidity_min_price = deposit_liquidity_min_price,
            deposit_liquidity_max_price = deposit_liquidity_max_price,
            uuid = new_bot.uuid,
            mode = new_bot.mode,
            pub_secret_key=pub_secret_key,
            from_asset_code=source_code,
            from_asset_issuer=source_issuer,
            dest_asset_code=dest_code,
            dest_asset_issuer=dest_issuer,
            destination_account=dest_account,
            amount1=amount_1,
            amount2=amount_2,
            custom_path=enable_custom_path,
            delay = delay,
            liquidity_pool_id= liquidity_pool_id,
            withdraw_liquidity_Amount = withdraw_liquidity_Amount,
            withdraw_min_amount_A = withdraw_min_amount_A,
            withdraw_min_amount_B = withdraw_min_amount_B

        )
        bot_config.save()

    return redirect('/run_bot/multi_transaction_bot/')


@login_required
def multi_get_running_bots(request):
    if request.method == 'POST':
        secret_key = request.POST.get('secret_key')
        all_bots = MultiOperationConfiguration.objects.filter(pub_secret_key=secret_key)
    else:
        all_bots = MultiOperationConfiguration.objects.all()

    return render(request, 'multibot_running.html', {'all_bots': all_bots})



def multi_view_logs(request, bot_uuid):
    if request.method == 'GET':
        try:
            bot = MultiOperationConfiguration.objects.filter(uuid=bot_uuid).first()

            if bot is not None:
                log_file_path = os.path.join('logs', f'{bot_uuid}.log')
                if os.path.exists(log_file_path):
                    with open(log_file_path, 'r') as file:
                        content = file.read()
                        context = {
                            "bot": bot,
                            "logs": content
                        }
                else:
                    content = 'Logs Are Not Present At The Moment. Check Again in a Few Minutes'
                    context = {
                        "bot": bot,
                        "logs": content
                    }

                return render(request, 'presenting_log.html', context)
            else:
                # Handle the case where a BotConfiguration with the specified UUID does not exist
                return HttpResponse('Bot Configuration Not Found', content_type="text/plain")

        except Exception as e:
            return HttpResponse(content=e, content_type="text/plain")
    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")
    


# start multi  opertational bots 


def multi_starter_function(uuid,delay,pub_secret_key,usedest,mode, source_asset, destination_asset,server_site,amount1, amount2, enable_custom_path,liquidity_pool_id, deposit_Max_Amount_A,deposit_Max_Amount_B , deposit_Min_Price, deposit_Max_Price, withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B):
    
    global multi_trans_bots_processes
    

    if enable_custom_path == 'true':
        path_file=os.path.join('paths',f'{uuid}-path.txt')
        with open(path_file, "r") as file:
                lines = file.readlines()
                if 0 < len(lines) <= 6:
                    optimal_path = []
                    for line in lines:
                        asset_code, asset_issuer = line.strip().split(",")
                        if asset_code == "XLM" or asset_code == "native":
                            optimal_path.append(Asset.native())
                            custom_paths = optimal_path
                        else:
                            optimal_path.append(Asset(asset_code, asset_issuer))
                            custom_paths = optimal_path
    newbot=  MultiOperationBot(uuid=uuid, mode=mode, pub_secret_key=pub_secret_key,use_dest=usedest,server_site=server_site,source_asset=source_asset,destination_asset=destination_asset,liquidity_pool_id=liquidity_pool_id)
    instance=newbot
    print('HERE',enable_custom_path)
    if instance.mode == 'strict-send' and enable_custom_path == 'false':
        process = multiprocessing.Process(target=multi_try_trade_path_payment_send, args=(instance, amount1, amount2,delay,liquidity_pool_id,deposit_Max_Amount_A,deposit_Max_Amount_B,deposit_Min_Price,deposit_Max_Price,withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B))
        process.start()
        multi_trans_bots_processes[str(uuid)] = process.pid
        print(process.pid)
        
    if instance.mode == 'strict-send' and enable_custom_path == 'true':
        process = multiprocessing.Process(target=multi_try_trade_path_payment_send_custom,args=(instance, custom_paths, amount1, amount2,delay,liquidity_pool_id,deposit_Max_Amount_A,deposit_Max_Amount_B,deposit_Min_Price,deposit_Max_Price,withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B))
        process.start()
        multi_trans_bots_processes[str(uuid)] = process.pid
        print(process.pid)
        
    if instance.mode == 'strict-receive' and enable_custom_path == 'false':
        process = multiprocessing.Process(target=multi_try_trade_path_payment_receive, args=(instance, amount1, amount2,delay,liquidity_pool_id,deposit_Max_Amount_A,deposit_Max_Amount_B,deposit_Min_Price,deposit_Max_Price,withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B))
        process.start()
        multi_trans_bots_processes[str(uuid)] = process.pid
        print(process.pid)
    if instance.mode == 'strict-receive' and enable_custom_path == 'true':
        process = multiprocessing.Process(target=multi_try_trade_path_payment_receive_custom,args=(instance, custom_paths, amount1, amount2,delay,liquidity_pool_id,deposit_Max_Amount_A,deposit_Max_Amount_B,deposit_Min_Price,deposit_Max_Price,withdraw_liquidity_Amount,withdraw_min_amount_A,withdraw_min_amount_B))
        process.start()
        multi_trans_bots_processes[str(uuid)] = process.pid
        print(process.pid)
        

    else:
        return 'Invalid Configs'




# START BOAT FUNCTION 


def multi_start_bot(request):
    if request.method == 'POST':
        bot_uuid = request.POST.get('bot_uuid')
        if str(bot_uuid) not in multi_trans_bots_processes:
            print(f'STARTIGN BOT {bot_uuid}')
            print(f'Currently Running {multi_trans_bots_processes}')
            try:
                bot_object = MultiOperationConfiguration.objects.filter(uuid=bot_uuid).first()
                if bot_object.from_asset_code.lower() == 'xlm':
                    source_asset = Asset.native()
                else:
                    source_asset = Asset(bot_object.from_asset_code, bot_object.from_asset_issuer)
                if bot_object.dest_asset_code.lower() == 'xlm':
                    destination_asset = Asset.native()
                else:
                    destination_asset = Asset(bot_object.dest_asset_code, bot_object.dest_asset_issuer)
                rand =random.randint(0,5)
                server_site= horizon_servers[rand]
                multi_starter_function(uuid=bot_object.uuid,mode=bot_object.mode, pub_secret_key = bot_object.pub_secret_key,delay=bot_object.delay,enable_custom_path=bot_object.custom_path, amount1=bot_object.amount1, amount2=bot_object.amount2,liquidity_pool_id=bot_object.liquidity_pool_id,deposit_Max_Amount_A=bot_object.deposit_liquidity_asset_a_max_amount,deposit_Max_Amount_B=bot_object.deposit_liquidity_asset_b_max_amount,deposit_Max_Price=bot_object.deposit_liquidity_max_price,deposit_Min_Price=bot_object.deposit_liquidity_min_price,withdraw_liquidity_Amount=bot_object.withdraw_liquidity_Amount,withdraw_min_amount_A=bot_object.withdraw_min_amount_A,withdraw_min_amount_B=bot_object.withdraw_min_amount_B,usedest=bot_object.destination_account, source_asset=source_asset,destination_asset=destination_asset,server_site=server_site)
                print('BEFORE',multi_trans_bots_processes)
                messages.success(request, f"Bot with UUID {bot_uuid} has been started successfully.")
            except Exception as e:
                messages.error(request, f"Failed to start bot with UUID {bot_uuid}. Error: {str(e)}")
        else:
            messages.warning(request, f"Bot with UUID {bot_uuid} is already running.")

        
        return redirect('/run_bot/multi_operational_running_bots/')
    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")












# STOP BOT FUNCTION 


def multi_stop_bot(request):
    if request.method == 'POST':
        bot_uuid = request.POST.get('bot_uuid')
        print('STOPING BOT => ',bot_uuid )
        
        if str(bot_uuid) in multi_trans_bots_processes:
            try:
                pid = multi_trans_bots_processes[str(bot_uuid)]
                print('KILLED',pid)
                kill(pid)
                del multi_trans_bots_processes[str(bot_uuid)]
                messages.success(request, f"Bot with UUID {bot_uuid} has been stopped successfully.")
                return redirect('/run_bot/multi_operational_running_bots/')
            except Exception as e:
                messages.error(request, f"Failed to stop bot with UUID {bot_uuid}. Error: {str(e)}")
            return redirect('/run_bot/multi_operational_running_bots/')
        else:
            messages.warning(request, f"Bot with UUID {bot_uuid} is not running.")
        return redirect('/run_bot/multi_operational_running_bots/')
    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")
    






def multi_delete_bot(request):
    if request.method == 'POST':
        bot_uuid = request.POST.get('bot_uuid')
        print('DELETED BOT : ', bot_uuid)

        if str(bot_uuid) in multi_trans_bots_processes:
            try:
                process = multi_trans_bots_processes[str(bot_uuid)]
                kill(process) 
                del multi_trans_bots_processes[str(bot_uuid)]  # Remove the bot from the process dictionary
            except Exception as e:
                messages.error(request, f'Error stopping bot: {str(e)}')

        #Delete Logs
        log_path_file=os.path.join('logs',f'{bot_uuid}.log')
        if os.path.exists(log_path_file):
            os.remove(log_path_file)
        else:
            pass    


        path_file=os.path.join('paths',f'{bot_uuid}-path.txt')
        if os.path.exists(path_file):
            os.remove(path_file)
        else:
            pass
        
        try:
            bot = MultiOperationConfiguration.objects.get(uuid=bot_uuid)
            bot.delete()
            messages.success(request, f'Bot with UUID {bot_uuid} has been deleted successfully.')
        except MultiOperationConfiguration.DoesNotExist:
            messages.warning(request, f'Bot with UUID {bot_uuid} not found in the database.')
        except Exception as e:
            messages.error(request, f'Error deleting bot: {str(e)}')

        return redirect('/run_bot/multi_operational_running_bots/')  

    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")
    





    # CLONE BOTS


def multi_clone_bot(request):
    connection.connect()
    if request.method == 'POST':
        bot_uuid = request.POST.get('bot_uuid')
        amount1 = request.POST.get('amount1')
        amount2 = request.POST.get('amount2')
        mode = request.POST.get('mode')
        
        times = request.POST.get('times')
        print(f'CLOINIG {bot_uuid} {times} times')
        for i in range(1, int(times)+1 , 1):
            try:
                bot_object = MultiOperationConfiguration.objects.filter(uuid=bot_uuid).first()
                if bot_object.from_asset_code.lower() == 'xlm':
                    source_asset = Asset.native()
                else:
                    source_asset = Asset(bot_object.from_asset_code, bot_object.from_asset_issuer)
                if bot_object.dest_asset_code.lower() == 'xlm':
                    destination_asset = Asset.native()
                else:
                    destination_asset = Asset(bot_object.dest_asset_code, bot_object.dest_asset_issuer)
                rand =random.randint(0,5)
                server_site= horizon_servers[rand]
                new_uuid = uuid.uuid4()
                bot_config = MultiOperationConfiguration(
                deposit_liquidity_pool_secret= bot_object.deposit_liquidity_pool_secret,
                deposit_liquidity_asset_a = bot_object.deposit_liquidity_asset_a,
                deposit_liquidity_asset_a_issuer = bot_object.deposit_liquidity_asset_a_issuer,
                deposit_liquidity_asset_b = bot_object.deposit_liquidity_asset_b,
                deposit_liquidity_asset_b_issuer = bot_object.deposit_liquidity_asset_b_issuer,
                deposit_liquidity_asset_a_max_amount = bot_object.deposit_liquidity_asset_a_max_amount,
                deposit_liquidity_asset_b_max_amount = bot_object.deposit_liquidity_asset_b_max_amount,
                deposit_liquidity_min_price = bot_object.deposit_liquidity_min_price,
                deposit_liquidity_max_price = bot_object.deposit_liquidity_max_price,
                uuid=new_uuid,
                mode=mode,
                pub_secret_key=bot_object.pub_secret_key,
                from_asset_code=bot_object.from_asset_code,
                from_asset_issuer=bot_object.from_asset_issuer,
                dest_asset_code=bot_object.dest_asset_code,
                dest_asset_issuer=bot_object.dest_asset_issuer,
                destination_account=bot_object.destination_account,
                liquidity_pool_id = bot_object.liquidity_pool_id,
                amount1=amount1,
                amount2=amount2,
                delay = bot_object.delay,
                custom_path=bot_object.custom_path,
                withdraw_liquidity_Amount = bot_object.withdraw_liquidity_Amount,
                withdraw_min_amount_A = bot_object.withdraw_min_amount_A,
                withdraw_min_amount_B = bot_object.withdraw_min_amount_B
                )
                bot_config.save()
                print('saved successfully')
                if bot_object.custom_path == 'true':
                    path_file=os.path.join('paths',f'{bot_uuid}-path.txt')
                    new_log_file = os.path.join('paths',f'{new_uuid}-path.txt')
                    with open(path_file,'rb') as real:
                        with open(new_log_file, 'wb') as clone:
                            clone.write(real.read())
                    
                multi_starter_function(uuid=new_uuid,mode=mode, pub_secret_key = bot_object.pub_secret_key,delay=bot_object.delay,enable_custom_path=bot_object.custom_path, amount1=amount1, amount2=amount2,liquidity_pool_id=bot_object.liquidity_pool_id,deposit_Max_Amount_A=bot_object.deposit_liquidity_asset_a_max_amount,deposit_Max_Amount_B=bot_object.deposit_liquidity_asset_b_max_amount,deposit_Max_Price=bot_object.deposit_liquidity_max_price,deposit_Min_Price=bot_object.deposit_liquidity_min_price,withdraw_liquidity_Amount=bot_object.withdraw_liquidity_Amount,withdraw_min_amount_A=bot_object.withdraw_min_amount_A,withdraw_min_amount_B=bot_object.withdraw_min_amount_B,usedest=bot_object.destination_account, source_asset=source_asset,destination_asset=destination_asset,server_site=server_site)
                messages.success(request, f"Bot with UUID {bot_uuid} has been cloned successfully.")
            except Exception as e:
                messages.error(request, f"Failed to Clone bot with UUID {bot_uuid}. Error: {str(e)}")
            messages.success(request, f"Bots has been cloned successfully.")    

            
        return redirect('/run_bot/multi_operational_running_bots/')
    else:
        return HttpResponse('Method Not Allowed', content_type="text/plain")
    

def render_clone_multi(request):
    return render(request, 'multi_clone_bot.html')