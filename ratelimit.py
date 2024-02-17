import time

SEARCH_LIMIT = 5  # Maximum number of searches allowed within the time window
TIME_WINDOW = 60  # Time window in seconds (e.g., 60 seconds = 1 minute)

# Define a dictionary to store search counts for each IP address
search_counts = {}

# Function to check if a request exceeds the rate limit
def exceeds_rate_limit(ip_address):
    current_time = time.time()
    if ip_address not in search_counts:
        search_counts[ip_address] = [(current_time, 1)]
        return False
    else:
        # Remove old entries from the search counts list
        search_counts[ip_address] = [(t, c) for t, c in search_counts[ip_address] if current_time - t <= TIME_WINDOW]
        # Calculate the total number of searches within the time window
        total_searches = sum(count for _, count in search_counts[ip_address])
        return total_searches >= SEARCH_LIMIT