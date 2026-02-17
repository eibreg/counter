import streamlit as st
import requests
from PIL import Image
import io
import base64
import pytesseract
import cv2
import numpy as np
from github import Github
import tempfile
import os

# Page config
st.set_page_config(page_title="GitHub Image OCR", page_icon="🔍", layout="wide")

# Title
st.title("🔍 GitHub Image OCR Extractor")
st.markdown("Extract text from images stored in GitHub repositories")

# Sidebar for GitHub configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # GitHub token (optional - for private repos or higher rate limits)
    github_token = st.text_input("GitHub Token (optional)", type="password", 
                                  help="For private repos or to increase rate limits")
    
    st.markdown("---")
    st.header("📁 Repository Details")
    
    # Repository input
    repo_url = st.text_input("GitHub Repository URL", 
                             placeholder="https://github.com/username/repo")
    
    # Or split inputs
    col1, col2 = st.columns(2)
    with col1:
        owner = st.text_input("Owner", placeholder="username")
    with col2:
        repo_name = st.text_input("Repository", placeholder="repo-name")
    
    # Branch
    branch = st.text_input("Branch", value="main")
    
    # File path
    image_path = st.text_input("Image Path in Repo", 
                               placeholder="path/to/image.jpg",
                               help="Relative path from repository root")
    
    # OCR Settings
    st.markdown("---")
    st.header("🔧 OCR Settings")
    ocr_lang = st.selectbox("Language", ["eng", "fra", "deu", "spa", "ita", "jpn", "kor", "chi_sim"])
    preprocessing = st.checkbox("Enable Image Preprocessing", value=True, 
                                help="Enhance image for better OCR results")

# Main content area - split into two columns
col1, col2 = st.columns(2)

# Function to get image from GitHub
def get_image_from_github(owner, repo, path, branch="main", token=None):
    """Fetch image from GitHub repository"""
    try:
        # Construct GitHub API URL
        if token:
            # Use authenticated request
            headers = {'Authorization': f'token {token}'}
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            response = requests.get(url, headers=headers)
        else:
            # Public repo
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            response = requests.get(url)
        
        if response.status_code == 200:
            content = response.json()
            if content.get('encoding') == 'base64':
                # Decode base64 image
                image_data = base64.b64decode(content['content'])
                return Image.open(io.BytesIO(image_data))
            else:
                # Direct download URL
                download_url = content.get('download_url')
                if download_url:
                    img_response = requests.get(download_url)
                    return Image.open(io.BytesIO(img_response.content))
        else:
            st.error(f"Error fetching image: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Function to browse repository files
def browse_repo_files(owner, repo, branch="main", token=None, path=""):
    """Browse files in GitHub repository"""
    try:
        if token:
            headers = {'Authorization': f'token {token}'}
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            response = requests.get(url, headers=headers)
        else:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

# Function to preprocess image for better OCR
def preprocess_image(image):
    """Enhance image for better OCR results"""
    # Convert PIL to OpenCV
    img = np.array(image)
    
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    
    # Apply thresholding to get black and white image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    denoised = cv2.medianBlur(thresh, 1)
    
    # Convert back to PIL
    return Image.fromarray(denoised)

# Function to perform OCR
def perform_ocr(image, lang='eng', preprocess=True):
    """Extract text from image using pytesseract"""
    try:
        if preprocess:
            processed_img = preprocess_image(image)
        else:
            processed_img = image
        
        # Extract text
        text = pytesseract.image_to_string(processed_img, lang=lang)
        
        # Get detailed data for bounding boxes
        data = pytesseract.image_to_data(processed_img, lang=lang, output_type=pytesseract.Output.DICT)
        
        return text, data, processed_img
    except Exception as e:
        st.error(f"OCR Error: {str(e)}")
        return "", None, image

# Function to draw bounding boxes
def draw_boxes(image, ocr_data):
    """Draw bounding boxes around detected text"""
    img = np.array(image)
    
    # Convert to RGB if grayscale
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    
    n_boxes = len(ocr_data['level'])
    for i in range(n_boxes):
        if int(ocr_data['conf'][i]) > 30:  # Filter low confidence detections
            (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], 
                           ocr_data['width'][i], ocr_data['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    return Image.fromarray(img)

# File browser in sidebar
if owner and repo_name:
    with st.sidebar:
        st.markdown("---")
        st.header("📂 Repository Browser")
        
        files = browse_repo_files(owner, repo_name, branch, github_token)
        
        if files:
            # Filter for images
            image_files = [f for f in files if f['name'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            
            if image_files:
                selected_file = st.selectbox(
                    "Select an image file",
                    options=[f['name'] for f in image_files],
                    format_func=lambda x: f"🖼️ {x}"
                )
                
                if selected_file:
                    # Find the selected file's path
                    for f in image_files:
                        if f['name'] == selected_file:
                            image_path = f['path']
                            st.session_state['selected_path'] = image_path
                            st.info(f"Selected: {image_path}")
                            break
            else:
                st.warning("No image files found in this directory")

# Main area - Process button
if st.button("🚀 Extract Text", type="primary"):
    if (owner and repo_name and image_path) or (repo_url and image_path):
        
        # Parse repo URL if provided
        if repo_url and not (owner and repo_name):
            parts = repo_url.rstrip('/').split('/')
            if len(parts) >= 2:
                owner = parts[-2]
                repo_name = parts[-1].replace('.git', '')
        
        with st.spinner("Fetching image from GitHub..."):
            # Get image from GitHub
            image = get_image_from_github(owner, repo_name, image_path, branch, github_token)
            
            if image:
                # Display original image
                with col1:
                    st.subheader("📷 Original Image")
                    st.image(image, use_column_width=True)
                
                # Perform OCR
                with st.spinner("Performing OCR..."):
                    text, ocr_data, processed_img = perform_ocr(image, ocr_lang, preprocessing)
                    
                    # Display results
                    with col2:
                        st.subheader("📝 Extracted Text")
                        
                        # Text area with extracted text
                        st.text_area("", text, height=300)
                        
                        # Download button for text
                        st.download_button(
                            label="📥 Download Text",
                            data=text,
                            file_name="extracted_text.txt",
                            mime="text/plain"
                        )
                    
                    # Show processed image with boxes
                    if ocr_data:
                        st.subheader("🎯 Text Detection")
                        boxed_image = draw_boxes(processed_img, ocr_data)
                        st.image(boxed_image, caption="Detected Text Regions", use_column_width=True)
                    
                    # Show statistics
                    st.success(f"✅ Extracted {len(text.split())} words from image")
            else:
                st.error("Failed to load image from GitHub")
    else:
        st.warning("Please provide repository details and image path")

# Footer with instructions
st.markdown("---")
with st.expander("📖 How to use"):
    st.markdown("""
    ### Instructions:
    1. **Enter GitHub repository details** (owner/name) or full URL
    2. **Specify the image path** within the repository
    3. **Optional**: Add GitHub token for private repos
    4. **Click "Extract Text"** to process
    
    ### Example:
    - Repository: `https://github.com/username/my-repo`
    - Image Path: `images/screenshot.png`
    - Branch: `main`
    
    ### Tips:
    - Use preprocessing for better results with low-quality images
    - Select the correct language for non-English text
    - The bounding boxes show where text was detected
    """)

# Check for Tesseract installation
try:
    pytesseract.get_tesseract_version()
except:
    st.error("⚠️ Tesseract OCR is not installed or not in PATH. Please install it first.")
    st.info("""
    **Installation:**
    - **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
    - **macOS**: `brew install tesseract`
    - **Linux**: `sudo apt install tesseract-ocr`
    """)
