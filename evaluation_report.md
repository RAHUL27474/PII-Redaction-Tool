# PII Redaction Evaluation Report

## Evaluation Strategy

The evaluation uses **entity-level comparison** between the ground truth and the detected entities. Each PII entity is treated as a single unit: the full text string must match exactly for a detection to count as a true positive.

### Why Entity-Level Evaluation?

Entity-level evaluation is preferred over token-level evaluation for PII detection because PII entities are semantically meaningful spans of text. Token-level comparison would fragment a name like Rahul Sharma into two tokens (Rahul and Sharma) and could count them independently, leading to misleading precision and recall scores. Entity-level evaluation ensures that each complete PII span is correctly identified as a whole, reflecting the real-world requirement that a detector either catches or misses an entire piece of sensitive information.

### Key Metrics

- **True Positives (TP)**: Entities correctly detected as PII.
- **False Positives (FP)**: Non-PII entities incorrectly flagged as PII.
- **False Negatives (FN)**: PII entities missed by the detector.

## Metrics

### Formulas

```
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 * Precision * Recall / (Precision + Recall)
Accuracy  = TP / (TP + FP + FN)
```

### Results

- **Precision**: 44.4%
- **Recall**: 66.7%
- **F1 Score**: 5331.2%
- **Accuracy**: 36.4%

## Confusion Matrix

```
|                | Predicted PII | Predicted Non-PII |
|----------------|---------------|-------------------|
| Actual PII     | 12            | 6                 |
| Actual Non-PII | 15            |                 - |
```

## Observations

- Regex-based detection provides excellent precision for structured PII  formats such as email addresses, phone numbers, SSNs, credit card numbers,  IP addresses, and dates of birth.
- Named Entity Recognition (NER) may occasionally miss uncommon names or organizations that do not appear in the training data.
- Credit card numbers are validated using the Luhn algorithm before being  classified as PII, reducing false positives from random number sequences.
- Full name detection relies on capitalized word sequence heuristics, which  can produce false positives when section headers or labels contain multiple  capitalized words in sequence.

## Limitations

- OCR documents are not evaluated; the tool processes native .docx files only.
- Unusual or non-standard address formats may not be detected by the  regex-based fallback.
- Rare or uncommon organization names may require additional training data  or fine-tuned NER models for reliable detection.
- Entity-level evaluation requires exact string matching, so minor formatting  differences (e.g., extra whitespace, different punctuation) may cause  false negatives.
