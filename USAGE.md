# Process Data Usage

## Basic Usage

Process all studies and generate all tables:
```bash
python process.py
```

## Test Mode

Process only the first 100 studies:
```bash
python process.py --test
```

Process the first 500 studies:
```bash
python processpy --test --test-count 500
```

## Selective Table Generation

Generate only specific tables using the `--tables` option:

```bash
# Generate only studies and text tables (good for ML features + NLP text processing)
python process.py --tables studies text

# Generate only studies and conditions (for condition-based features)
python process.py --tables studies conditions

# Generate everything except text (to save time/space)
python process.py --tables studies conditions interventions collaborators locations

# Interventions only with conditions
python process.py --tables studies interventions
```

## Available Tables

- **studies**: Main study table (nct_id, phase, status, enrollment, dates, etc.) - ~26 columns
- **text**: Text fields (official_title, brief_summary, detailed_description) - For NLP processing
- **conditions**: One-to-many: conditions per study
- **interventions**: One-to-many: intervention types per study
- **collaborators**: One-to-many: collaborating organizations per study
- **locations**: One-to-many: facility locations with addresses per study

## Output Files

Default output prefix is `studies.csv`. Files are generated with date suffixes (DDMMYYYY) or `_test` suffix in test mode:

```
studies_15012026.csv
studies_text_15012026.csv
studies_conditions_15012026.csv
studies_interventions_15012026.csv
studies_collaborators_15012026.csv
studies_locations_15012026.csv
```

## Custom Output Directory

Specify a custom data directory:
```bash
python process.py --data-dir /path/to/data
```

## Help

```bash
python process.py --help
```
