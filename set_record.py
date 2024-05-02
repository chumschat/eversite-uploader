import argparse
import asyncio
import logging
import os
import sys

import htmlmin
import nekoton as nt

from config import load_config
from domain import Domain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("set_record")
logger.setLevel(logging.INFO)

ONCHAIN_RECORD = 1004
ONCHAIN_CONTRACT_RECORD = 1005
SITE_SIZE_LIMIT = 889


async def main():
    parser = argparse.ArgumentParser(description="Set .ever domain record to store html or site address")
    parser.add_argument('-r', '--record',  default=1005, help='type of record to store your site (1004 or 1005)')
    parser.add_argument('html', nargs='?', help='path to html file for uploading')
    args = parser.parse_args()
    record = int(args.record)
    file_path = args.html
    if record not in [ONCHAIN_RECORD, ONCHAIN_CONTRACT_RECORD]:
        sys.exit(f"Record type must be {ONCHAIN_RECORD} or {ONCHAIN_CONTRACT_RECORD}")
    if record == ONCHAIN_RECORD:
        if not file_path:
            sys.exit(f"File path is required for {ONCHAIN_RECORD} record")
        elif not os.path.exists(file_path):
            sys.exit(f"File {file_path} not found!")

    config = load_config()
    transport = await config.get_transport()
    keypair = config.get_keypair()
    ever_wallet = nt.contracts.EverWallet(transport, keypair)
    address = ever_wallet.address
    logger.info("Address %s is used as uploader", address)

    domain_address = nt.Address(config.domain_address)
    domain = Domain(transport, domain_address)

    domain_info = await domain.get_info()
    if domain_info["owner"] != address:
        sys.exit(f"Uploader address {address} is not the owner of the domain {config.domain_address}")

    if record == ONCHAIN_CONTRACT_RECORD:
        logger.info("Setting domain %s record %d to site address %s",
                    domain_address, record, config.site_address)

        cell_abi = [("value", nt.AbiAddress())]
        cell_data = {"value": nt.Address(config.site_address)}
        cell = nt.Cell.build(abi=cell_abi, value=cell_data)
        payload = await domain.get_set_record_body(record, cell)

        tx = await ever_wallet.send(domain_address, nt.Tokens(1), payload, True)
        logger.info("Domain %s record %d successfully set in transaction %s",
                    domain_address, record, tx.hash.hex())

    if record == ONCHAIN_RECORD:
        with open(file_path) as f:
            site_source = f.read()
        site_source_min = htmlmin.minify(site_source, remove_comments=True, remove_empty_space=True)
        site_size = len(site_source_min.encode("utf-8"))
        if site_size >= SITE_SIZE_LIMIT:
            sys.exit(f"Html size is too big ({site_size} bytes), max size is 889 bytes")

        logger.info("Setting domain %s record %d to store html",
                    domain_address, record)

        cell_abi = [("value", nt.AbiString())]
        cell_data = {"value": site_source_min}
        cell = nt.Cell.build(abi=cell_abi, value=cell_data)
        payload = await domain.get_set_record_body(record, cell)

        tx = await ever_wallet.send(domain_address, nt.Tokens(1), payload, True)
        logger.info("Domain %s record %d successfully set in transaction %s",
                    domain_address, record, tx.hash.hex())


asyncio.run(main())
