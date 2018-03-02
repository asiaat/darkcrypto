import requests
import configparser


config = configparser.ConfigParser()
config.read("config.ini")


block_explorer_url      = config.get("blockchain","url")
webhose_access_token    = config.get("webhose","token")
blacklist               = config.get("webhose","blacklist")
webhose_base_url        = config.get("webhose","url")
webhose_darkweb_url     = "/darkFilter?token=%s&format=json&q=" % webhose_access_token


def get_all_transactions(bitcoin_address):
    """
    Retrieve all bitcoin transactions for a Bitcoin address
    :param bitcoin_address:
    :return: transaction's list
    """
    transactions = []
    from_number = 0
    to_number = 50

    block_explorer_url_full = block_explorer_url + bitcoin_address + "/txs?from=%d&to=%d" % (from_number, to_number)

    response = requests.get(block_explorer_url_full)

    try:
        results = response.json()
    except:
        print("[!] Error retrieving bitcoin transactions. Please re-run this script.")
        return transactions

    if results['totalItems'] == 0:
        print("[*] No transactions for %s" % bitcoin_address)
        return transactions

    transactions.extend(results['items'])

    while len(transactions) < results['totalItems']:
        from_number += 50
        to_number += 50

        block_explorer_url_full = block_explorer_url + bitcoin_address + "/txs?from=%d&to=%d" % (from_number, to_number)

        response = requests.get(block_explorer_url_full)

        results = response.json()

        transactions.extend(results['items'])

    print("[*] Retrieved %d bitcoin transactions." % len(transactions))

    return transactions



def get_unique_bitcoin_addresses(transaction_list):
    """
     Simple function to return a list of all unique
     bitcoin addresses from a transaction list

    :param transaction_list:
    :return:
    """
    bitcoin_addresses = []
    for tx in transaction_list:

        for addr in tx['vout'][0]['scriptPubKey']['addresses']:
            #print (addr)
            if addr not in bitcoin_addresses:
                bitcoin_addresses.append(addr)



    return tuple(bitcoin_addresses)

def test_webhose(bitcoin_addresses):
    bitcoin_to_hidden_services = {}
    count = 1
    result = None

    for bitcoin_address in bitcoin_addresses:

        print("[*] Searching %d of %d bitcoin addresses." % (count, len(bitcoin_addresses)))

        # search for the bitcoin address
        search_url  = webhose_base_url + webhose_darkweb_url + bitcoin_address
        response    = requests.get(search_url)
        result      = response.json()

        count += 1

    return result


def search_webhose(bitcoin_addresses):
    """
    Search Webhose.io for each bitcoin address
    :param bitcoin_addresses:
    :return:
    """
    bitcoin_to_hidden_services = {}
    count = 1

    for bitcoin_address in bitcoin_addresses:

        print("[*] Searching %d of %d bitcoin addresses." % (count, len(bitcoin_addresses)))

        # search for the bitcoin address
        search_url  = webhose_base_url + webhose_darkweb_url + bitcoin_address
        response    = requests.get(search_url)
        result      = response.json()

        # loop continually until we have retrieved all results at Webhose
        while result['totalResults'] > 0:

            # now walk each search result and map out the unique hidden services
            for search_result in result['darkposts']:

                if not bitcoin_to_hidden_services.has_key(bitcoin_address):
                    bitcoin_to_hidden_services[bitcoin_address] = []

                if search_result['source']['site'] not in bitcoin_to_hidden_services[bitcoin_address]:
                    bitcoin_to_hidden_services[bitcoin_address].append(search_result['source']['site'])

            # if we have 10 or less results no need to ding the API again
            if result['totalResults'] <= 10:
                break

            # build a filtering keyword string
            query = "%s" % bitcoin_address

            for hidden_service in bitcoin_to_hidden_services[bitcoin_address]:
                query += " -site:%s" % hidden_service

            # use the blacklisted onions as filters
            for hidden_service in blacklist:
                query += " -site:%s" % hidden_service

            search_url = webhose_base_url + webhose_darkweb_url + query

            response = requests.get(search_url)

            result = response.json()

        if bitcoin_to_hidden_services[bitcoin_address]:
            print("[*] Discovered %d hidden services connected to %s" % (
            len(bitcoin_to_hidden_services[bitcoin_address]), bitcoin_address))

        count += 1

    return bitcoin_to_hidden_services



if __name__ == '__main__':
    print("Bitcoin transactions explorer")

    bitcoin_address   = "1JAQc1a8jNZwkxUTUsTKBCb1MnbzcmPqKv"


    transaction_list  = get_all_transactions(bitcoin_address)
    bitcoin_addresses = ()

    if len(transaction_list) > 0:
        # get all of the unique bitcoin addresses
        bitcoin_addresses = get_unique_bitcoin_addresses(transaction_list)

    for addr in bitcoin_addresses:
        print(addr)

    webhose = test_webhose(bitcoin_addresses[:5])
    print(webhose)
