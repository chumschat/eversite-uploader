import argparse
import asyncio
import logging
import os
import sys

import htmlmin
import nekoton as nt

from config import load_config
from eversite import EverSite

MESSAGE_SIZE = 60_000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("upload_site")
logger.setLevel(logging.INFO)


async def main():
    parser = argparse.ArgumentParser(description="Upload html site to eversite contract")
    parser.add_argument('html', help='path to html file for uploading')
    args = parser.parse_args()
    file_path = args.html
    if not os.path.exists(file_path):
        sys.exit(f"File {file_path} not found")

    config = load_config()
    transport = await config.get_transport()
    keypair = config.get_keypair()
    address = nt.contracts.EverWallet.compute_address(keypair.public_key)
    site = EverSite(transport, nt.Address(config.site_address), keypair)

    logger.info("Address %s is used as uploader", address)
    site_owner = await site.get_owner()
    if site_owner != keypair.public_key:
        sys.exit(f"Uploader address {address} is not the owner of the site {config.site_address}")

    logger.info("Reading and minifying html from file %s", file_path)
    with open(file_path) as f:
        site_source = f.read()
    site_source_min = htmlmin.minify(site_source, remove_comments=True, remove_empty_space=True)
    site_chunks = []
    for i in range(0, len(site_source_min), MESSAGE_SIZE):
        site_chunks.append(site_source_min[i:i + MESSAGE_SIZE])

    chunks = len(site_chunks)
    logger.info("Minified html fits to %d chunks of %d symbols", chunks, MESSAGE_SIZE)
    logger.info("Uploading %d chunks to site %s", chunks, config.site_address)

    for index, chunk in enumerate(site_chunks):
        cell_abi = [("value", nt.AbiString())]
        cell_data = {"value": chunk}
        cell = nt.Cell.build(abi=cell_abi, value=cell_data)
        tx = await site.send_chunk(cell, index)
        logger.info("Uploaded %d/%d chunk in transaction %s", index+1, chunks, tx.hash.hex())

    logger.info("Site uploaded successfully")


asyncio.run(main())
