import cv2
import csv
import re
import numpy as np
import math
import os
import Levenshtein
from datetime import datetime
from typing import Tuple, Union
from deskew import determine_skew
from mappings import *

curr_date = datetime.now().date()
date_today = curr_date.strftime('%d-%m-%Y')

def rotate(
        image: np.ndarray, angle: float, background: Union[int, Tuple[int, int, int]]
) -> np.ndarray:
    try:
        old_width, old_height = image.shape[:2]
        angle_radian = math.radians(angle)
        width = abs(np.sin(angle_radian) * old_height) + abs(np.cos(angle_radian) * old_width)
        height = abs(np.sin(angle_radian) * old_width) + abs(np.cos(angle_radian) * old_height)

        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        rot_mat[1, 2] += (width - old_width) / 2
        rot_mat[0, 2] += (height - old_height) / 2
        return cv2.warpAffine(image, rot_mat, (int(round(height)), int(round(width))), borderValue=background)
    except Exception as e:
            # Handle the error or simply return the original image
            print(f"Error in rotate function: {e}")
            return image

def image_processing(img):
    #1 Resize
    image = cv2.resize(img, (612, 350))
    #2 Grayscale
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #3 Deskew
    angle = determine_skew(grayscale)
    rotated = rotate(image, angle, (0, 0, 0))
    #4 Force back to grayscale
    gray_image = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    #5 Bilateral filtering
    bilateral = cv2.bilateralFilter(gray_image,5,6,6)
    #6 Gaussian filtering
    gaussian_filtered = cv2.GaussianBlur(bilateral, (5, 5), 2)
    #7 Sharpening
    sharpened = cv2.addWeighted(bilateral, 7.5, gaussian_filtered, -6.5, 0)

    return sharpened

def text_processing(ocr_text):
    if len(ocr_text) == 9:
          # Convert to uppercase
        processed_text = ocr_text.upper()
        # Remove spaces before character mapping
        processed_text = ocr_text.replace(" ", "")
        # Process only the first two characters
        for i in range(min(2, len(processed_text))):  
            if processed_text[i] in char_mapping:
                processed_text = processed_text[:i] + char_mapping[processed_text[i]] + processed_text[i+1:]
        # Specific character mapping
        for (index, misread_char), (new_index, correct_char) in specific_char_mapping_9.items():
            if 0 <= index < len(processed_text) and processed_text[index] == misread_char:
                processed_text = processed_text[:index] + correct_char + processed_text[index + 1:]
        # Number mapping
        for (index, misread_char), (new_index, correct_char) in number_mapping_9.items():
            if 0 <= index < len(processed_text) and processed_text[index] == misread_char:
                processed_text = processed_text[:index] + correct_char + processed_text[index + 1:]

        # Remove all special characters after character mapping
        processed_text = re.sub(r'[^A-Z0-9]', '', processed_text)

        return processed_text
    elif len(ocr_text) == 10:
        # Convert to uppercase
        processed_text = ocr_text.upper()  
        # Remove spaces before character mapping
        ocr_text = ocr_text.replace(" ", "")
        # Process only the first two characters
        for i in range(min(2, len(processed_text))):  
            if processed_text[i] in char_mapping:
                processed_text = processed_text[:i] + char_mapping[processed_text[i]] + processed_text[i+1:]
        # Specific character mapping
        for (index, misread_char), (new_index, correct_char) in specific_char_mapping_10.items():
            if 0 <= index < len(processed_text) and processed_text[index] == misread_char:
                processed_text = processed_text[:index] + correct_char + processed_text[index + 1:]
        # Number mapping
        for (index, misread_char), (new_index, correct_char) in number_mapping_10.items():
            if 0 <= index < len(processed_text) and processed_text[index] == misread_char:
                processed_text = processed_text[:index] + correct_char + processed_text[index + 1:]

        # Remove all special characters after character mapping
        processed_text = re.sub(r'[^A-Z0-9]', '', processed_text)

        return processed_text
    elif len(ocr_text) == 11:
        ocr_text = ocr_text[1:]
        # Convert to uppercase
        processed_text = ocr_text.upper()
        # Remove spaces before character mapping
        ocr_text = ocr_text.replace(" ", "")
        # Process only the first two characters
        for i in range(min(2, len(processed_text))):
            if processed_text[i] in char_mapping:
                processed_text = processed_text[:i] + char_mapping[processed_text[i]] + processed_text[i+1:]
        # Specific character mapping
        for (index, misread_char), (new_index, correct_char) in specific_char_mapping_10.items():
            if 0 <= index < len(processed_text) and processed_text[index] == misread_char:
                processed_text = processed_text[:index] + correct_char + processed_text[index + 1:]
        # Number mapping
        for (index, misread_char), (new_index, correct_char) in number_mapping_10.items():
            if 0 <= index < len(processed_text) and processed_text[index] == misread_char:
                processed_text = processed_text[:index] + correct_char + processed_text[index + 1:]

        # Remove all special characters after character mapping
        processed_text = re.sub(r'[^A-Z0-9]', '', processed_text)
    else:
        # Convert to uppercase
        processed_text = ocr_text.upper()
        # Remove spaces before character mapping
        ocr_text = ocr_text.replace(" ", "")
        # Remove all special characters after character mapping
        processed_text = re.sub(r'[^A-Z0-9]', '', processed_text)
        return ocr_text

    if processed_text.startswith("IS"):
        return "TS" + processed_text[2:]
    elif processed_text.startswith("O"):
        return "OD" + processed_text[2:]
    elif processed_text.startswith("R"):
        return "RJ" + processed_text[2:]
    elif processed_text.startswith("S"):
        return "SK" + processed_text[2:]
    elif processed_text.startswith("W"):
        return "WB" + processed_text[2:]
    
    return processed_text

def check_time(final_tuple_time, old_tuple_time):
    if final_tuple_time - old_tuple_time <=90:
        return None
    elif final_tuple_time - old_tuple_time >90:
        return True

def append_to_csv(count, cameranumber,entry_exit,date,time,licenseplate,conf_score,image_path,cropped_image_path):
    headers = ['SNo', 'Camera','Entry/Exit','Date','Time','LicensePlate','Confidence Score','Image Path','Cropped Image']
    with open(f'output/ANPR {entry_exit} {date_today}.csv', mode="a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writerow({"SNo":count,
                        "Camera": cameranumber, 
                        "Entry/Exit": entry_exit, 
                        "Date": date, 
                        "Time": time, 
                        "LicensePlate": licenseplate,
                        "Confidence Score": conf_score,
                        "Image Path": image_path,
                        "Cropped Image": cropped_image_path})
        
def similarity(text1,text2):
    distance = Levenshtein.distance(text1, text2)
    max_length = max(len(text1), len(text2))
    similarity = 1 - (distance / max_length)

    return similarity

def delete_recent_row(entry_exit):
    with open(f'output/ANPR {entry_exit} {date_today}.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        
        # Read the CSV data into a list of rows
        rows = list(reader)

    # Check if there are any rows in the file
    if len(rows) > 0:
        # Remove the most recent row (last row)
        removed_row = rows.pop()

        # Open the same CSV file for writing and create a writer object
        with open(f'output/ANPR {entry_exit} {date_today}.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            
            # Write the remaining rows back to the file
            writer.writerows(rows)

        print(f"Removed the most recent row: {removed_row}")
    else:
        print("The CSV file is empty.")

def delete_recent_images(frame,lp):
        try:
            if os.path.exists(frame):
                os.remove(frame)
                print(f"File '{frame}' deleted successfully.")
            else:
                print(f"File '{frame}' does not exist.")
            if os.path.exists(lp):
                os.remove(lp)
                print(f"File '{lp}' deleted successfully.")
            else:
                print(f"File '{lp}' does not exist.")
        except PermissionError as pe:
            print(f'File might be locked! {pe}')

def check_date(date_today,enorex):
    datetocheck = datetime.now().date()
    checkdate = datetocheck.strftime('%d-%m-%Y')
    if not date_today == checkdate :
        date_today = checkdate
       # Output directories for images and CSV file
        output_directory = "output"
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        entry_LP_directory = f"output/Entry {date_today}"
        if not os.path.exists(entry_LP_directory):
            os.makedirs(entry_LP_directory)
        exit_LP_directory = f"output/Exit {date_today}"
        if not os.path.exists(exit_LP_directory):
            os.makedirs(exit_LP_directory)

        # Check if the CSV file already exists
        if not os.path.exists(f'output/ANPR {enorex} {date_today}.csv'):
            headers = ['SNo', 'Camera', 'Entry/Exit', 'Date', 'Time', 'LicensePlate', 'Confidence Score', 'Image Path', 'Cropped Image']
            # Create a new CSV file
            with open(f'output/ANPR {enorex} {date_today}.csv', mode='w', newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
