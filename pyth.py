
from __future__ import annotations
import asyncio
import os
import signal
import sys
from typing import List, Any
import datetime

from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pythclient.pythclient import PythClient  # noqa
from pythclient.ratelimit import RateLimit  # noqa
from pythclient.pythaccounts import PythPriceAccount  # noqa
from pythclient.utils import get_key # noqa
from pythclient.solana import SolanaClient, SolanaPublicKey, SOLANA_DEVNET_HTTP_ENDPOINT, SOLANA_DEVNET_WS_ENDPOINT

logger.enable("pythclient")

RateLimit.configure_default_ratelimit(overall_cps=9, method_cps=3, connection_cps=3)

to_exit = False
account_key = SolanaPublicKey("EdVCmQ9FSPcVe5YySXDPCRmc8aDQLKJ9xvYBMZPie1Vw")
solana_client = SolanaClient(endpoint=SOLANA_DEVNET_HTTP_ENDPOINT, ws_endpoint=SOLANA_DEVNET_WS_ENDPOINT)
price = PythPriceAccount(account_key, solana_client)
latest_time = None

def set_to_exit(sig: Any, frame: Any):
    global to_exit
    to_exit = True


signal.signal(signal.SIGINT, set_to_exit)


async def main():
    global to_exit, account_key, solana_client, price
    use_program = len(sys.argv) >= 2 and sys.argv[1] == "program"
    v2_first_mapping_account_key = get_key("mainnet", "program")
    v2_program_key = get_key("mainnet", "program")
    async with PythClient(
        first_mapping_account_key=v2_first_mapping_account_key,
        program_key=v2_program_key if use_program else None,
    ) as c:
        await refresh()
        ws = c.create_watch_session()
        await ws.connect()
        if use_program:
            print("Subscribing to program account")
            await ws.program_subscribe(v2_program_key, await c.get_all_accounts())
        else:
            print("Subscribing to all prices")
            # for account in all_prices:
            await ws.subscribe(price)
        print("Subscribed!")

        while True:
            if to_exit:
                break
            update_task = asyncio.create_task(ws.next_update())
            while True:
                if to_exit:
                    update_task.cancel()
                    break
                done, _ = await asyncio.wait({update_task}, timeout=1)
                if update_task in done:
                  await refresh()
        print("Unsubscribing...")
        if use_program:
            await ws.program_unsubscribe(v2_program_key)
        else:
            for account in all_prices:
                await ws.unsubscribe(account)
        await ws.disconnect()
        print("Disconnected")

async def refresh():
  global price
  await price.update()
  time = datetime.datetime.now()
  print("ETH/USD is", price.aggregate_price, "±", price.aggregate_price_confidence_interval, "time", time)

asyncio.run(main())