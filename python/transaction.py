import requests

def get_recipients_in_block(block_number, api_key):
    hex_block = hex(block_number)

    url = (
        "https://api.etherscan.io/api"
        "?module=proxy"
        "&action=eth_getBlockByNumber"
        f"&tag={hex_block}"
        "&boolean=true"
        f"&apikey={api_key}"
    )

    response = requests.get(url)
    data = response.json()

    transactions = data["result"].get("transactions", [])

    to_addresses = []
    for tx in transactions:
        to_addr = tx.get("to") 
        if to_addr is not None:
            to_addresses.append(to_addr)

    return to_addresses


if __name__ == "__main__":
    block_number = <insert block number>  
    api_key = "[API KEY]"

    try:
        recipients = get_recipients_in_block(block_number, api_key)
        print(f"Block Number: {block_number}")
        print("Recipients (to) addresses:")
        for addr in recipients:
            print(addr)
    except ValueError as e:
        print(e)
