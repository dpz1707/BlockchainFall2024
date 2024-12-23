import json
from web3 import Web3
from solcx import compile_standard, install_solc


solidity_code = r'''
pragma solidity ^0.8.17;

contract EnergyTrading {
    event EnergyListed(address indexed seller, uint256 amountKWh, uint256 pricePerKWh);
    event EnergyPurchased(address indexed buyer, address indexed seller, uint256 amountKWh, uint256 totalPrice);

    struct Listing {
        uint256 amountKWh;     // how many kWh are offered
        uint256 pricePerKWh;   // price in wei per kWh
    }

    mapping(address => Listing) public listings;
    mapping(address => uint256) public energyBalance;

    function listEnergy(uint256 _amountKWh, uint256 _pricePerKWh) public {
        require(_amountKWh > 0, "Amount of energy must be > 0");
        require(_pricePerKWh > 0, "Price per kWh must be > 0");

        listings[msg.sender] = Listing(_amountKWh, _pricePerKWh);
        emit EnergyListed(msg.sender, _amountKWh, _pricePerKWh);
    }

    function buyEnergy(address _seller, uint256 _amountKWh) public payable {
        Listing storage listing = listings[_seller];
        require(listing.amountKWh >= _amountKWh, "Not enough energy available");
        
        uint256 totalPrice = listing.pricePerKWh * _amountKWh;
        require(msg.value == totalPrice, "Incorrect Ether sent for purchase");

        payable(_seller).transfer(totalPrice);

        listing.amountKWh -= _amountKWh;

        energyBalance[msg.sender] += _amountKWh;

        emit EnergyPurchased(msg.sender, _seller, _amountKWh, totalPrice);
    }
}
'''

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "EnergyTrading.sol": {
                "content": solidity_code
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                }
            }
        }
    },
)

contract_data = compiled_sol["contracts"]["EnergyTrading.sol"]["EnergyTrading"]
contract_abi = contract_data["abi"]
contract_bytecode = contract_data["evm"]["bytecode"]["object"]
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
deployer_account = w3.eth.accounts[0]
w3.eth.default_account = deployer_account


EnergyTrading = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

print("Deploying contract...")
tx_hash = EnergyTrading.constructor().transact()
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = tx_receipt.contractAddress

print(f"Contract deployed at address: {contract_address}")

energy_contract = w3.eth.contract(address=contract_address, abi=contract_abi)



def list_energy(seller_account, amount_kwh, price_per_kwh):

    nonce = w3.eth.get_transaction_count(seller_account)
    txn = energy_contract.functions.listEnergy(amount_kwh, price_per_kwh).buildTransaction({
        'from': seller_account,
        'nonce': nonce,
        'gas': 3000000,
        'gasPrice': w3.toWei('5', 'gwei')
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key="YOUR_PRIVATE_KEY_IF_NEEDED")
    tx_hash_local = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash_local)
    return receipt

def buy_energy(buyer_account, seller_address, amount_kwh, total_price_wei):
    nonce = w3.eth.get_transaction_count(buyer_account)
    txn = energy_contract.functions.buyEnergy(seller_address, amount_kwh).buildTransaction({
        'from': buyer_account,
        'nonce': nonce,
        'value': total_price_wei,  # Ether in Wei
        'gas': 3000000,
        'gasPrice': w3.toWei('5', 'gwei')
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key="YOUR_PRIVATE_KEY_IF_NEEDED")
    tx_hash_local = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash_local)
    return receipt

def list_energy_unlocked(seller_account, amount_kwh, price_per_kwh):
    return energy_contract.functions.listEnergy(amount_kwh, price_per_kwh).transact({
        'from': seller_account
    })

def buy_energy_unlocked(buyer_account, seller_address, amount_kwh, total_price_wei):
    return energy_contract.functions.buyEnergy(seller_address, amount_kwh).transact({
        'from': buyer_account,
        'value': total_price_wei
    })

print("\n--- Producer lists 100 kWh at 1 gwei each, Consumer (acct2) buys 30 kWh ---")
acct1 = w3.eth.accounts[1]
acct2 = w3.eth.accounts[2]

price_per_kwh = w3.toWei(1, 'gwei')  
list_tx_receipt = list_energy_unlocked(acct1, 100, price_per_kwh)
print(f"Energy listed by {acct1}. TX: {list_tx_receipt.hex() if hasattr(list_tx_receipt, 'hex') else list_tx_receipt}")

amount_to_buy = 30
total_price = price_per_kwh * amount_to_buy
buy_tx_receipt = buy_energy_unlocked(acct2, acct1, amount_to_buy, total_price)
print(f"Energy purchased by {acct2}. TX: {buy_tx_receipt.hex() if hasattr(buy_tx_receipt, 'hex') else buy_tx_receipt}")

balance_seller = energy_contract.functions.energyBalance(acct1).call()
balance_buyer = energy_contract.functions.energyBalance(acct2).call()
listing_info = energy_contract.functions.listings(acct1).call()

print(f"\n--- Final Balances ---")
print(f"Seller (acct1) energy balance: {balance_seller} kWh (should be 0 if they’re just selling)")
print(f"Buyer  (acct2) energy balance: {balance_buyer} kWh (should be 30)")

print(f"Remaining listing for {acct1}: {listing_info[0]} kWh at {listing_info[1]} wei/kWh")
