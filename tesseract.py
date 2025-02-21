import pytesseract
import cv2

# Set the path to Tesseract executable (if needed)
pytesseract.pytesseract.tesseract_cmd = "/app/.apt/usr/bin/tesseract"


def preprocess_image(image_path):
    """Enhance image quality for better OCR."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply CLAHE (Adaptive Contrast Enhancement)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced_image = clahe.apply(image)

    # Apply Unsharp Masking (Sharpening)
    blurred = cv2.GaussianBlur(enhanced_image, (0, 0), 3)
    sharpened_image = cv2.addWeighted(enhanced_image, 1.5, blurred, -0.5, 0)

    # Denoising to remove background noise
    denoised_image = cv2.bilateralFilter(sharpened_image, 9, 75, 75)

    return denoised_image

def ocr_image(image_path):
    """Extract text from an image using Tesseract OCR."""
    processed_image = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_image, config="--psm 6")  # Using PSM 6 for better block-wise OCR
    return text
