import requests
import json
import datetime
import pandas as pd


def get_studies(search_expr):
    '''
    Pulls studies from ctgov API based on user input search expression.

    Ensure that the search expression is not too generic so that the API does not crash.

    Expressions like "Cancer" are generic. Be more specific such as "Head OR Neck AND Cancer".
    '''
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "pageSize": 500, 
        "query.term": search_expr  
    }    
    
    all_studies = []
    # Set page token to iterate through >500 studies for search expresion
    next_page_token = None
    
    while True:
        # Set limit @ 10 000 studies before API gets killed
        if len(all_studies) > 10000:
            ValueError("Search Expression is too generic, please specify the query")
        
        if next_page_token:
            params["pageToken"] = next_page_token
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        all_studies.extend(data.get("studies", []))
        next_page_token = data.get("nextPageToken")

        if not next_page_token:
            break
    
    # returns as a json-type list
    return(all_studies)

get_st