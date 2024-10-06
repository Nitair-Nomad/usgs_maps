import requests
from tqdm import tqdm  # Importing tqdm for the progress bar
import os
import time

# API endpoint
url = "https://tnmaccess.nationalmap.gov/api/v1/products"

# Starting offset
offset = 0

# Set to store unique download URLs
item_set = set()

# Variable to track total number of items (initially unknown)
total_items = None

# Loop to continue requests until all items are processed or an error is encountered
while True:
    # Update parameters with the current offset
    params = {
        'datasets': 'US Topo Current',  # Dataset name
        'prodFormats': '',              # Specify product format if needed
        'offset': str(offset)           # Incremented offset
    }

    # Send GET request
    response = requests.get(url, params=params)

    # Check if request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # If total items are not yet set, fetch it from the response
        if total_items is None:
            total_items = data.get('total', 0)
            print(f"Total items to download: {total_items}")
            # Initialize progress bar with the total number of items
            progress_bar = tqdm(total=total_items, desc="Creating Link List:")

        items = data.get('items', [])

        # If no items are found, break out of the loop
        if not items:
            print("No more items found. Ending loop.")
            break

        # Add download URLs to the set to ensure uniqueness
        for item in items:
            download_url = item.get('downloadURL')
            if download_url:  # Check if the download URL is valid (non-null)
                item_set.add(download_url)

        # Update the progress bar
        progress_bar.update(len(items))

        # Increment the offset by 50 for the next request
        offset += 50
    else:
        # Print error message and exit the loop if the request fails
        print(f"Error: {response.status_code} - {response.text}")
        break

# Close the progress bar after completion of link collection
progress_bar.close()

# Write the unique download URLs to a file
with open("out.txt", "w") as file:
    file.write('\n'.join(item_set))

# Print the total number of unique download URLs collected
print(f"Total unique download URLs collected: {len(item_set)}")
print(item_set)

# --- Start Downloading the Files ---

# Create a directory for downloads
download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)

# Initialize the progress bar for downloading files
download_progress = tqdm(total=len(item_set), desc="Downloading Files:", unit='file', unit_scale=True)

# Track download speed
start_time = time.time()
downloaded_bytes = 0

for url in item_set:
    try:
        # Send a GET request to download the file
        file_response = requests.get(url, stream=True)
        
        # Check if the download was successful
        if file_response.status_code == 200:
            # Extract the filename from the URL
            filename = os.path.join(download_dir, url.split("/")[-1])
            # Open a file and write the content
            with open(filename, "wb") as file:
                for chunk in file_response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    downloaded_bytes += len(chunk)  # Track the number of bytes downloaded
                    
                    # Calculate elapsed time and download speed
                    elapsed_time = time.time() - start_time
                    speed_kbps = (downloaded_bytes / 1024) / elapsed_time if elapsed_time > 0 else 0

                    # Update the progress bar with the current download speed
                    download_progress.set_postfix({"Speed": f"{speed_kbps:.2f} KB/s"})
                    download_progress.update(1)  # Update the progress bar for each file downloaded

        else:
            print(f"Failed to download {url}: {file_response.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Close the download progress bar after completion
download_progress.close()
print("All downloads completed.")