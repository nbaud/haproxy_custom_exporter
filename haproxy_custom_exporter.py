from prometheus_client import start_http_server, Counter
import time
import re
from datetime import datetime

# Define Prometheus metric with all labels
requests_with_all_labels = Counter(
    'haproxy_requests_custom', 
    'HTTP requests by backend, server, status code, method, and referer', 
    ['backend', 'server', 'status_code', 'method', 'referer']
)

# Function to get the current log file path based on the current date
def get_log_file_path():
    current_date = datetime.now().strftime("%Y-%m-%d")
    return f"/var/log/2024/{current_date}"

# Regular expression to match and extract relevant data from the log lines
log_regex = re.compile(
    r'.*\] \S+ (?P<backend>[^/]+)/(?P<server>\S+) \S+ (?P<status_code>\d{3}|\-1|0).*"(?P<method>GET|POST|PUT|DELETE|<BADREQ>)[^"]*" referer:"(?P<referer>[^"]*)"'
)

# Function to process the entire log file from the beginning
def process_log_file(log_file_path, last_position=0):
    with open(log_file_path, 'r') as f:
        # Move to the last read position
        f.seek(last_position)
        
        # Read new lines
        for line in f:
            print(f"Processing line: {line.strip()}")
            match = log_regex.match(line)
            if match:
                backend = match.group('backend')
                server = match.group('server')
                status_code = match.group('status_code')
                method = match.group('method')
                referer = match.group('referer') or 'unknown'

                # Increment the metric with all labels
                requests_with_all_labels.labels(
                    backend=backend, 
                    server=server, 
                    status_code=status_code, 
                    method=method, 
                    referer=referer
                ).inc()

        # Return the new file position
        return f.tell()

if __name__ == "__main__":
    # Start the Prometheus HTTP server on port 8406
    start_http_server(8406)

    log_file_path = get_log_file_path()
    last_position = process_log_file(log_file_path)  # Reprocess the entire log file once at the start

    while True:
        last_position = process_log_file(log_file_path, last_position)  # Process only new lines on subsequent iterations
        time.sleep(60)  # Adjust the sleep time as needed
