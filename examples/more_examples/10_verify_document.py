from pycardano import *
from dotenv import load_dotenv
import os
from os.path import exists
from blockfrost import BlockFrostApi, ApiError, ApiUrls,BlockFrostIPFS
import sys
import random
from hashlib import sha256
import urllib.request 
import json

def split_into_64chars(string):
    return [string[i:i+64] for i in range(0, len(string), 64)]

load_dotenv()
network = os.getenv('network')
wallet_mnemonic = os.getenv('wallet_mnemonic')
blockfrost_api_key = os.getenv('blockfrost_api_key')



if network=="testnet":
    base_url = ApiUrls.preprod.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET


new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)


main_address=Address(payment_part=payment_skey.to_verification_key().hash(), staking_part=staking_skey.to_verification_key().hash(),network=cardano_network)



prefix = "a401010327200621"
jsonkey = json.loads(payment_skey.to_verification_key().to_non_extended().to_json())



api = BlockFrostApi(project_id=blockfrost_api_key, base_url=base_url)
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

#get commandline arguments

transaction_id = sys.argv[1]
document_hash = sys.argv[2]


onchain_metadata = api.transaction_metadata(transaction_id)

if onchain_metadata is None:
    print("No metadata onchain.")
    sys.exit(1)


if "1787" in onchain_metadata[0].label:
    print("This transaction has a 1787 metadata label onchain.")

    result = onchain_metadata[0].json_metadata

    if document_hash in str(result): 
        print("Document hash found onchain.")

        if getattr(result, document_hash).signature:
            print("Signature found onchain.")
            signature = getattr(result, document_hash).signature

            public_key = f"{prefix}{jsonkey['cborHex']}"

            signed_message = {
                "signature": ''.join(signature),
                "key": public_key,
            }

            result = cip8.verify(signed_message=signed_message, attach_cose_key=True)


            if result["verified"]:
                print("This signature is verified correctly, this document was signed by this wallet/identity.")
                print("Original payload:")
                print(result["message"])
            else:
                print("This signature is NOT correct!")
        else:
            print("This transaction does not have a signatuer attribute")
    else:
        print(f"Document hash ({document_hash}) was not found in this transaction.")
else:
    print("This transaction DOES NOT have a 1787 metadata label.")






