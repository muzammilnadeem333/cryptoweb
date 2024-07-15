

from django.db import models
import uuid

class BotConfiguration(models.Model):
    uuid = models.UUIDField(primary_key=True, default='', editable=False)
    mode = models.CharField(max_length=255)  
    pub_secret_key = models.CharField(max_length=255)  
    from_asset_code = models.CharField(max_length=255)  
    from_asset_issuer = models.CharField(max_length=255)  
    dest_asset_code = models.CharField(max_length=255)
    dest_asset_issuer = models.CharField(max_length=255) 
    destination_account = models.CharField(max_length=255 , default='false')
    custom_path = models.CharField(max_length=30, default='false')
    amount1 = models.DecimalField(max_digits=20, decimal_places=7)  
    amount2 = models.DecimalField(max_digits=20, decimal_places=7)  
    delay = models.IntegerField(default=18)



    def __str__(self):
        return str(self.uuid)
    

class MultiOperationConfiguration(models.Model):
    deposit_liquidity_pool_secret =  models.CharField(max_length=255)
    deposit_liquidity_asset_a = models.CharField(max_length=255)
    deposit_liquidity_asset_a_issuer = models.CharField(max_length=255)
    deposit_liquidity_asset_b = models.CharField(max_length=255)
    deposit_liquidity_asset_b_issuer = models.CharField(max_length=255)
    deposit_liquidity_asset_a_max_amount = models.DecimalField(max_digits=20, decimal_places=7)
    deposit_liquidity_asset_b_max_amount = models.DecimalField(max_digits=20, decimal_places=7)
    deposit_liquidity_min_price = models.DecimalField(max_digits=20, decimal_places=7)
    deposit_liquidity_max_price = models.DecimalField(max_digits=20, decimal_places=7)

    # Bot Configuration

    uuid = models.UUIDField(primary_key=True, default='', editable=False)
    mode = models.CharField(max_length=255)  
    pub_secret_key = models.CharField(max_length=255)  
    from_asset_code = models.CharField(max_length=255)  
    from_asset_issuer = models.CharField(max_length=255) 
    dest_asset_code = models.CharField(max_length=255)
    dest_asset_issuer = models.CharField(max_length=255) 
    destination_account = models.CharField(max_length=255 , default='false')
    custom_path = models.CharField(max_length=30, default='false')
    amount1 = models.DecimalField(max_digits=20, decimal_places=7) 
    amount2 = models.DecimalField(max_digits=20, decimal_places=7)  
    delay = models.IntegerField(default=18)

    # Liquidity Withdraw
    liquidity_pool_id = models.CharField(max_length=255)
    withdraw_liquidity_Amount = models.DecimalField(max_digits=20, decimal_places=7)
    withdraw_min_amount_A = models.DecimalField(max_digits=20, decimal_places=7)
    withdraw_min_amount_B = models.DecimalField(max_digits=20, decimal_places=7)


    def __str__(self):
        return str(self.uuid)