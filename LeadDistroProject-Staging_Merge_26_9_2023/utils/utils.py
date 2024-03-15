import csv, json, requests
from django.utils.crypto import get_random_string
import string, os
import pandas as pd 
from django.core.validators import validate_email

import uuid

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def HandleLeadCsvFile(filepath, return_data= False):
    """
        1. read as str and skip all bad rows
        2. resave file 
        3. return total rows, headers
    """
    df = pd.read_csv(filepath, encoding='latin-1', low_memory=True, on_bad_lines='skip', skip_blank_lines=True, skipinitialspace=True, dtype=str)
    df.dropna(how="all", inplace=True)

    if return_data:
        return df.to_dict(orient='records')
                        
    df.to_csv(filepath, encoding='latin-1', header=True, index=False)
    return df.shape[0], df.to_dict(orient='records')[0].keys()


def returnCleanPhone(number):
    try:
        phone_clean = ''.join([n for n in number if n.isdigit()])[-10:]
        phone_clean = str(phone_clean).strip()
        if len(phone_clean) == 10:
            return phone_clean
    except:
        pass
    return None


def chunk_based_on_size(lst, n):
    for x in range(0, len(lst), n):
        each_chunk = lst[x: n+x]
        if len(each_chunk) < n:
            each_chunk = each_chunk + [None for y in range(n-len(each_chunk))]
        yield each_chunk


def generateAPIKEY():
    return get_random_string(40, allowed_chars=string.ascii_uppercase + string.digits + string.ascii_lowercase)


def generatePassword():
    return get_random_string(12, allowed_chars=string.ascii_uppercase + string.digits + string.ascii_lowercase)


def isValidEmailFormat(email):
    try:
        validate_email(email)
        return True
    except:
        return False


def extra_file_columns_filter_output(leads_data):
    rows = []

    # Create a list of custom fields
    column_names = {
        'birthdate': 'Birthdate',
        'address': 'Address',
        'state': 'State',
        'zipcode': 'ZipCode',
        'custom_field1': 'Custom_Field1',
        'custom_field2': 'Custom_Field2',
        'custom_field3': 'Custom_Field3',
        'custom_field4': 'Custom_Field4',
        'custom_field5': 'Custom_Field5',
    }

    # Initialize the header with default columns
    header = ['Sr.', 'Name', 'Phone', 'Email', 'Assigned To', 'Call Block', 'Line Type', 'Dnc Type', 'Added At']

    # Iterate over custom fields and add them to the header if they exist in any lead
    for field, column_name in column_names.items():
        if any(getattr(lead, field) for lead in leads_data):
            header.append(column_name)

    rows.append(header)

    for i, lead in enumerate(leads_data):
        row = [
            i + 1, lead.name, lead.phone, lead.email, lead.get_lead_agent_display(),
            lead.is_callblock, lead.linetype, lead.dnctype, lead.updated_at
        ]

        # Iterate over custom fields and add their values to the row if they exist in the lead
        for field, column_name in column_names.items():
            if getattr(lead, field):
                row.append(getattr(lead, field))
        rows.append(row)

    return rows
