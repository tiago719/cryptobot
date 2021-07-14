import sys
import threading
import websocket
import json
import time
from threading import Thread
from copy import deepcopy


TRADE_SYMBOL = sys.argv[1]
TOTAL_WORKERS = int(sys.argv[2])
INVEST_PER_WORKER = int(sys.argv[3])
WIN_MARGIN = float(sys.argv[4])


STREAM = 'wss://stream.binance.com:9443/ws/{}@kline_1m'.format(TRADE_SYMBOL.lower())
OPERATIONS_COMPLETED = False
LAST_VALUE = None


OPERATIONS = []
def show_operations():
    while not OPERATIONS_COMPLETED:
        print('\n\n\n\n')
        for op in OPERATIONS:
            print('Worker: {}; Ended: {}; Buy Value: {}; Sell Value: {};'.format(
                op['worker'],
                op['ended'],
                op['buy_value'],
                op['sell_value']
            ))

        time.sleep(15)

PRINT_THREAD = Thread(target=show_operations)
PRINT_THREAD.start()


class HandleStream:
    def on_open(ws):
        print('Opened connection')

    def on_close(ws):
        print('Closed connection')

    def on_error(ws, error):
        print(error)

    def on_message(ws, message):
        global closes, LAST_VALUE
        message = json.loads(message)

        candle = message['k']
        LAST_VALUE = float(candle['c'])
        print('Last Value', LAST_VALUE)


start_time = time.time()


ws = None


def run_server():
    global ws
    ws = websocket.WebSocketApp(
        STREAM,
        on_open=HandleStream.on_open,
        on_close=HandleStream.on_close,
        on_message=HandleStream.on_message
    )
    ws.run_forever()


STREAM_THREAD = Thread(target=run_server)
STREAM_THREAD.start()


workers_count = 0
def run_operations():
    global workers_count, LAST_VALUE, OPERATIONS
    workers_count += 1

    op = {'buy_value': None, 'sell_value': None, 'worker': workers_count, 'ended': False}
    OPERATIONS.append(op)

    while True:
        if LAST_VALUE is not None:
            op['buy_value'] = LAST_VALUE
            break
        else:
            time.sleep(1)

    while True:
        current_value = LAST_VALUE

        if op['sell_value']:
            if current_value >= op['sell_value']:
                # Sell
                print('Worker {}: Just sold at {}'.format(op['worker'], op['sell_value']))
                op['ended'] = True
                return
            else:
                # Not high enough
                pass
        elif op['buy_value']:
            # Buy
            if current_value <= op['buy_value']:
                # Buy
                print('Worker {}: Just bought the value at {}'.format(op['worker'], op['buy_value']))
                profit = (WIN_MARGIN * op['buy_value']) / INVEST_PER_WORKER
                op['sell_value'] = op['buy_value'] + profit
            else:
                # Not low enough
                pass
        time.sleep(0.1)


start_time = time.time()
threads = []
def create_threads():
    for _ in range(0, TOTAL_WORKERS):
        thread = Thread(target=run_operations)
        thread.start()
        threads.append(thread)
        time.sleep(20)
t = Thread(target=create_threads)
t.start()
t.join()
for thread in threads:
    # Wait for all threads to wait
    thread.join()


OPERATIONS_COMPLETED = True
ws.close()
STREAM_THREAD.join()
PRINT_THREAD.join()

print('Execution time for {} workers: {}. Investing Value per worker: {}. Profit: {}'.format(
    TOTAL_WORKERS,
    time.time() - start_time,
    INVEST_PER_WORKER,
    WIN_MARGIN
))
exit
