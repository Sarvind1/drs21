"""Utility functions for the document review system."""

import base64
import os
import pandas as pd
from datetime import datetime
from io import StringIO, BytesIO
import csv
import tempfile
import uuid
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

def embed_pdf_in_browser(s3_key):
    """Display PDF from S3 directly in the browser without iframe."""
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)
        buffer = BytesIO()
        s3_client.download_fileobj(bucket_name, full_key, buffer)
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        pdf_display = f'''
        <object data="data:application/pdf;base64,{base64_pdf}" 
                type="application/pdf" 
                width="100%" 
                height="800px">
            <embed src="data:application/pdf;base64,{base64_pdf}" 
                  type="application/pdf">
            </embed>
        </object>
        '''
        return pdf_display
    except Exception as e:
        return f"<p style='color:red'>Error displaying PDF: {str(e)}</p>"

def embed_pdf_with_pdfjs(s3_key):
    """Display PDF from S3 using PDF.js (Mozilla's PDF viewer)."""
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)
        buffer = BytesIO()
        s3_client.download_fileobj(bucket_name, full_key, buffer)
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        # Minimal PDF.js embed (for demo; for production use a full viewer)
        pdf_display = f'''
        <div id="pdfjs-canvas-container" style="width:100%;height:800px;">
            <canvas id="pdfjs-canvas" style="width:100%;height:100%;"></canvas>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
        <script>
        const pdfData = atob("{base64_pdf}");
        const pdfjsLib = window['pdfjs-dist/build/pdf'];
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
        const loadingTask = pdfjsLib.getDocument({{data: new Uint8Array([...pdfData].map(c => c.charCodeAt(0))) }});
        loadingTask.promise.then(function(pdf) {{
            pdf.getPage(1).then(function(page) {{
                var scale = 1.5;
                var viewport = page.getViewport({{scale: scale}});
                var canvas = document.getElementById('pdfjs-canvas');
                var context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                page.render({{canvasContext: context, viewport: viewport}});
            }});
        }});
        </script>
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

def save_pdf_from_s3_to_static(s3_key, static_dir="static"):
    """Download PDF from S3 and save to a local static directory. Returns local path."""
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)
        os.makedirs(static_dir, exist_ok=True)
        unique_name = f"{uuid.uuid4()}.pdf"
        local_path = os.path.join(static_dir, unique_name)
        with open(local_path, "wb") as f:
            s3_client.download_fileobj(bucket_name, full_key, f)
        return local_path
    except Exception as e:
        return None