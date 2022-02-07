
from __future__ import annotations
import asyncio
import signal
import sys
from typing import Any
from datetime import datetime, timedelta

from loguru import logger

from pythclient.pythclient import PythClient  # noqa
from pythclient.ratelimit import RateLimit  # noqa
from pythclient.pythaccounts import PythPriceAccount  # noqa
from pythclient.utils import get_key # noqap
from pythclient.solana import SolanaClient, SolanaPublicKey, SOLANA_DEVNET_HTTP_ENDPOINT, SOLANA_DEVNET_WS_ENDPOINT, SOLANA_MAINNET_WS_ENDPOINT, SOLANA_MAINNET_HTTP_ENDPOINT

from utils import init_csv_writer, save_to_csv, PRICE_FEED_SYMBOL

logger.enable('pythclient')
RateLimit.configure_default_ratelimit(overall_cps=9, method_cps=3, connection_cps=3)

to_exit = False
time, price_account = None, None
pyth_csv_name = 'pyth.csv'

def set_to_exit(sig: Any, frame: Any):
    global to_exit
    to_exit = True

signal.signal(signal.SIGINT, set_to_exit)

async def main():
    global to_exit, price_account, pyth_csv_name

    devnet = len(sys.argv) < 2 or (len(sys.argv) >= 2 and sys.argv[1] != 'main')
    price_account = get_price_account(devnet)
    net_name = 'devnet' if devnet else 'mainnet'
    v2_first_mapping_account_key = get_key(net_name, 'mapping')
    net_name = 'devnet' if devnet else 'mainnet'
    pyth_csv_name = f'{PRICE_FEED_SYMBOL}-chainlink-{net_name}-{datetime.now()}.csv'
    fields = ['Price', 'Confidence Interval', 'Timestamp'] 
    init_csv_writer(pyth_csv_name, fields)

    async with PythClient(first_mapping_account_key=v2_first_mapping_account_key) as pyth_client:
        watch_session = pyth_client.create_watch_session()
        await watch_session.connect()
        print('Subscribing to price_account')
        await watch_session.subscribe(price_account)
        print('Subscribed!')
        # rate limit error will probably be hit in < 10 min
        end_time = datetime.now() + timedelta(minutes=10)

        update_task = asyncio.create_task(watch_session.next_update())
        while datetime.now() < end_time:
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
  global price_account, time, pyth_csv_name

  await price_account.update()
  time = datetime.now()
  save_to_csv(pyth_csv_name, [price_account.aggregate_price, price_account.aggregate_price_confidence_interval, time])
  print(f"{PRICE_FEED_SYMBOL}: {price_account.aggregate_price} ± {price_account.aggregate_price_confidence_interval} @ {time}")

def get_price_account(devnet : bool) -> PythPriceAccount:
    price_account_key = SolanaPublicKey('EdVCmQ9FSPcVe5YySXDPCRmc8aDQLKJ9xvYBMZPie1Vw' if devnet else 'JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB')
    solana_client = SolanaClient(endpoint=SOLANA_DEVNET_HTTP_ENDPOINT if devnet else SOLANA_MAINNET_HTTP_ENDPOINT, ws_endpoint=SOLANA_DEVNET_WS_ENDPOINT if devnet else SOLANA_MAINNET_WS_ENDPOINT)
    return PythPriceAccount(price_account_key, solana_client)

asyncio.run(main())