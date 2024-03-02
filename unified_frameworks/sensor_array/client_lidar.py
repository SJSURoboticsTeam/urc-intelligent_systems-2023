import asyncio
import websockets
from LidarClass import Lidar
from threading import Thread
import json

class WirelessLidar(Lidar):
    def __init__(self, uri):
        self.uri = uri
        self.data = None
        self.connected = True
        self.thread = Thread(target=self.start_connection)
        self.thread.start()
    async def receive_data(self):
        async with websockets.connect(self.uri) as websocket:
            while self.connected:
                data = await websocket.recv()
                self.data = json.loads(data)
    def start_connection(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(self.receive_data())
    def iter_scans(self):
        return iter(self)
    def __iter__(self):
        return self
    def __next__(self):
        return self.data
    def stop(self):
        return super().stop()
    def stop_motor(self):
        return super().stop_motor()
    def disconnect(self):
        self.connected = False
        self.thread.join()

if __name__=='__main__':
    import time
    lidar = WirelessLidar("ws://192.168.1.107:8765")
    # lidar = WirelessLidar("ws://localhost:8765")
    lidar_iter = iter(lidar)
    start_time = time.time()
    count = 0
    while time.time() - start_time < 5:
        count += 1
        print()
        print(f"{count}: {next(lidar_iter)}")
        # time.sleep(0.005)
    lidar.disconnect()
    print("disconnected")