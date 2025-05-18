"""CSS styles for the document review system."""

STYLES = """
<style>
    /* Basic elements */
    .stRadio > div {
        flex-direction: row;
        gap: 1rem;
    }
    
    iframe {
        width: 100%;
        height: 100%;
        min-height: 60vh;
        border: 1px solid #ccc;
    }
    
    .pdf-container {
        width: 100%;
        height: 100%;
    }
    
    /* Layout settings */
    .block-container {
        max-width: 100%;
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Header styles */
    h1, h3, h4, h5 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Main container */
    .main .block-container {
        max-width: 100%;
        padding: 1rem;
    }
    
    /* Status tags */
    .status-tag {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 5px;
    }
    
    .status-reviewed {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-not-reviewed {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .portal-status {
        display: inline-block;
        padding: 3px 6px;
        border-radius: 3px;
        font-size: 0.7rem;
        margin-left: 5px;
        background-color: #e2e3e5;
        color: #383d41;
    }
    
    /* Version comparison buttons */
    .stButton button {
        width: 100%;
        padding: 0.25rem 0.5rem;
        font-size: 0.9rem;
        margin: 0.25rem 0;
    }
    
    .stButton>button:focus:not(:active) {
        box-shadow: none;
    }
    
    /* Form elements */
    .stSelectbox, .stTextInput {
        margin-bottom: 0.5rem !important;
    }
    
    /* Selected version caption */
    .caption-selected {
        text-align: center;
        color: #1E88E5;
        font-weight: bold;
        font-size: 0.8rem;
        margin: 0;
        padding: 0;
    }
    
    /* Column spacing */
    div.row-widget {
        margin-bottom: 0.5rem !important;
    }
    
    /* Remove extra padding from containers */
    div.css-1544g2n.e1fqkh3o4 {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Improve radio button layout */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: flex-start;
        gap: 2rem;
    }
    
    /* Streamlit elements spacing */
    div.element-container {
        margin-bottom: 0.5rem;
    }
</style>
"""