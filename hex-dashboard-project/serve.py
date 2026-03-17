import http.server
import os
os.chdir('/Users/ongunozdemir/Desktop/Anthropic/anthropic-application/hex-dashboard-project')
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=8765)
