from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Get the IP address of the client
    if request.headers.getlist("X-Forwarded-For"):
        client_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        client_ip = request.remote_addr
    
    # Get the port of the client
    client_port = request.environ.get('REMOTE_PORT', 'Unknown')
    
    # Get the browser type
    user_agent = request.headers.get('User-Agent', 'Unknown')

    # Get other headers
    name_address = request.headers.get('Name-Address', 'Not provided')
    server_proxy = request.headers.get('Server-Proxy', 'Not provided')
    
    # Render the template with the gathered information
    return render_template('index.html', 
                          client_ip=client_ip,
                          client_port=client_port,
                          user_agent=user_agent,
			  name_address=name_address,
			  server_proxy=server_proxy)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
