import websockets
import asyncio
import rplidar
from actual_lidar import *
from fake_lidar import *
import json
import sys
import serial.tools.list_ports
import serial


def getDevicePort():
    ports = serial.tools.list_ports.comports()

    for port in ports:
        if "USB" in port.device:
            return port.device


port = getDevicePort()


# @note Quick encoder from numpy's ndarray to json
# @note since json cannot serialize ndarrays
class NumpyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()


# lidar = RPLidar(port)
lidar = None

if port is None:
    print("[SERVER] Device port not found!")
    print("[SERVER] Using Fake Lidar")
    lidar = FakeLidar()
else:
    print(f"[SERVER] Device port {port} found!")
    lidar = ActualLidar()
lidar.connect()

clients = []  # @note List of clients connected in the server
buffer = None


# Creating WebSocket server
# @note Server listens for ConnectionClosedOK
# @note Sends data from the server to the client via websockets
# @note checks if the lidar we are sending data from is either FakeLidar or ActualLidar
# @note If current lidar is FakeLidar then we utilize NumpyEncoder.
async def sendServerDataToClient(websocket):
    clients.append(websocket)
    print("[SERVER] Client has connected to the server")
    # await websocket.send(json.dumps("[SERVER] You have connected to the server!"))
    # await asyncio.sleep(0.01)
    isConnectedStill = True

    try:
        while isConnectedStill:
            buffer = None

            # @note Checking lidars instance to see which data the buffer should contain
            # @note Buffer will send the raw data from the lidar to the client
            if isinstance(lidar, FakeLidar):
                buffer = json.dumps(lidar.get_measures(), cls=NumpyEncoder)
            else:
                buffer = json.dumps(lidar.get_measures())

            if len(clients) > 0:
                await websocket.send(buffer)
                await asyncio.sleep(0.2)

    except websockets.exceptions.ConnectionClosedOK:
        print("[SERVER] Client disconnected from server!")
        # await websocket.send(json.dumps("[SERVER] You have disconnected from the server"))
        # await asyncio.sleep(0.01)
        clients.remove(websocket)
    except websockets.ConnectionClosedError:
        print("[SERVER] Internal Server Error.")
        # await websocket.send(json.dumps("[SERVER] Internal Server error has occurred!"))
        # await asyncio.sleep(0.01)
    except rplidar.RPLidarException:
        print("[SERVER] RPLidarException has been caught!")
        # await websocket.send(json.dumps("[SERVER] RPLidarException has occurred!"))
        # await asyncio.sleep(0.01)
        lidar.disconnect()


async def startServer():
    async with websockets.serve(sendServerDataToClient, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        print("[SERVER] Server ON")
        asyncio.run(startServer())
    except KeyboardInterrupt:
        print("[SERVER] Keyboard Interrupt occurred!")
        lidar.disconnect()
