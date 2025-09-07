from ultralytics import YOLO
import cv2
import os
import re
import pandas as pd
import csv
import time
import signal
import json
from datetime import datetime
from paddleocr import PaddleOCR
from util import *
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def signal_handler(sig, frame):
    print("Received termination signal. Stopping the main script...")
    global stop_flag
    stop_flag = True

def write_pid_to_file():
    pid = os.getpid()
    with open("main_pid.txt", "w") as pid_file:
        pid_file.write(f"PID: {pid}\n")
        pid_file.write("Status: Started\n")

def ANPR(ip_adr,  enorex):
    print(f"Starting {ip_adr} {enorex} ANPR")
    curr_date = datetime.now().date()
    date_today = curr_date.strftime('%d-%m-%Y')

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


    # Initialize PaddleOCR  
    ocr = PaddleOCR(use_angle_cls=True, use_gpu=True, lang='en', show_log=False)

    # Initialize our custom object detection model
    model = YOLO('LPDetector.pt')

    #Set containing LicensePlate and TimePeriod for validating uniqueness
    empty_tuple = ("AP13BD3188",15)
    unique_lp_set = set()
    unique_lp_set.add(empty_tuple)
    # Retrieve the last count from the CSV file
    df = pd.read_csv(f'output/ANPR {enorex} {date_today}.csv')
    last_count = df['SNo'].max() if not df.empty else 0
    daily_count = last_count

    # Number of frames to skip
    skip_frames = 20 # Adjust this value to skip the desired number of frames
    # Frame counter
    frame_counter = 0
    
    # Get credentials from environment variables
    rtsp_username = os.getenv('RTSP_USERNAME', 'admin')
    rtsp_password = os.getenv('RTSP_PASSWORD', 'skill@123')
    video_path = f"rtsp://{rtsp_username}:{rtsp_password}@{ip_adr}"
    cap = cv2.VideoCapture(video_path)
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    # Loop through the video frames
    write_pid_to_file()
    while cap.isOpened() and not stop_flag:
        # Read a frame from the video
        success, frame = cap.read()
        frame_counter += 1
        if success:
            # If a day changes , Dates are checked and new directories are made respectfully
            check_date(date_today,enorex)
            # If the frame counter is not a multiple of skip_frames, then that frame is skipped
            if frame_counter % skip_frames != 0:                                                    
                continue 
            # Run YOLOv8 inference on the frame
            results = model(frame, stream=True, device=0)

            #Extracting the individual results from the inference
            for result in results:
                
                boxes = result.boxes.cpu().numpy()
                # Extracting the bounding boxes
                for i, box in enumerate(boxes):                                   
                    r = box.xyxy[0].astype(int)
                    # Cropping the original inference image down to the license plate
                    lp_cropped = frame[r[1]:r[3], r[0]:r[2]] 
                    
                                                        
                    # Confidence Threshold of LP Detector
                    if (box.conf[0] > 0.5):
                    
                        #Image Processing on the cropped license plate
                        processed_lp = image_processing(lp_cropped)    
                        #Read the processed image
                        ocr_result = ocr.ocr(processed_lp,cls=True)
                        # Extract the text from the results
                        for idx in range(len(ocr_result)):
                            res = ocr_result[idx]
                            if res is not None:
                                for line in res:
                                    LPtext = line[1][0]
                                    ConfidenceScore = line[1][1]
                                LicensePlate = text_processing(LPtext)

                                #OCR Confidence Threshold
                                if ConfidenceScore>0.7:
                                    # Initializing the pattern to check whether OCR text matches our format
                                    if len(LicensePlate) == 9:
                                        pattern = re.compile(r'^(?:[A-Z]{2}\d{1}[A-Z0-9]{2}\d{4}|[A-Z]{2}\d{2}[A-Z0-9]{1}\d{4})$')
                                    elif len(LicensePlate) == 10:
                                        pattern = re.compile(r'^[A-Z]{2}\d{2}[A-Z0-9]{2}\d{4}$')
                                    else:
                                        pattern = None
                                    
                                    # Values for saving and appending to csv
                                    current_date = datetime.now().strftime("%dth %b %Y")
                                    current_time = datetime.now().time().strftime("%H:%M:%S")

                                    # Checking for uniqueness
                                    epoch = time.time()       
                                    LicensePlate_tuple = (LicensePlate,epoch)
                                    iterating_list = list(unique_lp_set)
                                    is_unique=True                                   
                                    for i in iterating_list:
                                        similarity_score = similarity(LicensePlate_tuple[0], i[0])
                                        similarity_threshold = 0.7
                                        
                                        if LicensePlate_tuple[0] == i[0] and check_time(LicensePlate_tuple[1], i[1]) is None:
                                            # Matching but not unique
                                            with open(f'output/ANPR {enorex} {date_today}.csv', 'r', newline='') as file:
                                                reader = csv.reader(file)
                                                most_recent_row = None
                                                # Iterate through the rows in the CSV file
                                                for row in reader:
                                                    most_recent_row = row  # Update the most_recent_row variable with the current row
                                            recent_conf = float(most_recent_row[6])
                                            recent_frame=str(most_recent_row[7])
                                            recent_lpimage=recent_frame.replace("Frame", "LP")

                                            if ConfidenceScore >= recent_conf:
                                                if not pattern == None and pattern.match(LicensePlate):
                                                    delete_recent_row(enorex)
                                                    delete_recent_images(recent_frame,recent_lpimage)
                                                    unique_lp_set.discard(LicensePlate_tuple)
                                                    daily_count=daily_count-1
                                                    is_unique=True
                                                    break
                                                elif pattern == None:
                                                    is_unique=False
                                                    break
                                                else:
                                                    is_unique=False
                                                    break
                                            elif ConfidenceScore < recent_conf:
                                                is_unique=False
                                                break
                                            
                                        elif LicensePlate_tuple[0] == i[0] and check_time(LicensePlate_tuple[1], i[1]) == True:
                                            # Matching and unique
                                            is_unique = True
                                            break
                                        elif similarity_score >= similarity_threshold and check_time(LicensePlate_tuple[1],i[1]) is None:
                                            # Similar
                                            # Open the CSV file for reading
                                            with open(f'output/ANPR {enorex} {date_today}.csv', 'r', newline='') as file:
                                                reader = csv.reader(file)
                                                most_recent_row = None
                                                # Iterate through the rows in the CSV file
                                                for row in reader:
                                                    most_recent_row = row  # Update the most_recent_row variable with the current row
                                            recent_conf = float(most_recent_row[6])
                                            recent_frame=str(most_recent_row[7])
                                            recent_lpimage=recent_frame.replace("Frame", "LP")
                                            if ConfidenceScore < recent_conf:
                                                is_unique=False
                                                break
                                            elif ConfidenceScore >= recent_conf:
                                                if not pattern == None and pattern.match(LicensePlate):
                                                    delete_recent_row(enorex)
                                                    delete_recent_images(recent_frame,recent_lpimage)
                                                    unique_lp_set.discard(LicensePlate_tuple)
                                                    daily_count=daily_count-1
                                                    is_unique=True
                                                    break
                                                elif pattern == False:
                                                    is_unique=False
                                                    break
                                                else:
                                                    is_unique=False
                                                    break
                                    # If it's a new unique plate, add it to the set
                                    if is_unique:
                                        if not pattern == None and pattern.match(LicensePlate):
                                            unique_lp_set.add(LicensePlate_tuple)
                                            daily_count=daily_count+1
                                            # Save Frame and license plate image
                                            timestamp = datetime.now().strftime("%d%m%Y%H%M%S")
                                            frame_filename = f"{timestamp}_Frame.jpg"
                                            try:
                                                lp_cropped_filename = f"{timestamp}_LP.jpg"
                                                frame_save_path = os.path.join(f"output/{enorex} {date_today}/", frame_filename)
                                                lp_cropped_save_path = os.path.join(f"output/{enorex} {date_today}", lp_cropped_filename)
                                                cv2.imwrite(frame_save_path, frame)
                                                cv2.imwrite(lp_cropped_save_path, lp_cropped)
                                            except Exception as e:
                                                print(f'Error saving images: {e}')
                                            # Append the unique license plate and its info into the csv file
                                            append_to_csv(daily_count,ip_adr,enorex,current_date,current_time,LicensePlate,ConfidenceScore,frame_save_path,lp_cropped_save_path)
                                            print("License plate is unique")
                                            print("License PLate:",LicensePlate,"Confidence Score:",ConfidenceScore)
                                        else:
                                            print("License plate not according to format:",LicensePlate)
                                            break
                                    elif not is_unique:
                                        print("License plate is not unique")
                                        print("License PLate:",LicensePlate,"Confidence Score:",ConfidenceScore)
                                else:
                                    #OCR Confidence Threshold
                                    break
        
                            else:
                                # No OCR Result
                                break
                    else:   
                        #Low Box Confidence
                        break
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Break the loop if the end of the video is reached
            break


    # Release the video capture object and close the display window
    cap.release()
    cv2.destroyAllWindows()
    print("Stopped")

# Set up the stop flag
stop_flag = False

# Register the signal handler for SIGTERM (termination)
signal.signal(signal.SIGTERM, signal_handler)

def load_theme(file_path):
    with open (json_file_path,'r') as jsonfile:
            theme = json.load(jsonfile)
    return theme
    
json_file_path = 'settings.json'
theme = load_theme(json_file_path)
ip_adr1 = theme["ip_adr1"]
ip_adr2 = theme["ip_adr2"]

EntryANPR = Thread(target=ANPR, args=(ip_adr1,"Entry"))
ExitANPR = Thread(target=ANPR, args=(ip_adr2, "Exit"))
EntryANPR.start()
ExitANPR.start()