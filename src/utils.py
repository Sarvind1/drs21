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
import boto3
from botocore.exceptions import ClientError

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

def _get_s3_client_and_bucket():
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        return s3_client, bucket_name
    except Exception:
        # fallback to boto3 default if not running in Streamlit
        return boto3.client('s3'), 'your-bucket-name'

def embed_pdf_in_browser(s3_key):
    """Display PDF from S3 directly in the browser using data URI."""
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)
        buffer = BytesIO()
        try:
            s3_client.download_fileobj(bucket_name, full_key, buffer)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return f"<p style='color:red'>PDF not found: {s3_key}</p>"
            raise
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        pdf_display = f'''
        <div style="width:100%; height:800px;">
            <object data="data:application/pdf;base64,{base64_pdf}" 
                    type="application/pdf" 
                    width="100%" 
                    height="100%">
                <p>Your browser doesn't support embedded PDFs. 
                   <a href="data:application/pdf;base64,{base64_pdf}" download="document.pdf">Download the PDF</a> instead.
                </p>
            </object>
        </div>
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
        try:
            s3_client.download_fileobj(bucket_name, full_key, buffer)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return f"<p style='color:red'>PDF not found: {s3_key}</p>"
            raise
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        pdf_display = f'''
        <div id="pdf-viewer" style="width:100%; height:800px; border:1px solid #ccc; overflow:hidden; position:relative;">
            <div id="loading" style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);">Loading PDF...</div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
            <script>
                // Initialize PDF.js
                const loadingTask = pdfjsLib.getDocument({{data: atob('{base64_pdf}')}});
                
                loadingTask.promise.then(function(pdf) {{
                    const container = document.getElementById('pdf-viewer');
                    const loading = document.getElementById('loading');
                    
                    // Create viewer elements
                    const viewer = document.createElement('div');
                    viewer.style.width = '100%';
                    viewer.style.height = '100%';
                    viewer.style.position = 'relative';
                    viewer.style.overflow = 'auto';
                    container.appendChild(viewer);
                    
                    // Create canvas wrapper for better sizing
                    const canvasWrapper = document.createElement('div');
                    canvasWrapper.style.width = '100%';
                    canvasWrapper.style.display = 'flex';
                    canvasWrapper.style.justifyContent = 'center';
                    viewer.appendChild(canvasWrapper);
                    
                    // Create canvas
                    const canvas = document.createElement('canvas');
                    canvasWrapper.appendChild(canvas);
                    
                    // Get page and render
                    pdf.getPage(1).then(function(page) {{
                        const viewport = page.getViewport({{scale: 1.5}});
                        
                        // Set canvas size to match viewport
                        canvas.height = viewport.height;
                        canvas.width = viewport.width;
                        
                        // Render PDF page
                        const renderContext = {{
                            canvasContext: canvas.getContext('2d'),
                            viewport: viewport
                        }};
                        
                        page.render(renderContext).promise.then(() => {{
                            // Remove loading indicator when done
                            loading.style.display = 'none';
                        }});
                    }});
                }}).catch(function(error) {{
                    const container = document.getElementById('pdf-viewer');
                    container.innerHTML = `<p style="color:red">Error loading PDF: ${{error.message}}</p>`;
                }});
            </script>
        </div>
        '''
        return pdf_display
    except Exception as e:
        return f"<p style='color:red'>Error displaying PDF: {str(e)}</p>"

def embed_pdf_streamlit(s3_key):
    """Display PDF in Streamlit using st.components.html."""
    try:
        s3_client, bucket_name = _get_s3_client_and_bucket()
        full_key = get_full_s3_key(s3_key)  # Use get_full_s3_key instead of lstrip
        buffer = BytesIO()
        s3_client.download_fileobj(bucket_name, full_key, buffer)
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        html_string = f'''
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="800" 
                style="border: none;">
        </iframe>
        '''
        st.components.v1.html(html_string, height=800)
        return True
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")
        return False

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

def get_file_from_s3(s3_uri):
    """
    Retrieve a file from S3 using the provided URI or s3_key.
    Args:
        s3_uri: S3 URI in the format 's3://bucket-name/path/to/file' or just the S3 key.
    Returns:
        Binary content of the file
    """
    # If s3_uri is a full URI, parse bucket and key
    if s3_uri.startswith('s3://'):
        parts = s3_uri.replace('s3://', '').split('/', 1)
        if len(parts) < 2:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")
        bucket = parts[0]
        key = parts[1]
    else:
        # Use configured bucket and prefix
        bucket = st.secrets["aws"]["bucket_name"]
        key = get_full_s3_key(s3_uri)
    try:
        s3_client = get_s3_client()
        file_obj = BytesIO()
        s3_client.download_fileobj(bucket, key, file_obj)
        file_obj.seek(0)
        return file_obj.read()
    except Exception as e:
        raise Exception(f"Error accessing S3: {str(e)}")

def embed_pdf_base64(file_path_or_s3key):
    """
    Create an HTML string to embed a PDF using base64 encoding.
    Args:
        file_path_or_s3key: Local file path or S3 key/URI.
    Returns:
        HTML string with embedded PDF viewer
    """
    try:
        # Handle S3 keys/URIs
        if file_path_or_s3key.startswith('s3://') or not os.path.exists(file_path_or_s3key):
            pdf_content = get_file_from_s3(file_path_or_s3key)
        else:
            with open(file_path_or_s3key, "rb") as f:
                pdf_content = f.read()
        base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
        pdf_display = f"""
            <iframe 
                src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="800px" 
                style="border: none; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);"
                type="application/pdf">
            </iframe>
        """
        return pdf_display
    except Exception as e:
        return f"<p style='color:red'>Error displaying PDF: {str(e)}</p>"

def embed_pdf_with_fallback(s3_key):
    """Try multiple methods to display PDF with fallbacks."""
    html = embed_pdf_with_pdfjs_viewer(s3_key)
    if not html or html.strip().startswith("<p style='color:red'>"):
        html = embed_pdf_with_presigned_url(s3_key)
        if not html or html.strip().startswith("<p style='color:red'>"):
            html = embed_pdf_base64(s3_key)
    return html

def embed_pdf_with_presigned_url(s3_key, expiration=3600):
    """Display PDF using a pre-signed S3 URL."""
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': full_key,
                'ResponseContentType': 'application/pdf',
                'ResponseContentDisposition': 'inline'
            },
            ExpiresIn=expiration
        )
        
        html = f'''
        <div style="width:100%; height:800px;">
            <iframe 
                src="{url}" 
                width="100%" 
                height="100%" 
                style="border: none;">
            </iframe>
        </div>
        '''
        return html
    except Exception as e:
        return f"<p style='color:red'>Error generating pre-signed URL: {str(e)}</p>"

def embed_pdf_streamlit_with_presigned_url(s3_key, expiration=3600):
    """Display PDF in Streamlit using a pre-signed S3 URL."""
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': full_key,
                'ResponseContentType': 'application/pdf',
                'ResponseContentDisposition': 'inline'
            },
            ExpiresIn=expiration
        )
        
        html = f'''
        <iframe 
            src="{url}" 
            width="100%" 
            height="800" 
            style="border: none;">
        </iframe>
        '''
        
        st.components.v1.html(html, height=800, scrolling=True)
        st.markdown(f"[Open PDF directly]({url})")
        return True
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")
        return False

def embed_pdf_with_pdfjs_viewer(s3_key):
    """Display PDF using PDF.js built-in viewer."""
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)
        buffer = BytesIO()
        
        try:
            s3_client.download_fileobj(bucket_name, full_key, buffer)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return f"<p style='color:red'>PDF not found: {s3_key}</p>"
            raise
            
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        
        pdf_display = f'''
        <div style="width:100%; height:800px;">
            <iframe
                src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/web/viewer.html?file=data:application/pdf;base64,{base64_pdf}"
                width="100%"
                height="100%"
                style="border: none;">
            </iframe>
        </div>
        '''
        return pdf_display
    except Exception as e:
        return f"<p style='color:red'>Error displaying PDF: {str(e)}</p>"

def embed_pdf_streamlit_enhanced(s3_key):
    """Enhanced PDF display in Streamlit with multiple fallback options."""
    try:
        s3_client = get_s3_client()
        bucket_name = st.secrets["aws"]["bucket_name"]
        full_key = get_full_s3_key(s3_key)
        buffer = BytesIO()
        
        try:
            s3_client.download_fileobj(bucket_name, full_key, buffer)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                st.error(f"PDF not found: {s3_key}")
                return False
            raise
            
        buffer.seek(0)
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        
        # Standard embed method
        html_standard = f'''
        <div style="width:100%; height:800px;">
            <object
                data="data:application/pdf;base64,{base64_pdf}"
                type="application/pdf"
                width="100%"
                height="100%">
                <p>Browser doesn't support embedded PDFs.</p>
            </object>
        </div>
        '''
        
        # Fallback download option
        html_download = f'''
        <div style="width:100%; text-align:center; padding:20px;">
            <a href="data:application/pdf;base64,{base64_pdf}" 
               download="document.pdf" 
               class="download-button">
               Download PDF
            </a>
        </div>
        '''
        
        # Try standard embed first
        st.components.v1.html(html_standard, height=800, scrolling=True)
        
        # Always provide download option
        st.markdown("<style>.download-button{background:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;}</style>", 
                   unsafe_allow_html=True)
        st.components.v1.html(html_download, height=100)
        
        return True
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")
        return False