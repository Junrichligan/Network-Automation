import os
from flask import Flask, render_template, request
from netmiko import ConnectHandler

app = Flask(__name__)

# Device settings: one source of truth for the connection and the page
DEVICE_TYPE = "cisco_ios_telnet"  # switch to "cisco_ios" if SSH is enabled
DEVICE_IP = os.environ.get("ROUTER_IP", "192.168.10.31")
DEVICE_PORT = int(os.environ.get("ROUTER_PORT", "32770"))
COMMANDS = ["show version", "show ip interface brief", "show running-config"]


def connect_params():
    """Build connection settings. Credentials come from environment variables."""
    password = os.environ["ROUTER_PASS"]
    return {
        "device_type": DEVICE_TYPE,
        "ip": DEVICE_IP,
        "port": DEVICE_PORT,
        "username": os.environ["ROUTER_USER"],
        "password": password,
        "secret": os.environ.get("ROUTER_SECRET", password),
    }


def run_commands(commands):
    """Connect, enter enable mode, run each command, and always disconnect."""
    results = {}
    conn = ConnectHandler(**connect_params())
    try:
        conn.enable()
        for cmd in commands:
            results[cmd] = conn.send_command(cmd)
    finally:
        conn.disconnect()
    return results


@app.route("/", methods=["GET", "POST"])
def index():
    results, error = {}, None
    if request.method == "POST":
        try:
            results = run_commands(COMMANDS)
        except Exception as e:
            error = f"Connection failed: {e}"

    device = {"ip": DEVICE_IP, "port": DEVICE_PORT, "protocol": "Telnet"}
    return render_template(
        "index.html",
        results=results,
        error=error,
        device=device,
        commands=COMMANDS,
    )


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)