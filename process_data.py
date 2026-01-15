import xml.etree.ElementTree as ET
import pandas as pd
import os
from pathlib import Path
from tqdm import tqdm
from typing import List, Dict, Optional
from datetime import datetime

def extract_text(element, tag: str, default: str = "") -> str:
    """Safely extract text from an XML element."""
    try:
        elem = element.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
    except:
        pass
    return default

def extract_text_with_attr(element, tag: str, attr: str = None, default: str = "") -> str:
    """Safely extract text from an XML element and optionally its attribute."""
    try:
        elem = element.find(tag)
        if elem is not None:
            if attr:
                attr_value = elem.get(attr)
                if attr_value:
                    return attr_value.strip()
                return default
            elif elem.text:
                return elem.text.strip()
    except:
        pass
    return default

def extract_list(element, tag: str) -> str:
    """Extract multiple elements and join them."""
    try:
        items = [item.text.strip() for item in element.findall(tag) if item.text]
        return "; ".join(items) if items else ""
    except:
        return ""

def parse_clinical_trial(xml_file: str) -> Optional[Dict]:
    """Parse a single clinical trial XML file and extract relevant fields."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Helper function to safely check if element exists
        def elem_exists(element):
            return element is not None
        
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
            'study_type': extract_text(study_design_info, 'study_type') if elem_exists(study_design_info) else extract_text(root, 'study_type'),
            'phase': extract_text(root, 'phase'),
            'overall_status': extract_text(root, 'overall_status'),
            'why_stopped': extract_text(root, 'why_stopped'),
            
            # Dates
            'start_date': extract_text(root, 'start_date'),
            'completion_date': extract_text(root, 'completion_date'),
            'primary_completion_date': extract_text(root, 'primary_completion_date'),
            
            # Enrollment
            'enrollment': extract_text(root, 'enrollment'),
            'enrollment_type': extract_text_with_attr(root, 'enrollment', 'type'),
            
            # Study Design Details
            'allocation': extract_text(study_design_info, 'allocation') if elem_exists(study_design_info) else "",
            'intervention_model': extract_text(study_design_info, 'intervention_model') if elem_exists(study_design_info) else "",
            'primary_purpose': extract_text(study_design_info, 'primary_purpose') if elem_exists(study_design_info) else "",
            'masking': extract_text(study_design_info, 'masking') if elem_exists(study_design_info) else "",
            
            # Oversight
            'has_dmc': extract_text(oversight_info, 'has_dmc') if elem_exists(oversight_info) else "",
            'is_fda_regulated_drug': extract_text(oversight_info, 'is_fda_regulated_drug') if elem_exists(oversight_info) else "",
            'is_fda_regulated_device': extract_text(oversight_info, 'is_fda_regulated_device') if elem_exists(oversight_info) else "",
            
            # Sponsor Information
            'lead_sponsor': extract_text(sponsors, 'lead_sponsor') if elem_exists(sponsors) else "",
            'collaborators': extract_list(sponsors, 'collaborator') if elem_exists(sponsors) else "",
            'source': extract_text(root, 'source'),
            
            # Study Population
            'gender': extract_text(eligibility, 'gender') if elem_exists(eligibility) else "",
            'minimum_age': extract_text(eligibility, 'minimum_age') if elem_exists(eligibility) else "",
            'maximum_age': extract_text(eligibility, 'maximum_age') if elem_exists(eligibility) else "",
            'accepts_healthy_volunteers': extract_text(eligibility, 'accepts_healthy_volunteers') if elem_exists(eligibility) else "",
            
            # Conditions
            'conditions': extract_list(root, 'condition'),
            
            # Interventions
            'interventions': extract_list(root, 'intervention_type'),
            
            # Number of Arms
            'number_of_arms': extract_text(root, 'number_of_arms'),
            
            # Brief Summary
            'brief_summary': extract_text(brief_summary, 'textblock') if elem_exists(brief_summary) else "",
            
            # Detailed Description
            'detailed_description': extract_text(detailed_description, 'textblock') if elem_exists(detailed_description) else "",
        }
        
        return data
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return None

def find_xml_files(data_dir: str, test_mode: bool = False, test_count: int = 100) -> List[str]:
    """Find all XML files in the data directory."""
    xml_files = []
    
    # Find the latest data directory if data_dir is 'data'
    if data_dir == 'data':
        data_path = Path(data_dir)
        if not data_path.exists():
            raise FileNotFoundError(f"Data directory '{data_dir}' not found")
        
        # Get subdirectories sorted by date (newest first), excluding 'output'
        subdirs = sorted([d for d in data_path.iterdir() if d.is_dir() and d.name.startswith('data_')], 
                        key=lambda x: x.name, reverse=True)
        
        if not subdirs:
            raise FileNotFoundError(f"No data subdirectories found in '{data_dir}'")
        
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
                   test_mode: bool = False, test_count: int = 100):
    """Process all clinical trial XML files and save to CSV."""
    
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
    
    # Create DataFrame
    df = pd.DataFrame(studies)
    
    # Save to CSV
    output_path = f"{output_file.replace('.csv', '')}_{'test' if test_mode else datetime.now().strftime('%d%m%Y')}.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\nProcessing complete!")
    print(f"Processed {len(df)} studies")
    print(f"Saved to {output_path}")
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    return df

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process clinical trial XML files into CSV")
    parser.add_argument("--data-dir", default="data", help="Path to data directory containing XML files")
    parser.add_argument("--output", default="studies.csv", help="Output CSV file name")
    parser.add_argument("--test", action="store_true", help="Test mode: only process first N studies")
    parser.add_argument("--test-count", type=int, default=100, help="Number of studies to process in test mode")
    
    args = parser.parse_args()
    
    df = process_studies(
        data_dir=args.data_dir,
        output_file=args.output,
        test_mode=args.test,
        test_count=args.test_count
    )
