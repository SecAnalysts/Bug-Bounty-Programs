import requests
import re
import time
import os
import json
from urllib.parse import urlparse

BASE = "https://bugcrowd.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://bugcrowd.com/"
}

ENG_FILE = "engagements.txt"
INSCOPE_FILE = "inscope.txt"
WILDCARD_FILE = "wildcard.txt"

normal_targets = set()
wildcard_targets = set()


def get_engagements_from_web():
    print("[+] Fetching engagements from web...")
    all_slugs = []

    for page in range(1, 10):  # Page 1 sampai 9
        print(f"   -> Page {page}")
        url = f"{BASE}/engagements.json"
        params = {
            "category": "bug_bounty",
            "sort_by": "promoted",
            "sort_direction": "desc",
            "page": page
        }

        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as e:
            print(f"   [!] Error fetching page {page}: {e}")
            continue
        except json.JSONDecodeError:
            print(f"   [!] Invalid JSON on page {page}")
            continue

        engagements = data.get("engagements", [])
        if not engagements:
            print(f"   [!] No engagements found on page {page}")
            break

        for e in engagements:
            brief = e.get("briefUrl")
            if brief:
                slug = brief.strip("/").split("/")[-1]
                all_slugs.append(slug)

        time.sleep(1)  # Increased delay to be respectful

    all_slugs = sorted(set(all_slugs))

    with open(ENG_FILE, "w", encoding="utf-8") as f:
        for slug in all_slugs:
            f.write(slug + "\n")

    print(f"[✔] Saved {len(all_slugs)} engagements to {ENG_FILE}")
    return all_slugs


def load_engagements():
    if os.path.exists(ENG_FILE):
        print("[+] Loading engagements from file...")
        with open(ENG_FILE, "r", encoding="utf-8") as f:
            slugs = [line.strip() for line in f if line.strip()]
        print(f"[✔] Loaded {len(slugs)} engagements from {ENG_FILE}")
        return slugs
    else:
        print(f"[!] File {ENG_FILE} not found.")
        print("[+] Fetching engagements from web instead...")
        return get_engagements_from_web()


def get_latest_uuid(slug):
    url = f"{BASE}/engagements/{slug}"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        content = r.text
        
        # Cari UUID dalam halaman
        pattern = rf'/engagements/{re.escape(slug)}/changelog/([a-f0-9]{{8}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{12}})'
        matches = re.findall(pattern, content)
        
        if matches:
            return matches[0]
        
        return None
        
    except requests.RequestException as e:
        print(f"   [!] Error fetching {slug}: {e}")
        return None


def extract_scope(slug):
    uuid = get_latest_uuid(slug)
    if not uuid:
        print(f"   [!] No UUID found for: {slug}")
        return

    api_url = f"{BASE}/engagements/{slug}/changelog/{uuid}.json"
    
    print(f"   -> Fetching JSON from {api_url}")
    
    try:
        r = requests.get(api_url, headers=HEADERS, timeout=15)
        
        if r.status_code == 404:
            print(f"   [!] JSON not found (404) for {slug}")
            return
        
        r.raise_for_status()
        data = r.json()
        
        targets_found = 0
        
        if "data" not in data:
            print(f"   [!] No 'data' key in JSON for {slug}")
            return
        
        if "scope" not in data["data"]:
            print(f"   [!] No 'scope' key in data for {slug}")
            return
        
        scope_groups = data["data"]["scope"]
        
        if not scope_groups:
            print(f"   -> No scope groups found for {slug}")
            return
        
        print(f"   -> Found {len(scope_groups)} scope groups")
        
        for group in scope_groups:
            group_name = group.get("name", "").lower()
            group_in_scope = group.get("inScope", True)
            
            if not group_in_scope:
                print(f"   -> Skipping out of scope group: {group_name}")
                continue
            
            if any(term in group_name for term in ["out of scope", "out-of-scope", "out_of_scope"]):
                print(f"   -> Skipping out of scope group by name: {group_name}")
                continue
            
            targets = group.get("targets", [])
            if not targets:
                continue
            
            print(f"   -> Processing {len(targets)} targets in group: {group_name}")
            
            for target in targets:
                uri = target.get("uri")
                if uri is None:
                    uri = ""
                else:
                    uri = str(uri).strip()
                
                if not uri:
                    target_name = target.get("name", "")
                    if target_name:
                        target_name = str(target_name).strip()
                        if ("." in target_name or "http" in target_name) and len(target_name) > 3:
                            uri = target_name
                
                if not uri:
                    continue
                
                if target.get("in_scope") is False:
                    continue
                
                if uri.startswith("http://") or uri.startswith("https://"):
                    parsed = urlparse(uri)
                    uri = parsed.netloc + parsed.path
                
                uri = uri.rstrip('/')
                
                if not uri or "." not in uri or len(uri) < 4:
                    continue
                
                if any(c in uri for c in ["\n", "\t", "\r", "  "]):
                    continue
                
                full_uri = f"https://{uri}" if not uri.startswith("http") else uri
                
                if "*" in uri:
                    wildcard_targets.add(full_uri)
                    print(f"     -> Added wildcard: {full_uri}")
                else:
                    normal_targets.add(full_uri)
                    print(f"     -> Added normal: {full_uri}")
                
                targets_found += 1
        
        if targets_found > 0:
            print(f"   -> Found {targets_found} in-scope targets")
        else:
            print(f"   -> No in-scope targets found")
        
        return True
        
    except requests.RequestException as e:
        print(f"   [!] Error fetching JSON for {slug}: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"   [!] Invalid JSON for {slug}: {e}")
        return False
    except Exception as e:
        print(f"   [!] Unexpected error for {slug}: {e}")
        return False


def main():
    print("=" * 60)
    print("Bugcrowd Scope Extractor - SecAnalysts")
    print("=" * 60)
    
    # Load engagements from file or fetch from web
    slugs = load_engagements()
    
    if not slugs:
        print("[!] No engagements to process. Exiting.")
        return
    
    print(f"\n[+] Processing {len(slugs)} engagements...")
    
    successful_slugs = 0
    failed_slugs = []
    for i, slug in enumerate(slugs, 1):
        print(f"\n[{i}/{len(slugs)}] Processing: {slug}")
        
        prev_normal = len(normal_targets)
        prev_wildcard = len(wildcard_targets)
        
        try:
            success = extract_scope(slug)
            if not success:
                failed_slugs.append(slug)
        except Exception as e:
            print(f"   [!] Major error for {slug}: {e}")
            failed_slugs.append(slug)
        
        if len(normal_targets) > prev_normal or len(wildcard_targets) > prev_wildcard:
            successful_slugs += 1
        
        time.sleep(0.5)  # Be respectful to the server
    
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    
    if normal_targets:
        with open(INSCOPE_FILE, "w", encoding="utf-8") as f:
            for t in sorted(normal_targets):
                f.write(t + "\n")
        print(f"[✔] Saved {len(normal_targets)} in-scope targets to {INSCOPE_FILE}")
        print("Sample targets (first 10):")
        for t in list(sorted(normal_targets))[:10]:
            print(f"  - {t}")
    
    if wildcard_targets:
        with open(WILDCARD_FILE, "w", encoding="utf-8") as f:
            for t in sorted(wildcard_targets):
                f.write(t + "\n")
        print(f"[✔] Saved {len(wildcard_targets)} wildcard targets to {WILDCARD_FILE}")
        print("Sample wildcards (first 5):")
        for t in list(sorted(wildcard_targets))[:5]:
            print(f"  - {t}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total engagements processed: {len(slugs)}")
    print(f"Successful extractions: {successful_slugs}")
    print(f"Failed extractions: {len(failed_slugs)}")
    
    if failed_slugs:
        print(f"Failed slugs (first 10): {', '.join(failed_slugs[:10])}")
        if len(failed_slugs) > 10:
            print(f"  ... and {len(failed_slugs) - 10} more")
    
    print(f"Normal targets found: {len(normal_targets)}")
    print(f"Wildcard targets found: {len(wildcard_targets)}")
    print(f"Total unique targets: {len(normal_targets) + len(wildcard_targets)}")
    
    if not normal_targets and not wildcard_targets:
        print("\n[!] No targets found.")


if __name__ == "__main__":
    main()