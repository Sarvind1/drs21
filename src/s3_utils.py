"""S3 utilities for document storage and retrieval."""

import boto3
import streamlit as st
from botocore.exceptions import ClientError
import os

def get_secret(key, default=None):
    """Get a secret from Streamlit secrets or environment variables."""
    try:
        return st.secrets["aws"][key]
    except (KeyError, FileNotFoundError):
        return os.environ.get(f"AWS_{key.upper()}", default)

def get_s3_client():
    """Create and return an S3 client using credentials from Streamlit secrets or environment variables."""
    return boto3.client(
        's3',
        aws_access_key_id=get_secret('access_key_id'),
        aws_secret_access_key=get_secret('secret_access_key'),
        aws_session_token=get_secret('session_token'),
        region_name=get_secret('region', 'eu-central-1')
    )

def get_full_s3_key(relative_key):
    """Get the full S3 key including the base prefix.
    
    Args:
        relative_key (str): Relative path within the document review system
    
    Returns:
        str: Full S3 key including base prefix
    """
    base_prefix = get_secret('base_prefix', 'Doc_Review/')
    return f"{base_prefix}{relative_key}"

def upload_file_to_s3(local_file_path, relative_key):
    """Upload a file to S3.
    
    Args:
        local_file_path (str): Path to the local file
        relative_key (str): Relative S3 key (path) where the file will be stored
    """
    try:
        s3_client = get_s3_client()
        bucket_name = get_secret('bucket_name')
        if not bucket_name:
            raise ValueError("S3 bucket name not configured")
        
        full_key = get_full_s3_key(relative_key)
        s3_client.upload_file(local_file_path, bucket_name, full_key)
        return True
    except Exception as e:
        st.error(f"Error uploading file to S3: {str(e)}")
        return False

def download_file_from_s3(relative_key, local_file_path):
    """Download a file from S3.
    
    Args:
        relative_key (str): Relative S3 key (path) of the file to download
        local_file_path (str): Local path where the file should be saved
    """
    try:
        s3_client = get_s3_client()
        bucket_name = get_secret('bucket_name')
        if not bucket_name:
            raise ValueError("S3 bucket name not configured")
        
        full_key = get_full_s3_key(relative_key)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        s3_client.download_file(bucket_name, full_key, local_file_path)
        return True
    except Exception as e:
        st.error(f"Error downloading file from S3: {str(e)}")
        return False

def get_s3_file_url(relative_key):
    """Generate a pre-signed URL for an S3 object.
    
    Args:
        relative_key (str): Relative S3 key (path) of the file
    
    Returns:
        str: Pre-signed URL for the file
    """
    try:
        s3_client = get_s3_client()
        bucket_name = get_secret('bucket_name')
        if not bucket_name:
            raise ValueError("S3 bucket name not configured")
        
        full_key = get_full_s3_key(relative_key)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': full_key},
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return url
    except Exception as e:
        st.error(f"Error generating pre-signed URL: {str(e)}")
        return None

def list_s3_files(prefix=""):
    """List files in the S3 bucket with the given prefix.
    
    Args:
        prefix (str): Additional prefix to filter objects
    
    Returns:
        list: List of S3 object keys (relative to base_prefix)
    """
    try:
        s3_client = get_s3_client()
        bucket_name = get_secret('bucket_name')
        if not bucket_name:
            raise ValueError("S3 bucket name not configured")
        
        base_prefix = get_secret('base_prefix', 'Doc_Review/')
        full_prefix = f"{base_prefix}{prefix}"
        
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=full_prefix
        )
        
        if 'Contents' in response:
            # Remove base prefix from returned keys
            return [obj['Key'][len(base_prefix):] for obj in response['Contents']]
        return []
    except Exception as e:
        st.error(f"Error listing S3 files: {str(e)}")
        return [] 