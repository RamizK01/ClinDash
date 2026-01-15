import xml.etree.ElementTree as ET
import pandas as pd
import os
import logging
from pathlib import Path
from tqdm import tqdm
from typing import List, Dict, Optional
from datetime import datetime

# Optional: Set up logging for debugging
logging.basicConfig(level=logging.WARNING)  # Change to DEBUG for verbose output
logger = logging.getLogger(__name__)

def extract_text(element, tag: str, attr: str = None, default: str = "") -> str:
    """Safely extract text from an XML element or its attribute."""
    try:
        if element is None:
            return default
        elem = element.find(tag)
        if elem is not None:
            if attr:
                attr_value = elem.get(attr)
                if attr_value:
                    return attr_value.strip()
            elif elem.text:
                return elem.text.strip()
    except (AttributeError, TypeError) as e:
        logger.debug(f"Error extracting {tag}: {e}")
    return default

def extract_list(element, tag: str) -> List[str]:
    """Extract multiple elements and return as list."""
    try:
        if element is None:
            return []
        items = [item.text.strip() for item in element.findall(tag) if item.text]
        return items
    except (AttributeError, TypeError) as e:
        logger.debug(f"Error extracting list {tag}: {e}")
        return []

def extract_locations(root) -> List[Dict]:
    """Extract location/facility information."""
    locations = []
    try:
        for location in root.findall('location'):
            loc_data = {}
            
            # Facility information
            facility = location.find('facility')
            if facility is not None:
                loc_data['facility_name'] = extract_text(facility, 'name')
                
                # Address information
                address = facility.find('address')
                if address is not None:
                    # Extract city and state (they may contain geolocation codes at the end)
                    city = extract_text(address, 'city').strip()
                    state = extract_text(address, 'state').strip()
                    
                    # Remove trailing numbers (geolocation codes)
                    city_clean = ' '.join(city.split()[:-1]) if city and city[-1].isdigit() else city
                    state_clean = ' '.join(state.split()[:-1]) if state and state[-1].isdigit() else state
                    
                    loc_data['city'] = city_clean
                    loc_data['state'] = state_clean
                    loc_data['country'] = extract_text(address, 'country')
                    loc_data['postal_code'] = extract_text(address, 'zip')
                
                if loc_data.get('facility_name'):  # Only add if we have at least a facility name
                    locations.append(loc_data)
    except (AttributeError, TypeError) as e:
        logger.debug(f"Error extracting locations: {e}")
    return locations

def parse_clinical_trial(xml_file: str) -> Optional[Dict]:
    """Parse a single clinical trial XML file and extract relevant fields."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        id_info = root.find('id_info')
        study_design_info = root.find('study_design_info')
        oversight_info = root.find('oversight_info')
        sponsors = root.find('sponsors')
        eligibility = root.find('eligibility')
        brief_summary = root.find('brief_summary')
        detailed_description = root.find('detailed_description')
        
        # Extract basic information
        data = {
            # IDs
            'nct_id': extract_text(id_info, 'nct_id'),
            'org_study_id': extract_text(id_info, 'org_study_id'),
            
            # Titles
            'brief_title': extract_text(root, 'brief_title'),
            'official_title': extract_text(root, 'official_title'),
            
            # Study Information
            'study_type': extract_text(study_design_info, 'study_type') if study_design_info is not None else extract_text(root, 'study_type'),
            'phase': extract_text(root, 'phase'),
            'overall_status': extract_text(root, 'overall_status'),
            'why_stopped': extract_text(root, 'why_stopped'),
            
            # Dates
            'start_date': extract_text(root, 'start_date'),
            'completion_date': extract_text(root, 'completion_date'),
            'primary_completion_date': extract_text(root, 'primary_completion_date'),
            
            # Enrollment
            'enrollment': extract_text(root, 'enrollment'),
            'enrollment_type': extract_text(root, 'enrollment', 'type'),
            
            # Study Design Details
            'allocation': extract_text(study_design_info, 'allocation') if study_design_info is not None else "",
            'intervention_model': extract_text(study_design_info, 'intervention_model') if study_design_info is not None else "",
            'primary_purpose': extract_text(study_design_info, 'primary_purpose') if study_design_info is not None else "",
            'masking': extract_text(study_design_info, 'masking') if study_design_info is not None else "",
            
            # Oversight
            'has_dmc': extract_text(oversight_info, 'has_dmc') if oversight_info is not None else "",
            'is_fda_regulated_drug': extract_text(oversight_info, 'is_fda_regulated_drug') if oversight_info is not None else "",
            'is_fda_regulated_device': extract_text(oversight_info, 'is_fda_regulated_device') if oversight_info is not None else "",
            
            # Sponsor Information
            'lead_sponsor': extract_text(sponsors, 'lead_sponsor') if sponsors is not None else "",
            'collaborators': extract_list(sponsors, 'collaborator') if sponsors is not None else [],
            'source': extract_text(root, 'source'),
            
            # Study Population
            'gender': extract_text(eligibility, 'gender') if eligibility is not None else "",
            'minimum_age': extract_text(eligibility, 'minimum_age') if eligibility is not None else "",
            'maximum_age': extract_text(eligibility, 'maximum_age') if eligibility is not None else "",
            'accepts_healthy_volunteers': extract_text(eligibility, 'accepts_healthy_volunteers') if eligibility is not None else "",
            
            # Conditions (as list)
            'conditions': extract_list(root, 'condition'),
            
            # Interventions (as list)
            'interventions': extract_list(root, 'intervention_type'),
            
            # Locations (as list of dicts)
            'locations': extract_locations(root),
            
            # Number of Arms
            'number_of_arms': extract_text(root, 'number_of_arms'),
            
            # Brief Summary
            'brief_summary': extract_text(brief_summary, 'textblock') if brief_summary is not None else "",
            
            # Detailed Description
            'detailed_description': extract_text(detailed_description, 'textblock') if detailed_description is not None else "",
        }
        
        return data
    except ET.ParseError as e:
        logger.error(f"XML parse error in {xml_file}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing {xml_file}: {e}")
        return None

def find_xml_files(data_dir: str, test_mode: bool = False, test_count: int = 100) -> List[str]:
    """Find all XML files in the data directory."""
    xml_files = []
    
    # Find the latest data directory if data_dir is 'data'
    if data_dir == 'data':
        data_path = Path(data_dir) / 'xml'
        if not data_path.exists():
            raise FileNotFoundError(f"Data directory '{data_path}' not found")
        
        # Get subdirectories sorted by date (newest first), excluding 'output'
        subdirs = sorted([d for d in data_path.iterdir() if d.is_dir() and d.name.startswith('data_')], 
                        key=lambda x: x.name, reverse=True)
        
        if not subdirs:
            raise FileNotFoundError(f"No data subdirectories found in '{data_path}'")
        
        latest_dir = subdirs[0]
        print(f"Using latest data directory: {latest_dir.name}")
    else:
        latest_dir = Path(data_dir)
    
    # Recursively find all XML files
    for xml_file in sorted(latest_dir.rglob("*.xml")):
        xml_files.append(str(xml_file))
        if test_mode and len(xml_files) >= test_count:
            break
    
    return xml_files

def process_studies(data_dir: str = "data", output_file: str = "studies.csv", 
                   test_mode: bool = False, test_count: int = 100,
                   tables: List[str] = None):
    """Process all clinical trial XML files and save to normalized CSVs.
    
    Args:
        data_dir: Path to data directory
        output_file: Output CSV file name prefix
        test_mode: Whether to run in test mode
        test_count: Number of studies to process in test mode
        tables: List of tables to generate. Options: 'studies', 'conditions', 'interventions', 
                'collaborators', 'locations', 'text'. If None, all are generated.
    """
    
    # Default to all tables if not specified
    if tables is None:
        tables = ['studies', 'conditions', 'interventions', 'collaborators', 'locations', 'text']
    
    print(f"Finding XML files in {data_dir}...")
    xml_files = find_xml_files(data_dir, test_mode=test_mode, test_count=test_count)
    
    if not xml_files:
        raise FileNotFoundError("No XML files found")
    
    print(f"Found {len(xml_files)} XML files")
    if test_mode:
        print(f"TEST MODE: Processing {test_count} studies")
    
    # Parse all XML files
    studies = []
    for xml_file in tqdm(xml_files, desc="Processing studies"):
        study_data = parse_clinical_trial(xml_file)
        if study_data:
            studies.append(study_data)
    
    # Create main studies DataFrame (without list columns)
    df_studies = pd.DataFrame(studies)
    
    # Extract text fields into separate table
    text_data = []
    if 'text' in tables:
        for idx, row in df_studies.iterrows():
            text_data.append({
                'nct_id': row['nct_id'],
                'official_title': row['official_title'],
                'brief_summary': row['brief_summary'],
                'detailed_description': row['detailed_description']
            })
    
    # Extract conditions into separate table
    conditions_data = []
    if 'conditions' in tables:
        for idx, row in df_studies.iterrows():
            nct_id = row['nct_id']
            for condition in row['conditions']:
                conditions_data.append({'nct_id': nct_id, 'condition': condition})
    
    # Extract interventions into separate table
    interventions_data = []
    if 'interventions' in tables:
        for idx, row in df_studies.iterrows():
            nct_id = row['nct_id']
            for intervention in row['interventions']:
                interventions_data.append({'nct_id': nct_id, 'intervention_type': intervention})
    
    # Extract collaborators into separate table
    collaborators_data = []
    if 'collaborators' in tables:
        for idx, row in df_studies.iterrows():
            nct_id = row['nct_id']
            for collaborator in row['collaborators']:
                collaborators_data.append({'nct_id': nct_id, 'collaborator': collaborator})
    
    # Extract locations into separate table
    locations_data = []
    if 'locations' in tables:
        for idx, row in df_studies.iterrows():
            nct_id = row['nct_id']
            for location in row['locations']:
                location['nct_id'] = nct_id
                locations_data.append(location)
    
    # Create DataFrames for each table
    df_text = pd.DataFrame(text_data) if text_data else pd.DataFrame()
    df_conditions = pd.DataFrame(conditions_data) if conditions_data else pd.DataFrame()
    df_interventions = pd.DataFrame(interventions_data) if interventions_data else pd.DataFrame()
    df_collaborators = pd.DataFrame(collaborators_data) if collaborators_data else pd.DataFrame()
    df_locations = pd.DataFrame(locations_data) if locations_data else pd.DataFrame()
    
    # Remove text and list columns from main studies table
    cols_to_drop = ['conditions', 'interventions', 'collaborators', 'locations', 
                    'official_title', 'brief_summary', 'detailed_description']
    df_studies = df_studies.drop(columns=[col for col in cols_to_drop if col in df_studies.columns])
    
    # Generate output file names and directory
    base_name = output_file.replace('.csv', '')
    if test_mode:
        suffix = '_test'
        csv_output_dir = Path('data') / 'csv' / f"test_{test_count}"
    else:
        date_str = datetime.now().strftime("%d%m%Y")
        suffix = f"_{date_str}"
        csv_output_dir = Path('data') / 'csv' / f"data_{date_str}"
    
    csv_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all CSVs
    files_saved = {}
    
    if 'studies' in tables:
        studies_path = csv_output_dir / f"{base_name}_{suffix}.csv"
        df_studies.to_csv(studies_path, index=False)
        files_saved['studies'] = (str(studies_path), df_studies.shape)
    
    if 'text' in tables and not df_text.empty:
        text_path = csv_output_dir / f"{base_name}_text_{suffix}.csv"
        df_text.to_csv(text_path, index=False)
        files_saved['text'] = (str(text_path), df_text.shape)
    
    if 'conditions' in tables and not df_conditions.empty:
        conditions_path = csv_output_dir / f"{base_name}_conditions_{suffix}.csv"
        df_conditions.to_csv(conditions_path, index=False)
        files_saved['conditions'] = (str(conditions_path), df_conditions.shape)
    
    if 'interventions' in tables and not df_interventions.empty:
        interventions_path = csv_output_dir / f"{base_name}_interventions_{suffix}.csv"
        df_interventions.to_csv(interventions_path, index=False)
        files_saved['interventions'] = (str(interventions_path), df_interventions.shape)
    
    if 'collaborators' in tables and not df_collaborators.empty:
        collaborators_path = csv_output_dir / f"{base_name}_collaborators_{suffix}.csv"
        df_collaborators.to_csv(collaborators_path, index=False)
        files_saved['collaborators'] = (str(collaborators_path), df_collaborators.shape)
    
    if 'locations' in tables and not df_locations.empty:
        locations_path = csv_output_dir / f"{base_name}_locations_{suffix}.csv"
        df_locations.to_csv(locations_path, index=False)
        files_saved['locations'] = (str(locations_path), df_locations.shape)
    
    # Print summary
    print(f"\n{'=' * 80}")
    print("Processing complete!")
    print(f"{'=' * 80}")
    for table_name, (path, shape) in files_saved.items():
        print(f"{table_name:20s} → {path:40s} ({shape[0]:6d} rows × {shape[1]:2d} cols)")
    
    return {
        'studies': df_studies,
        'text': df_text,
        'conditions': df_conditions,
        'interventions': df_interventions,
        'collaborators': df_collaborators,
        'locations': df_locations
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process clinical trial XML files into normalized CSVs")
    parser.add_argument("--data-dir", default="data", help="Path to data directory containing XML files")
    parser.add_argument("--output", default="studies.csv", help="Output CSV file name prefix")
    parser.add_argument("--test", action="store_true", help="Test mode: only process first N studies")
    parser.add_argument("--test-count", type=int, default=100, help="Number of studies to process in test mode")
    parser.add_argument("--tables", nargs='+',
                       choices=['studies', 'conditions', 'interventions', 'collaborators', 'locations', 'text'],
                       help="Specify which tables to generate. Default: all tables")
    
    args = parser.parse_args()
    
    dfs = process_studies(
        data_dir=args.data_dir,
        output_file=args.output,
        test_mode=args.test,
        test_count=args.test_count,
        tables=args.tables
    )