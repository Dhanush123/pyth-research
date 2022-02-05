
from __future__ import annotations
import asyncio
from copy import deepcopy
import os
import signal
import sys
from typing import Any
import datetime
import csv 

from loguru import logger

# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pythclient.pythclient import PythClient  # noqa
from pythclient.ratelimit import RateLimit  # noqa
from pythclient.pythaccounts import PythPriceAccount, PythProductAccount  # noqa
from pythclient.utils import get_key # noqap
from pythclient.solana import SolanaClient, SolanaPublicKey, SOLANA_DEVNET_HTTP_ENDPOINT, SOLANA_DEVNET_WS_ENDPOINT, SOLANA_MAINNET_WS_ENDPOINT, SOLANA_MAINNET_HTTP_ENDPOINT

logger.enable('pythclient')
RateLimit.configure_default_ratelimit(overall_cps=9, method_cps=3, connection_cps=3)

to_exit = False
time, price_account = None, None
symbol = 'ETH-USD'
filename = 'placeholder.csv'

def set_to_exit(sig: Any, frame: Any):
    global to_exit
    to_exit = True

signal.signal(signal.SIGINT, set_to_exit)

async def main():
    global to_exit, price_account

    devnet = len(sys.argv) < 2 or (len(sys.argv) >= 2 and sys.argv[1] != 'main')
    price_account = get_price_account(devnet)
    v2_first_mapping_account_key = get_key('devnet', 'mapping') if devnet else get_key('mainnet', 'mapping')
    init_csv_writer('devnet' if devnet else 'mainnet')

    async with PythClient(first_mapping_account_key=v2_first_mapping_account_key) as pyth_client:
        watch_session = pyth_client.create_watch_session()
        await watch_session.connect()
        print('Subscribing to price_account')
        await watch_session.subscribe(price_account)
        print('Subscribed!')
        end_time = datetime.datetime.now() + datetime.timedelta(minutes=1)

        update_task = asyncio.create_task(watch_session.next_update())
        while datetime.datetime.now() < end_time:
            if to_exit:
                update_task.cancel()
                break
            done, _ = await asyncio.wait({update_task}, timeout=1)
            if update_task in done:
                await get_latest_price()

        print('Unsubscribing...')
        await watch_session.unsubscribe(price_account)
        await watch_session.disconnect()
        print('Disconnected')

async def get_latest_price():
  global price_account, time

  await price_account.update()
  time = datetime.datetime.now()
  print(f"{symbol}: {price_account.aggregate_price} ± {price_account.aggregate_price_confidence_interval} @ {time}")
  save_to_csv(price_account.aggregate_price, price_account.aggregate_price_confidence_interval, time)

def get_price_account(devnet : bool) -> PythPriceAccount:
    price_account_key = SolanaPublicKey('EdVCmQ9FSPcVe5YySXDPCRmc8aDQLKJ9xvYBMZPie1Vw' if devnet else 'JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB')
    solana_client = SolanaClient(endpoint=SOLANA_DEVNET_HTTP_ENDPOINT if devnet else SOLANA_MAINNET_HTTP_ENDPOINT, ws_endpoint=SOLANA_DEVNET_WS_ENDPOINT if devnet else SOLANA_MAINNET_WS_ENDPOINT)
    return PythPriceAccount(price_account_key, solana_client)

def init_csv_writer(net : str):
    global filename
    filename = f'{symbol}-pyth-{net}-{datetime.datetime.now()}.csv'
    fields = ['Price','Confidence Interval','Timestamp'] 
    with open(filename, 'w', encoding='utf-8') as csvfile: 
        csvwriter = csv.writer(csvfile).writerow(fields) 

def save_to_csv(price : float, confidence_interval : float, timestamp : str):
    global filename
    with open(filename, 'a+', encoding='utf-8') as csvfile: 
        csvwriter = csv.writer(csvfile).writerow([price, confidence_interval, timestamp]) 

asyncio.run(main())