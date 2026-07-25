# PII Redaction Tool

A production-quality Python tool for detecting and redacting personally identifiable information (PII) from Microsoft Word documents. The tool replaces sensitive data with realistic fake values while maintaining consistent replacements throughout the entire document.

## Project Overview

This tool processes `.docx` files to identify and replace the following PII types:

- **Full Names** — Person names detected via NLP or heuristics
- **Email Addresses** — Standard email patterns
- **Phone Numbers** — Various phone number formats
- **Company Names** — Organization names detected via NLP or heuristics
- **Physical/Mailing Addresses** — Street addresses detected via NLP or heuristics
- **Social Security Numbers (SSNs)** — US SSN format (XXX-XX-XXXX)
- **Credit Card Numbers** — 13-16 digit numbers validated with Luhn algorithm
- **Date of Birth** — Common date formats (MM/DD/YYYY, DD-MM-YYYY, etc.)
- **IP Addresses** — IPv4 addresses

## Installation

1. Clone the repository or extract the project files.
2. Navigate to the project directory:

```bash
cd project
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. (Optional) Download the spaCy English model for improved named entity recognition:

```bash
python -m spacy download en_core_web_sm
```

## Dependencies

| Library | Purpose |
|---------|---------|
| `python-docx` | Reading and writing .docx files |
| `faker` | Generating realistic fake values |
| `regex` | Advanced regular expression patterns |
| `spacy` | Named Entity Recognition (optional) |
| `presidio-analyzer` | PII detection engine (optional) |
| `presidio-anonymizer` | PII anonymization (optional) |
| `scikit-learn` | Evaluation metrics |

## How to Run

Run the redaction tool from the command line:

```bash
python src/redact.py input/sample.docx output/redacted.docx
```

Arguments:

| Argument | Description |
|----------|-------------|
| `input_path` | Path to the input .docx file |
| `output_path` | Path where the redacted .docx will be saved |

To generate an evaluation report (requires a ground truth JSON file):

```bash
python src/evaluation.py output/redacted.docx ground_truth.json
```

## Detection Approach

The tool uses a layered detection strategy:

1. **Regex-based detection** for structured patterns:
   - Email addresses
   - Phone numbers (international and domestic formats)
   - Credit card numbers (with Luhn validation)
   - SSNs (XXX-XX-XXXX)
   - Dates of birth (multiple formats)
   - IPv4 addresses

2. **NLP-based detection** (when available):
   - spaCy NER for names, organizations, and locations
   - Microsoft Presidio for advanced PII entity detection

3. **Heuristic fallback** when NLP libraries are unavailable:
   - Capitalized word sequences for names
   - Known company keyword patterns for organizations
   - Street number + direction patterns for addresses

Each detection method runs in sequence, and results are deduplicated to avoid double-counting overlapping matches.

## Replacement Strategy

1. A global `mapping.json` file stores the mapping between original values and their fake replacements.
2. When a PII entity is detected, the tool checks if it already has a replacement in the mapping.
3. If a mapping exists, the consistent fake value is reused.
4. If no mapping exists, a new fake value is generated using Faker and stored in the mapping.
5. This ensures that every occurrence of the same original value is replaced with the same fake value throughout the document.

## Tradeoffs

- **Regex vs NLP**: Regex provides precise, deterministic matching for structured data (emails, SSNs, credit cards). NLP models are better for unstructured data (names, addresses) but may have higher false positive rates.
- **Consistency vs randomness**: The mapping dictionary ensures consistent replacements but means the same original always maps to the same fake, which could make the redacted document look less natural if the same fake name appears frequently.
- **Performance**: Running multiple detection passes (regex + NLP) adds overhead but improves coverage.

## Known Limitations

- Addresses detection via heuristic fallback may miss non-standard formats.
- Names with initials or suffixes (e.g., "J.R. Smith") may not be detected reliably.
- Credit cards that pass Luhn validation but are not randomly generated may still be flagged even if they are not real.
- The tool processes text runs within paragraphs and cells but may miss PII in complex document elements like text boxes or embedded objects.
- Presidio/spaCy are optional; without them, NLP-based entity detection falls back to simpler heuristics.

## Future Improvements

- Support for additional document formats (PDF, ODT).
- Configurable detection rules via a YAML configuration file.
- Batch processing of multiple documents.
- Context-aware name disambiguation (e.g., distinguishing between first names and last names).
- Integration with Presidio's annotator API for more accurate entity detection.
- Support for additional PII types (passport numbers, driver's licenses, bank account numbers).
- Web UI for reviewing and approving redactions before finalizing.

## Flask Web Application

The project can be deployed as a Flask web application on Render. The web UI provides a drag-and-drop upload form, processing progress indicator, and a one-click download for the redacted document.

### Web Application Structure

```
project/
├── app.py                         ← Flask application
├── templates/
│   └── index.html                 ← HTML template
├── static/
│   └── style.css                  ← Custom styles
├── Procfile                       ← Render build config
├── src/                           ← Existing redaction logic (unchanged)
├── input/                         ← Temp upload directory
├── output/                        ← Processed output directory
├── mapping.json                   ← PII→fake mapping
├── requirements.txt
└── README.md
```

### Deployment on Render

1. Push the project to a GitHub repository.
2. Create a new **Web Service** on Render.
3. Connect the repository.
4. Configure the following settings:

| Setting | Value |
|---------|-------|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Python Version** | 3.10 or higher |

5. Set the environment variable `SECRET_KEY` to a secure random value in Render's environment settings.
6. Deploy.

Render will automatically detect the `Procfile` and use the specified `web` process type. The application listens on `0.0.0.0` on the port provided by Render's `$PORT` environment variable.

### Running Locally

```bash
pip install -r requirements.txt
python app.py
```

The app runs at `http://localhost:5000`.
# PII-Redaction-Tool