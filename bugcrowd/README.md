# 🐞 Bugcrowd Scope Extractor

> Automated in-scope target extraction from public Bugcrowd engagements.  
> Built for security researchers, bug hunters, and recon automation workflows.

---

## 📌 Overview

**Bugcrowd Scope Extractor** is a Python-based automation tool that collects and extracts in-scope targets from publicly available Bugcrowd bug bounty engagements.

The script automatically:

- Fetches bug bounty engagements (paginated)
- Identifies the latest changelog UUID
- Retrieves engagement scope JSON
- Extracts in-scope targets
- Separates normal and wildcard targets
- Deduplicates and saves results into structured files

This tool is designed to accelerate reconnaissance preparation and target enumeration.

---

## ⚙️ Features

- ✅ Automated engagement discovery  
- ✅ UUID extraction from engagement pages  
- ✅ Scope JSON parsing  
- ✅ Out-of-scope filtering  
- ✅ Wildcard detection (`*.example.com`)  
- ✅ Target normalization (HTTPS formatted)  
- ✅ Deduplication  
- ✅ Error handling & timeout protection  
- ✅ Respectful request delays  

---

## 📂 Output Files

After execution, the script generates:

| File | Description |
|------|------------|
| `engagements.txt` | List of engagement slugs |
| `inscope.txt` | Normal in-scope targets |
| `wildcard.txt` | Wildcard targets |

All targets are normalized and saved in HTTPS format.

---

## 🧩 Requirements

- Python 3.8+
- `requests` library

Install dependencies:

```bash
pip install requests
```

---

## 🚀 Usage

Run the script:

```bash
python bugcrowd.py
```

---

## 🔎 Execution Flow

1. Load engagements from `engagements.txt` (if available)
2. Otherwise fetch engagements directly from Bugcrowd
3. Extract latest changelog UUID per engagement
4. Retrieve and parse scope JSON
5. Filter only valid in-scope targets
6. Classify into:
   - Normal targets
   - Wildcard targets
7. Save results
8. Display final summary report

---

## 🧠 Processing Logic

### 1️⃣ Engagement Discovery

Data is fetched from:

```
/engagements.json
```

Filtered by:

- `category = bug_bounty`
- `sort_by = promoted`
- `sort_direction = desc`

---

### 2️⃣ UUID Extraction

The script parses engagement HTML pages and extracts the latest changelog UUID using a regex pattern:

```
/engagements/{slug}/changelog/{uuid}
```

---

### 3️⃣ Scope Extraction

The script requests:

```
/engagements/{slug}/changelog/{uuid}.json
```

Then:

- Reads `data.scope`
- Skips out-of-scope groups
- Extracts valid target URIs
- Normalizes URLs
- Separates wildcard and normal targets
- Deduplicates results

---

## 📊 Final Summary Output

After execution, the script prints:

- Total engagements processed
- Successful extractions
- Failed extractions
- Total normal targets
- Total wildcard targets
- Total unique targets

---

## ⚠️ Important Notes

- This tool processes only publicly accessible data.
- Built with request delays to reduce server load.
- Always follow Bugcrowd’s Terms of Service.
- Respect each program’s rules before testing any target.

---

## 🛡 Disclaimer

This project is intended for **educational and authorized security research purposes only**.

Users are fully responsible for ensuring compliance with:

- Applicable laws
- Bugcrowd platform policies
- Individual bug bounty program rules

The author assumes no responsibility for misuse or unauthorized activity.

---

## 👤 Author

**SecAnalysts**  
Security Research & Automation  

---

## ☕ Support / Donation

If you find this project useful and would like to support my work,  
you can donate BTC to help support my child’s education:

BTC Address:
```
1sAXERLyPhg4Fg4rkhuRQfm9eek2NJo6V
```

Your support is greatly appreciated 🙏
