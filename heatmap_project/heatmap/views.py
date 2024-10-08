import os
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for Matplotlib
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .models import UploadedImage
from PIL import Image
import fitz  # PyMuPDF

# Function to generate RdBu heatmap
def generate_rdbu_heatmap(image_array, output_path):
    # Normalize the image to the range [-1, 1]
    image_array = 2 * (image_array / 255.0) - 1

    # Generate the heatmap
    plt.figure(figsize=(6, 6))
    plt.imshow(image_array, cmap='RdBu', interpolation='nearest')
    plt.axis('off')

    # Save the heatmap
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=100)
    plt.close()

# Function to load the image (handles pdf, jpg, png)
def load_image(file_path):
    if file_path.lower().endswith(('.jpg', '.png', '.pdf')):
        doc = fitz.open(file_path)
        page = doc.load_page(0)  # Load the first page
        pix = page.get_pixmap(matrix=fitz.Matrix(4, 4))  # Increase resolution
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return np.array(img)
    else:  # For .jpg and .png files
        return cv2.imread(file_path)

# Function to crop the QR code
def crop_qr_code(image):
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Crop the image to the exact area of the QR code
        cropped = image[y:y+h, x:x+w]
        
        return cropped
    else:
        return image  # Return original image if no contour is found

# Django view to handle the upload, cropping, and heatmap generation
def upload_and_process_images(request):
    if request.method == 'POST' and request.FILES:
        original_file = request.FILES['original_image']
        copy_file = request.FILES['copy_image']

        fs = FileSystemStorage()

        # Save original and copy images
        original_filename = fs.save(original_file.name, original_file)
        copy_filename = fs.save(copy_file.name, copy_file)

        original_file_path = fs.path(original_filename)
        copy_file_path = fs.path(copy_filename)

        # Load and crop the images
        original_image = load_image(original_file_path)
        copy_image = load_image(copy_file_path)

        cropped_original = crop_qr_code(original_image)
        cropped_copy = crop_qr_code(copy_image)

        # Convert cropped images to grayscale for heatmap generation
        gray_original = cv2.cvtColor(cropped_original, cv2.COLOR_BGR2GRAY) if cropped_original.ndim == 3 else cropped_original
        gray_copy = cv2.cvtColor(cropped_copy, cv2.COLOR_BGR2GRAY) if cropped_copy.ndim == 3 else cropped_copy

        # Paths to save the heatmaps
        original_heatmap_path = os.path.join(fs.location, 'original_heatmap.png')
        copy_heatmap_path = os.path.join(fs.location, 'copy_heatmap.png')

        # Generate the heatmaps
        generate_rdbu_heatmap(gray_original, original_heatmap_path)
        generate_rdbu_heatmap(gray_copy, copy_heatmap_path)

        # Save uploaded images and heatmaps to the database
        original_image_db = UploadedImage.objects.create(
            original_image=original_file.name,
            copy_image=copy_file.name,
            original_heatmap='original_heatmap.png',
            copy_heatmap='copy_heatmap.png'
        )

        # Pass the file names and URLs to the template
        context = {
            'original_image_name': original_file.name,
            'copy_image_name': copy_file.name,
            'original_image_url': fs.url(original_filename),
            'copy_image_url': fs.url(copy_filename),
            'original_heatmap_url': fs.url('original_heatmap.png'),
            'copy_heatmap_url': fs.url('copy_heatmap.png'),
        }

        return render(request, 'result.html', context)

    return render(request, 'index.html')
