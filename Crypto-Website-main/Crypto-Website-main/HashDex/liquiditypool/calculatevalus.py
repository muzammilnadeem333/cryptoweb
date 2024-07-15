def addLiquidity(source, signer, poolId, maxReserveA, maxReserveB):
    exactPrice = maxReserveA / maxReserveB
    minPrice = exactPrice - exactPrice * 0.1
    maxPrice = exactPrice + exactPrice * 0.1
    
    return exactPrice, minPrice, maxPrice

# Example usage:
source = "temp"
signer = "example_signer"
poolId = "example_pool_id" # FEE - F8T1 , WORK - FiT1
maxReserveA = 5564714.7075463
maxReserveB = 5556715.1390444

exactPrice, minPrice, maxPrice = addLiquidity(source, signer, poolId, maxReserveA, maxReserveB)

print("Exact Price:", exactPrice)
print("Min Price:", minPrice)
print("Max Price:", maxPrice)
