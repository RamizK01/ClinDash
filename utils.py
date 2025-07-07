import requests
import json
import datetime
import pandas as pd


def get_studies(search_expr):
    """
    Pulls studies from ctgov API based on user input search expression.

    Ensure that the search expression is not too generic so that the API does not crash.

    Expressions like "Cancer" are generic. Be more specific such as "Head OR Neck AND Cancer".
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {"pageSize": 500, "query.term": search_expr}

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
    return all_studies


class trials:
    def __init__(self, search_expr):
        """
        Initialize the trials class with a search expression.
        """
        self.search_expr = search_expr
        self.studies = get_studies(search_expr)


def process_studies(studies, type):
    """
    Process the studies to extract relevant information and convert to a pandas DataFrame.
    Specify the type of data to extract: "general" or "location".
    """
    data = pd.json_normalize(studies)

    if type == "general":
        study_df = data[
            [
                "protocolSection.identificationModule.nctId",
                "protocolSection.identificationModule.organization.fullName",
                "protocolSection.sponsorCollaboratorsModule.responsibleParty.type",  #
                "protocolSection.identificationModule.organization.class",  #
                "protocolSection.identificationModule.briefTitle",  #
                "protocolSection.identificationModule.officialTitle",
                "protocolSection.statusModule.overallStatus",
                "protocolSection.statusModule.lastKnownStatus",
                "protocolSection.statusModule.whyStopped",  #
                "protocolSection.descriptionModule.briefSummary",  #
                "protocolSection.descriptionModule.detailedDescription",  #
                "protocolSection.designModule.studyType",
                "protocolSection.designModule.phases",
                "protocolSection.designModule.designInfo.allocation",
                "protocolSection.designModule.designInfo.primaryPurpose",
                "protocolSection.designModule.designInfo.interventionModel",
                "protocolSection.designModule.enrollmentInfo.count",
                "protocolSection.designModule.enrollmentInfo.type",
                "protocolSection.eligibilityModule.sex",  #
                "protocolSection.eligibilityModule.minimumAge",  #
                "protocolSection.eligibilityModule.maximumAge",  #
                "protocolSection.eligibilityModule.stdAges",  #
                "protocolSection.statusModule.startDateStruct.date",
                "protocolSection.statusModule.primaryCompletionDateStruct.date",  #
                "protocolSection.statusModule.completionDateStruct.date",
            ]
        ]

        def flatten_data(df):
            # Convert nested columns (dicts/lists) to JSON strings
            for col in df.columns:
                if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                    df[col] = df[col].apply(lambda x: json.dumps(x) if x else "")
            return df

        study_df = flatten_data(study_df)

        return study_df

    elif type == "location":
        temp_loc_df = data[["protocolSection.contactsLocationsModule.locations"]]

        for i, study in enumerate(
            temp_loc_df["protocolSection.contactsLocationsModule.locations"]
        ):
            # remove empty entries
            if isinstance(study, float):
                continue

            if i == 0:
                loc_df = pd.json_normalize(study)

            loc_df = pd.concat([loc_df, pd.json_normalize(study)], ignore_index=True)

        return loc_df

    else:
        raise ValueError("Invalid type. Use 'general' or 'location'.")
