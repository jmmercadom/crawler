# Gaceta Oficial Crawler

Extract edition data from Gaceta Oficial HTML index files and output as JSON.

## Installation

```bash
uv sync
```

## Usage

```bash
python extract_editions.py -in samples/index-2025-11-07.html
```

Options:
- `-in` - Input HTML file (required)
- `-out` - Output JSON file (optional, defaults to `output/index-{date}-editions.json`)
- `LOG_LEVEL=DEBUG` - Enable debug logging

## Output Format

```json
[
  {
    "number": "1234",
    "type": "Ordinaria",
    "published_date": "2025-11-07",
    "administration": "Gobierno Nacional"
  }
]
```
