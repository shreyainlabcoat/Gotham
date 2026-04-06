# deployme.py
# Local deployment of the Gotham MCP Server
# Runs the server on 0.0.0.0:8000 so it is reachable from any device on your network.
#
# Run from this folder:
#   python deployme.py
#
# Then update SERVER in testme.py to:
#   http://127.0.0.1:8000/mcp       <- from this same machine
#   http://<your-ip>:8000/mcp       <- from another device on the same network

import os
import sys
import socket
import uvicorn

if __name__ == "__main__":
    _here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(_here)
    sys.path.insert(0, _here)

    # Print the local IP so you know where the server is reachable
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Gotham MCP Server starting...")
    print(f"  Local:   http://127.0.0.1:8000/mcp")
    print(f"  Network: http://{local_ip}:8000/mcp")
    print()

    uvicorn.run(
        "server:app",
        host="0.0.0.0",   # listen on all interfaces, not just localhost
        port=8000,
        reload=False,      # reload=False for stable "deployed" mode
    )
