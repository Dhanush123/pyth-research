import asyncio
from datetime import datetime, timedelta
from re import sub

from asyncstdlib import enumerate
from solana.rpc.websocket_api import connect
from solana.rpc.request_builder import LogsSubscribeFilter

from utils import init_csv_writer, save_to_csv, PRICE_FEED_SYMBOL

chainlink_csv_name = 'chainlink.csv'

async def main():
    global chainlink_csv_name

    async with connect("ws://api.devnet.solana.com") as websocket:
        await websocket.logs_subscribe(LogsSubscribeFilter.mentions('5zxs8888az8dgB5KauGEFoPuMANtrKtkpFiFRmo3cSa9'))
        first_resp = await websocket.recv()
        subscription_id = first_resp.result
        fields=['Timestamp']
        # Chainlink is currently only available on devnet on Solana
        chainlink_csv_name = f'{PRICE_FEED_SYMBOL}-chainlink-devnet-{datetime.now()}.csv'
        init_csv_writer(chainlink_csv_name,fields)
        # Chainlink updates less frequently than Pyth so it's better to get an average value over a long period of time
        end_time = datetime.now() + timedelta(minutes=60)
        async for _, msg in enumerate(websocket):
            if datetime.now() < end_time:
                save_to_csv(chainlink_csv_name, [datetime.now()])
                print("Chainlink log", msg, "\n\n")
        await websocket.logs_unsubscribe(subscription_id)

asyncio.run(main())