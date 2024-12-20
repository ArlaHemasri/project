
# Importing the required libraries
import pdfplumber
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import pandas as pd
import re

# writing a Function to convert pdf into the plain text
def clean_text(text):
    text = re.sub(r'\n+', ' ', text)  # Replacing the newlines
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Removing non-ASCII
    text = re.sub(r'[^\w\s\.\%\:\$\-]', '', text)  # Keeping valid symbols
    text = re.sub(r'\s+', ' ', text).strip()  # Normalizing spaces
    return text

# Function to preprocess images for OCR
def preprocess_image_for_ocr(image):
   
    image = image.convert("L")  # Grayscale
    image = ImageEnhance.Contrast(image).enhance(2.5)  # Increase contrast
    image = ImageOps.invert(image)  # Invert for better text visibility
    image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)  # Resize
    return image

# OCR function with fallback to different PSM modes

def ocr_page(pdf_path, page_number):
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_number]
            image = page.to_image(resolution=300).original
            image = preprocess_image_for_ocr(image)

            # First OCR attempt with PSM 6
            text = pytesseract.image_to_string(image, config="--psm 6")
            if not text.strip():
                text = pytesseract.image_to_string(image, config="--psm 4")
            print(f"OCR performed on Page {page_number + 1}")
            return clean_text(text)
    except Exception as e:
        return f"Error performing OCR on Page {page_number + 1}: {e}"

# Function to dynamically format and align OCR output
def format_ocr_output(text):
   
    # Patterns for degrees, percentages, and monetary values
    degree_pattern = r'(Doctoral|Professional|Masters|Bachelors|Associates|Some college|High school|Less than high school)\s(degree|diploma)'
    value_pattern = r'(\d+\.\d+\%|\$\d+|\d+)'

    # Find all degrees and values dynamically
    degrees = re.findall(degree_pattern, text)
    values = re.findall(value_pattern, text)

    formatted_output = []
    idx = 0

    # Align degrees with their respective values
    for degree in degrees:
        degree_text = " ".join(degree)
        value = values[idx] if idx < len(values) else "N/A"
        formatted_output.append(f"{degree_text}: {value}")
        idx += 1

    # Print formatted lines
    for line in formatted_output:
        print(line)

# Function to extract text from specific pages for better understanding
def extract_page_text(pdf_path, page_numbers):
    
    page_data = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in page_numbers:
            try:
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text and len(text.strip()) > 0:
                    page_data[f"Page {page_num+1}"] = clean_text(text)
                else:
                    print(f"No text found on Page {page_num+1}, performing OCR...")
                    page_data[f"Page {page_num+1}"] = ocr_page(pdf_path, page_num)
            except IndexError:
                page_data[f"Page {page_num+1}"] = "Page number out of range."
    return page_data

# Function to extract tabular data from the pdf
def extract_table_data(pdf_path, page_number):
   
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_number]
            tables = page.extract_tables()
            if tables:
                cleaned_table = [[re.sub(r'\s+', ' ', str(cell).strip()) for cell in row] for row in tables[0]]
                df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                print(f"Table extracted successfully from Page {page_number + 1}")
                return df
            else:
                print(f"No tables found on Page {page_number + 1}")
                return pd.DataFrame()
    except Exception as e:
        print(f"Error extracting table from Page {page_number + 1}: {e}")
        return pd.DataFrame()

# PDF File Path
pdf_path = "sample.pdf"

# Extract text and format Page 2
print("----- Page 2: Unemployment Information by Degree -----")
specific_pages = extract_page_text(pdf_path, [1, 5])
page_2_text = specific_pages.get("Page 2", "No data found.")
format_ocr_output(page_2_text)

# Extract and display tabular data from Page 6
print("\n----- Page 6: Tabular Data -----")
page_6_table = extract_table_data(pdf_path, 5)
if not page_6_table.empty:
    print("Extracted Tabular Data:")
    print(page_6_table)
else:
    print("No tabular data found on Page 6.")