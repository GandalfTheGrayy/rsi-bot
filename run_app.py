from __future__ import annotations

import os
import socket
import subprocess
import time
import webbrowser


def is_port_open(host: str, port: int) -> bool:
	s = socket.socket()
	s.settimeout(0.5)
	try:
		s.connect((host, port))
		return True
	except OSError:
		return False
	finally:
		s.close()


def main():
	port = int(os.getenv("STREAMLIT_PORT", 8501))
	url = f"http://localhost:{port}"
	if is_port_open("127.0.0.1", port):
		print(f"Streamlit already running at {url}")
		try:
			webbrowser.open(url)
		except Exception:
			pass
		return

	print("Starting Streamlit app...")
	proc = subprocess.Popen([
		"streamlit",
		"run",
		"app.py",
		"--server.port",
		str(port),
		"--server.headless",
		"true",
	])

	# Wait a bit for server to come up
	for _ in range(30):
		if is_port_open("127.0.0.1", port):
			print(f"App is up at {url}")
			try:
				webbrowser.open(url)
			except Exception:
				pass
			return
		time.sleep(1)

	print("Timed out waiting for Streamlit to start.")


if __name__ == "__main__":
	main()


