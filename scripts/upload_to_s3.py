#!/usr/bin/env python3
"""Script to migrate documents from local storage to S3."""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.s3_utils import upload_file_to_s3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)

def process_batch(batch_path):
    """Process a single batch directory.
    
    Args:
        batch_path (Path): Path to the batch directory
    """
    batch_id = batch_path.name
    
    # Process CI documents
    ci_path = batch_path / "CI"
    if ci_path.exists():
        for pdf in ci_path.glob("*.pdf"):
            version = pdf.stem.split("_")[-1]
            s3_key = f"CI/{batch_id}/{batch_id}_{version}.pdf"
            if upload_file_to_s3(str(pdf), s3_key):
                logging.info(f"Uploaded CI document: {s3_key}")
            else:
                logging.error(f"Failed to upload: {pdf}")
    
    # Process PL documents
    pl_path = batch_path / "PL"
    if pl_path.exists():
        for pdf in pl_path.glob("*.pdf"):
            version = pdf.stem.split("_")[-1]
            s3_key = f"PL/{batch_id}/{batch_id}_{version}.pdf"
            if upload_file_to_s3(str(pdf), s3_key):
                logging.info(f"Uploaded PL document: {s3_key}")
            else:
                logging.error(f"Failed to upload: {pdf}")
    
    # Process RG Excel files
    for excel in batch_path.glob("RG*.xlsx"):
        s3_key = f"audit/{batch_id}/{excel.name}"
        if upload_file_to_s3(str(excel), s3_key):
            logging.info(f"Uploaded audit file: {s3_key}")
        else:
            logging.error(f"Failed to upload: {excel}")

def main():
    """Main migration function."""
    source_dir = Path("/Users/teq-admin/Downloads/RB")
    if not source_dir.exists():
        logging.error(f"Source directory not found: {source_dir}")
        return
    
    # Process all batch directories
    batch_pattern = "BATCH*"
    for batch_path in sorted(source_dir.glob(batch_pattern)):
        if batch_path.is_dir():
            logging.info(f"Processing batch: {batch_path.name}")
            try:
                process_batch(batch_path)
            except Exception as e:
                logging.error(f"Error processing batch {batch_path.name}: {str(e)}")

if __name__ == "__main__":
    main() 