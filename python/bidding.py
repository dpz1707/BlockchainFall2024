import json
from web3 import Web3
from solcx import compile_standard, install_solc

# 1. Solidity code for the Bidding contract
solidity_code = r'''
pragma solidity ^0.8.17;

contract Bidding {
    address public owner;
    bool public biddingOpen;
    
    address public lowestBidder;
    uint public lowestBid;

    mapping(address => uint) public bids;

    constructor() {
        owner = msg.sender;
        biddingOpen = true;
        lowestBid = type(uint).max;
    }

    function placeBid() public payable {
        require(biddingOpen, "Bidding is closed");
        require(msg.value > 0, "Bid must be greater than 0");
        require(bids[msg.sender] == 0, "You already placed a bid");

        bids[msg.sender] = msg.value;

        if (msg.value < lowestBid) {
            lowestBid = msg.value;
            lowestBidder = msg.sender;
        }
    }

    function closeBidding() public {
        require(msg.sender == owner, "Only the owner can close bidding");
        biddingOpen = false;
    }

    function getWinner() public view returns (address, uint) {
        require(!biddingOpen, "Bidding must be closed to get the winner");
        return (lowestBidder, lowestBid);
    }
}


compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "Bidding.sol": {
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

contract_data = compiled_sol["contracts"]["Bidding.sol"]["Bidding"]
contract_abi = contract_data["abi"]
contract_bytecode = contract_data["evm"]["bytecode"]["object"]


w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

deployer_account = w3.eth.accounts[0]
w3.eth.default_account = deployer_account


BiddingContract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

print("Deploying")
tx_hash = BiddingContract.constructor().transact()
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = tx_receipt.contractAddress

print(f"Contract deployed at address: {contract_address}")

bidding_contract = w3.eth.contract(address=contract_address, abi=contract_abi)


def place_bid(from_account, value_in_wei):
    # You can convert ETH to wei using: w3.toWei(1, 'ether'), etc.
    txn = bidding_contract.functions.placeBid().buildTransaction({
        'from': from_account,
        'value': value_in_wei,
        'nonce': w3.eth.get_transaction_count(from_account),
        'gas': 3000000,
        'gasPrice': w3.toWei('1', 'gwei'),
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key="YOUR_PRIVATE_KEY_IF_NEEDED")
    tx_hash_local = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash_local)
    return receipt


def place_bid_unlocked(from_account, value_in_wei):
    return bidding_contract.functions.placeBid().transact({
        'from': from_account,
        'value': value_in_wei
    })

print("\n--- Placing bids ---")
acct_1 = w3.eth.accounts[1]
acct_2 = w3.eth.accounts[2]
acct_3 = w3.eth.accounts[3]

bids = [
    (acct_1, w3.toWei(3, 'ether')),
    (acct_2, w3.toWei(2, 'ether')),
    (acct_3, w3.toWei(5, 'ether')),
]

for (account, bid_amount) in bids:
    print(f"Placing bid of {bid_amount} wei from {account}...")
    tx_receipt = place_bid_unlocked(account, bid_amount)
    print(f" - Transaction hash: {tx_receipt.transactionHash.hex()}")


print("\nClosing bidding")
close_tx = bidding_contract.functions.closeBidding().transact({
    "from": deployer_account
})
w3.eth.wait_for_transaction_receipt(close_tx)
print("Bidding closed.")

lowest_bidder, lowest_bid = bidding_contract.functions.getWinner().call()
print(f"\n--- Winner Info ---")
print(f"Lowest Bidder: {lowest_bidder}")
print(f"Lowest Bid   : {lowest_bid} wei")

print("\nScript complete. Bidding demonstration finished.")
