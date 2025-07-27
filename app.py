from flask import Flask, render_template, request
import os
import socket
import logging
from datetime import datetime
import time

# Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] - %(message)s',
#     handlers=[
#         logging.FileHandler("access.log"),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

app = Flask(__name__)

CAT = r"""
#########
# /\_/\ #
#( o.o )#
# > ^ < #
#########
"""
@app.route('/')
def index():
    # Get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get client IP information
    if request.headers.getlist("X-Forwarded-For"):
        x_forwarded_for = request.headers.getlist("X-Forwarded-For")[0]
        client_ip = x_forwarded_for.split(',')[0].strip()
    else:
        client_ip = request.remote_addr
    
    # Get the port of the client
    client_port = request.environ.get('REMOTE_PORT', 'Unknown')
    
    # Get the browser type
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Get server information
    server_name = request.headers.get('Host', 'Unknown')
    try:
        server_ip = socket.gethostbyname(socket.gethostname())
    except:
        server_ip = "Unknown"
    
    # Get additional headers
    name_address = request.headers.get('Name-Address', 'Not provided')
    server_proxy = request.headers.get('Server-Proxy', 'Not provided')
    x_forwarded_for_full = request.headers.get('X-Forwarded-For', 'Not provided')
    
    # Log the access
    # logger.info(f"Access: IP={client_ip}, Port={client_port}, User-Agent={user_agent}")
    
    # Gather all request headers for debugging
    all_headers = dict(request.headers)
    
    # return cURL or Webpage
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if "text/plain" in request.headers.get("Accept", ""):
        text = f"Your IP: {ip}\n{CAT}"
        return Response(text, mimetype="text/plain")
    else:
        # Render the template with the gathered information
        return render_template('index.html', 
                              client_ip=client_ip,
                              client_port=client_port,
                              user_agent=user_agent,
                              name_address=name_address,
                              server_proxy=server_proxy,
                              x_forwarded_for_full=x_forwarded_for_full,
                              server_name=server_name,
                              server_ip=server_ip,
                              all_headers=all_headers)

@app.after_request
def after_request(response):
    # Additional logging after request is processed
    timestamp = time.time()
    # logger.info(f"Response: Status={response.status_code}, Time={timestamp}")
    return response

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8005, debug=True)
