import sys
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtNetwork import QTcpSocket


class SelfContainedPlugin:
    def __init__(self, host="127.0.0.1", port=12345):
        self.socket = QTcpSocket()
        self.socket.connected.connect(self.on_connected)
        self.socket.readyRead.connect(self.read_message)
        self.socket.errorOccurred.connect(self.on_error)

        # Connect to the launcher
        self.socket.connectToHost(host, port)

    def on_connected(self):
        print("[Plugin] Connected to launcher.")
        self.send_message("Hello from Self-Contained Plugin!")

    def read_message(self):
        while self.socket.bytesAvailable():
            message = self.socket.readAll().data().decode()
            print(f"[Plugin] Received: {message}")

    def send_message(self, message):
        if self.socket.state() == QTcpSocket.ConnectedState:
            self.socket.write((message + "\n").encode())
        else:
            print("[Plugin] Not connected to launcher.")

    def on_error(self, error):
        print(f"[Plugin] Socket error: {error}")


if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    plugin = SelfContainedPlugin()
    sys.exit(app.exec_())
