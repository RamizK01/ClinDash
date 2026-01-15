import requests
import zipfile
import os
from datetime import datetime
from tqdm import tqdm

def download_all_studies(output_dir="data"):
    # Generate the date-based subdirectory name (DDMMYYYY)
    date_str = datetime.now().strftime("%d%m%Y")
    sub_dir_name = f"data_{date_str}"
    target_path = os.path.join(output_dir, sub_dir_name)
    
    # Check if data already downloaded today
    if os.path.exists(target_path):
        file_count = len([f for f in os.walk(target_path)])
        if file_count > 0:
            print(f"Data already exists at {target_path}")
            print(f"Skipping download. Delete the directory if you want to re-download.")
            return target_path
    
    # Official Bulk Download URL
    url = "https://clinicaltrials.gov/AllPublicXML.zip"
    zip_path = "AllPublicXML.zip"
    
    try:
        # Check disk space (3 GB ZIP + ~10 GB extracted = need at least 15 GB free)
        try:
            stat = os.statvfs(output_dir if os.path.exists(output_dir) else ".")
            free_space_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            if free_space_gb < 15:
                raise Exception(f"Insufficient disk space: {free_space_gb:.1f} GB available (need ~15 GB)")
            print(f"Available disk space: {free_space_gb:.1f} GB")
        except Exception as e:
            print(f"Warning: Could not check disk space - {e}")
        
        # Download the ZIP file using streaming
        print(f"Downloading all study records to {zip_path}...")
        
        # Get the file size using a HEAD request
        try:
            head_response = requests.head(url, allow_redirects=True, timeout=10)
            total_size = int(head_response.headers.get('content-length', 0))
        except:
            total_size = 0
        
        if total_size > 0:
            total_size_gb = total_size / (1024**3)
            print(f"Total file size: {total_size_gb:.2f} GB")
        
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            # Fallback to GET response content-length if HEAD didn't work
            if total_size == 0:
                total_size = int(r.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Download Progress") as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
                            pbar.update(len(chunk))
        
        # Verify ZIP file integrity
        print("Verifying ZIP file integrity...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                bad_file = zip_ref.testzip()
                if bad_file:
                    raise Exception(f"Corrupted file in ZIP: {bad_file}")
        except zipfile.BadZipFile:
            raise Exception("Downloaded ZIP file is corrupted")
        
        # Create the target path if it doesn't exist
        if not os.path.exists(target_path):
            os.makedirs(target_path)
            print(f"Created directory: {target_path}")
        
        # Extract the files into the date-based subdirectory
        print(f"Extracting study records to {target_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_path)
        
        print("Download and extraction complete.")
        return target_path
    
    except Exception as e:
        print(f"ERROR: {e}")
        # Clean up partial data on failure
        if os.path.exists(zip_path):
            print(f"Cleaning up incomplete ZIP file...")
            os.remove(zip_path)
        if os.path.exists(target_path):
            try:
                if not any(os.scandir(target_path)):  # Directory is empty
                    os.rmdir(target_path)
                    print(f"Cleaned up empty directory {target_path}")
            except:
                pass
        raise
    
    finally:
        # Always clean up ZIP file
        if os.path.exists(zip_path):
            os.remove(zip_path)

if __name__ == "__main__":
    download_all_studies()