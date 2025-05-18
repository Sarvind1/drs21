"""Utility functions for the document review system."""

import base64
import os
import pandas as pd
from datetime import datetime
from io import StringIO
import csv
import tempfile
from s3_utils import upload_file_to_s3, download_file_from_s3, get_s3_file_url, get_s3_client, get_full_s3_key
import streamlit as st

def load_data():
    """Load and prepare the review data."""
    try:
        if os.path.exists("data/Manual_Review.csv"):
            df_batches = pd.read_csv("data/Manual_Review.csv")
        else:
            data = {
                'Batch': ['B001', 'B001', 'B002', 'B002', 'B003'],
                'batch_count': [1, 2, 1, 2, 1],
                'portal_status': ['Pending', 'Accepted', 'Rejected', 'Pending', 'Accepted'],
                'reason': ['', 'Approved by agent', 'Missing information', '', 'Complete documentation']
            }
            df_batches = pd.DataFrame(data)

        file_data = []
        for _, row in df_batches.iterrows():
            batch = row['Batch']
            count = row['batch_count']
            portal_status = row.get('portal_status', 'Unknown')
            reason = row.get('reason', '')

            for doc_type in ['CI', 'PL']:
                s3_key = f'{doc_type}/{batch}/{batch}_{count}.pdf'
                file_data.append({
                    'batch': batch,
                    'type': doc_type,
                    'version': count,
                    'file_path': s3_key,
                    'filename': f'{batch}_{count}.pdf',
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'portal_status': portal_status,
                    'reason': reason
                })

        return pd.DataFrame(file_data)
    except Exception as e:
        raise Exception(f"Error loading data: {e}")

def format_status_tag(status):
    """Format the review status tag HTML."""
    cls = 'status-reviewed' if status == 'reviewed' else 'status-not-reviewed'
    label = 'Reviewed' if status == 'reviewed' else 'Not Reviewed'
    return f"<span class='status-tag {cls}'>{label}</span>"

def format_portal_status(status, reason=""):
    """Format the portal status tag HTML."""
    tooltip = f" title='{reason}'" if reason else ""
    return f"<span class='portal-status'{tooltip}>{status}</span>"

def embed_pdf_from_s3(s3_key):
    """Display PDF from S3 using a signed URL (works on Streamlit Cloud)."""
    try:
        # Get S3 client and details
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)

        # Generate pre-signed URL valid for 10 minutes
        signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': full_key,
                'ResponseContentDisposition': 'inline',
                'ResponseContentType': 'application/pdf'
            },
            ExpiresIn=600
        )

        # Embed signed URL in an iframe
        pdf_display = f'''
            <iframe
                src="{signed_url}"
                width="100%"
                height="800px"
                style="border: none; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);"
                type="application/pdf">
            </iframe>
        '''
        return pdf_display
    except Exception as e:
        return f"<p style='color:red'>Error displaying PDF: {str(e)}</p>"

def generate_comparison_pairs(versions):
    """Generate pairs of versions for comparison."""
    if len(versions) < 2:
        return []
    pairs = [(versions[i], versions[i+1]) for i in range(len(versions)-1)]
    if len(versions) > 2:
        pairs.append((versions[0], versions[-1]))
    return pairs

def export_audit_trail(audit_trail):
    """Export audit trail to CSV format and save to S3."""
    if not audit_trail:
        return ""

    all_keys = set().union(*(row.keys() for row in audit_trail))
    fieldnames = list(all_keys)

    # Create CSV in memory
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in audit_trail:
        writer.writerow({key: row.get(key) for key in fieldnames})
    
    # Save to temporary file and upload to S3
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(buffer.getvalue())
        temp_file.flush()
        
        # Generate S3 key with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        s3_key = f'audit/audit_trails/{timestamp}/audit_trail.csv'
        
        # Upload to S3
        upload_file_to_s3(temp_file.name, s3_key)
        
        # Clean up temporary file
        os.unlink(temp_file.name)
    
    return buffer.getvalue() 