# Document Review System

A Streamlit application for comparing and reviewing document versions stored in S3.

## Features

- Display PDF documents side by side for comparison
- Track review decisions and comments
- Export audit trail of reviews
- Support for different document types and versions

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up AWS credentials:
   - Either create a `.streamlit/secrets.toml` file based on `.streamlit/secrets.example.toml`
   - Or set environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.)

4. Run the application:
   ```
   streamlit run src/app.py
   ```

## Deployment

This application can be deployed to Streamlit Cloud:
1. Connect your GitHub repository in the Streamlit Cloud dashboard
2. Configure the AWS credentials in the Streamlit Cloud secrets management
3. Set the main file path to `src/app.py`

## Structure

- `src/`: Main application code
  - `app.py`: Streamlit application entry point
  - `utils.py`: Utility functions
  - `s3_utils.py`: AWS S3 integration
  - `styles.py`: CSS styles
- `data/`: Sample data files
- `scripts/`: Helper scripts

## Security

This application requires AWS credentials to access S3. Never commit your credentials to the repository. Use `.streamlit/secrets.toml` locally (which is git-ignored) and Streamlit Cloud secrets for deployment.
