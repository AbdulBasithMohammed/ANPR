import customtkinter as ctk
import pandas as pd
import os
import webbrowser
import cv2
import csv
import json
import subprocess
import signal
import  sys
import pyperclip
import re
from tkcalendar import *
from datetime import datetime,timedelta
from CTkTable import *
from PIL import Image, ImageTk
from streamz.dataframe import PeriodicDataFrame
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Output directories for images and CSV file
curr_date = datetime.now().date()
date_today = curr_date.strftime('%d-%m-%Y')

output_directory = "output"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)
entry_LP_directory = f"output/Entry {date_today}"
if not os.path.exists(entry_LP_directory):
    os.makedirs(entry_LP_directory)
exit_LP_directory = f"output/Exit {date_today}"
if not os.path.exists(exit_LP_directory):
    os.makedirs(exit_LP_directory)

# Loading previous theme options from JSON file
def save_theme(theme,file_path):
        with open (json_file_path,'w') as jsonfile:
            json.dump(theme,jsonfile)

def load_theme(file_path):
    with open (json_file_path,'r') as jsonfile:
            theme = json.load(jsonfile)
    return theme
    
json_file_path = 'settings.json'
theme = load_theme(json_file_path)

# ANPR Start / Stop Functions
# Stop Functions
def stop_main_script(pid):
    try:
        os.kill(pid, signal.SIGTERM)
        print("Sent stop signal to the main script.")
    except OSError as e:
        print(f"Error stopping main script: {e}")


def get_main_pid_from_file():
    pid = None
    status = None
    with open("main_pid.txt", "r") as pid_file:
        lines = pid_file.readlines()
        if lines:
            pid_line = lines[0].strip()
            if pid_line.startswith("PID:"):
                pid = int(pid_line.split(":")[1].strip())
    return pid

def stop_main_script_from_file():
    global main_pid
    main_pid = get_main_pid_from_file()
    print('No main_pid.txt file created!')
    stop_main_script(main_pid)
    if os.path.exists("main_pid.txt"):
        os.remove("main_pid.txt")
        print("Deleted main_pid.txt")
    print("Sent stop signal to the main script.")

# Storage Functions
def CheckStorage(directory):
    for item in os.listdir(directory):

        pattern = r'\b\d{2}-\d{2}-\d{4}\b'
        match = re.search(pattern, item)

        if match:
            date_str = match.group()
            print(f"Found date string '{date_str}' in item '{item}'")
            try:
                dateconvert = datetime.strptime(date_str, "%d-%m-%Y")
                date = dateconvert.strftime("%d-%m-%Y")
                date_dt = datetime.strptime(date, "%d-%m-%Y")

                raw_date_today = datetime.now().date()
                date_today=raw_date_today.strftime("%d-%m-%Y")
                date_today_dt = datetime.strptime(date_today, "%d-%m-%Y")

                date_diff = (date_today_dt - date_dt).days
                try:
                    if date_diff > 90:
                        full_path = os.path.join(directory,item)
                        os.rmdir(full_path)
                        print(f'Directory {full_path} deleted succesfully!')
                    else:
                        print('Recent Directory detected. Skipping!')
                except OSError as e:
                    print(f'Error! {e}')

            except ValueError:
                print(f"Error: Invalid date format in '{item}' for date string '{date_str}'")
# Merging old CSVs
def MergeCSVs():
    date_files_dict = {}

    csv_files = [file for file in os.listdir('output/') if file.endswith('.csv')]
    if not csv_files:
        print("No CSV files found in the output directory.")
        exit()

    for csvfile in csv_files:
        pattern = r'\b\d{2}-\d{2}-\d{4}\b'
        match = re.search(pattern, csvfile)

        if match:
            date_str = match.group()
            if date_str in date_files_dict:
                date_files_dict[date_str].append(csvfile)
            else:
                date_files_dict[date_str] = [csvfile]

    # Merge CSV files with the same date
    for date, files in date_files_dict.items():
        if len(files) > 1:  # Merge only if there's more than one file for the date
            output_file_path = f'output/ANPR {date}.csv'
            if os.path.isfile(output_file_path):
                # Load existing merged file
                merged_df = pd.read_csv(output_file_path)
            else:
                merged_df = pd.DataFrame()

            # Concatenate new data to the existing or empty DataFrame
            dfs = [pd.read_csv(os.path.join('output/', file)) for file in files]
            dfs.append(merged_df)  # Append existing merged DataFrame
            merged_df = pd.concat(dfs)

            # Save the updated merged DataFrame
            merged_df.to_csv(output_file_path, index=False)

            # Delete old files after merging
            for file in files:
                os.remove(os.path.join('output/', file))

            print(f"Merged files for {date} and saved as {output_file_path}")
        else:
            print(f"Not enough files to merge for {date}")
# Appearance and Basic Window Settings
app = ctk.CTk()
app.geometry('1920x1080')
app.title("ANPR System")
app.iconbitmap('assets/icons/logo.ico')
ctk.deactivate_automatic_dpi_awareness()
ctk.set_appearance_mode(theme["appearance_mode"])
ctk.FontManager.load_font('assets/fonts/Nunito-VariableFont_wght.ttf')
ctk.FontManager.load_font('assets/fonts/Nunito-Italic-VariableFont_wght.ttf')
my_font_bold = "Nunito Medium"
my_font_italic = 'Nunito Italic'
my_font_light = 'Nunito light'
ip_adr1 = theme["ip_adr1"]
ip_adr2 = theme["ip_adr2"]

# Get RTSP credentials from environment variables
rtsp_username = os.getenv('RTSP_USERNAME', 'admin')
rtsp_password = os.getenv('RTSP_PASSWORD', 'skill@123')
video_path1 = f"rtsp://{rtsp_username}:{rtsp_password}@{ip_adr1}"
video_path2 = f"rtsp://{rtsp_username}:{rtsp_password}@{ip_adr2}"
cap1 = cv2.VideoCapture(video_path1)
w1 = cap1.get(cv2.CAP_PROP_FRAME_WIDTH)
h1 = cap1.get(cv2.CAP_PROP_FRAME_HEIGHT)
cap1.set(cv2.CAP_PROP_FRAME_WIDTH, w1)
cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, h1)
cap2 = cv2.VideoCapture(video_path2)
w2 = cap2.get(cv2.CAP_PROP_FRAME_WIDTH)
h2 = cap2.get(cv2.CAP_PROP_FRAME_HEIGHT)
cap2.set(cv2.CAP_PROP_FRAME_WIDTH, w2)
cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, h2)
current_date = datetime.now().date()
date_today = current_date.strftime('%d-%m-%Y')
main_color='#097BB9'


# ~~~ Main Window ~~~ #
side_menu = ctk.CTkFrame(app, corner_radius=0,fg_color=main_color, width=300, height = 2500, border_color='white')
side_menu.pack_propagate(0)
side_menu.pack(side='left')

main_frame = ctk.CTkFrame(app,corner_radius=0,border_width=0,border_color='white')
main_frame.pack(side='right',fill='both', expand=True)

# !!! Main Window !!! #

# ~~~ Side Menu ~~~ #
logo = ctk.CTkImage(Image.open('assets/icons/logo.png'), size=(100,100))
logo_label = ctk.CTkLabel(side_menu, image=logo, text="")
logo_label.pack(pady=100, anchor="center")


home_logo=ctk.CTkImage(Image.open('assets/icons/home.png'), size=(25,25))
home_btn = ctk.CTkButton(side_menu, image=home_logo, text='     Home', fg_color="transparent", corner_radius=15, font=(my_font_bold, 30), hover_color="#085F8E",width=240, height=55, anchor='w', command=lambda: switch_to_home(home_btn) )
home_btn.pack(anchor="center", pady=27)

totaldata_logo=ctk.CTkImage(Image.open('assets/icons/total_data.png'), size=(25,25))
totaldata_btn = ctk.CTkButton(side_menu, image=totaldata_logo, text='     Total Data', fg_color="transparent", corner_radius=15, font=(my_font_bold, 30), hover_color="#085F8E",width=240, height=55, anchor='w', command=lambda: switch_to_totaldata(totaldata_btn) )
totaldata_btn.pack(anchor="center", pady=27)

search_logo=ctk.CTkImage(Image.open('assets/icons/search.png'), size=(25,25))
search_btn = ctk.CTkButton(side_menu, image=search_logo, text='     Search', fg_color="transparent", corner_radius=15, font=(my_font_bold, 30), hover_color="#085F8E",width=240, height=55, anchor='w', command=lambda: switch_to_search(search_btn) )
search_btn.pack(anchor="center", pady=27)

settings_logo=ctk.CTkImage(Image.open('assets/icons/settings.png'), size=(25,25))
settings_btn = ctk.CTkButton(side_menu, image=settings_logo, text='     Settings', fg_color="transparent", corner_radius=15, font=(my_font_bold, 30), hover_color="#085F8E",width=240, height=55, anchor='w', command=lambda: switch_to_settings(settings_btn) )
settings_btn.pack(anchor="center", pady=27)

def switch_to_home(btn):
    for stuff in main_frame.winfo_children():
        stuff.destroy()
    homeselect_logo=ctk.CTkImage(Image.open('assets/icons/homeselect.png'),size=(25,25))
    side_menu_buttons_while_switching(btn)
    btn.configure(fg_color='white',text_color=main_color, hover=False, image=homeselect_logo)
    home_page()
    

def switch_to_totaldata(btn):
    for stuff in main_frame.winfo_children():
        stuff.destroy()
    total_data_select_logo=ctk.CTkImage(Image.open('assets/icons/total_data_select.png'),size=(25,25))
    side_menu_buttons_while_switching(btn)
    btn.configure(fg_color='white',text_color=main_color, hover=False, image=total_data_select_logo)
    total_data_page()

def switch_to_search(btn):
    for stuff in main_frame.winfo_children():
        stuff.destroy()
    searchselect_logo=ctk.CTkImage(Image.open('assets/icons/searchselect.png'),size=(25,25))
    side_menu_buttons_while_switching(btn)
    btn.configure(fg_color='white',text_color=main_color, hover=False, image=searchselect_logo)
    search_page()

def switch_to_settings(btn):
    for stuff in main_frame.winfo_children():
        stuff.destroy()
    settingsselect_logo=ctk.CTkImage(Image.open('assets/icons/settingsselect.png'),size=(25,25))
    side_menu_buttons_while_switching(btn)
    btn.configure(fg_color='white',text_color=main_color, hover=False, image=settingsselect_logo)
    settings_page()
        
def side_menu_buttons_while_switching(btn):
    if btn == home_btn:
        totaldata_btn.configure(fg_color='transparent',text_color='white', hover=True,image=totaldata_logo)
        search_btn.configure(fg_color='transparent',text_color='white', hover=True,image=search_logo)
        settings_btn.configure(fg_color='transparent',text_color='white', hover=True,image=settings_logo)
    elif btn == totaldata_btn:
        home_btn.configure(fg_color='transparent',text_color='white', hover=True,image=home_logo)
        search_btn.configure(fg_color='transparent',text_color='white', hover=True,image=search_logo)
        settings_btn.configure(fg_color='transparent',text_color='white', hover=True,image=settings_logo)
    elif btn == search_btn:
        totaldata_btn.configure(fg_color='transparent',text_color='white', hover=True,image=totaldata_logo)
        home_btn.configure(fg_color='transparent',text_color='white', hover=True,image=home_logo)
        settings_btn.configure(fg_color='transparent',text_color='white', hover=True,image=settings_logo)
    elif btn == settings_btn:
        totaldata_btn.configure(fg_color='transparent',text_color='white', hover=True,image=totaldata_logo)
        search_btn.configure(fg_color='transparent',text_color='white', hover=True,image=search_logo)
        home_btn.configure(fg_color='transparent',text_color='white', hover=True,image=home_logo)
# !!! Side Menu !!! #
        
# ~~~ HOME PAGE ~~~ #
def home_page():
    home_heading = ctk.CTkLabel(main_frame, text= 'ANPR Analytics', text_color=main_color, fg_color="transparent", corner_radius=15, font=(my_font_bold, 50),width=240, height=55, anchor='w')
    home_heading.pack_propagate(0)
    home_heading.place(x=80,y=75)

    home_date = ctk.CTkLabel(main_frame, text= date_today, text_color=main_color, fg_color="transparent", corner_radius=15, font=(my_font_bold, 25),width=240, height=55, anchor='w')
    home_date.pack_propagate(0)
    home_date.place(x=1350,y=75)

    #Live Feed
    def update():
        success, frame = cap1.read()
        success2, frame2 = cap2.read()
        if success:
            if success2:
                resized_frame = cv2.resize(frame, (640, 360))
                resized_frame2 = cv2.resize(frame2, (640, 360))
                photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)))
                photo2 = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(resized_frame2, cv2.COLOR_BGR2RGB)))
                home_camera1.create_image(0, 0, image=photo, anchor=ctk.NW)
                home_camera1.photo = photo
                home_camera2.create_image(0, 0, image=photo2, anchor=ctk.NW)
                home_camera2.photo = photo2
                main_frame.after(5, update) 
            else:
                print('Error: Failed to read frames from Exit Camera')
        else:
            print('Error: Failed to read frames from Entry Camera')
        
    home_camera1= ctk.CTkCanvas(main_frame, width=640, height=360,bg=main_color,highlightbackground=main_color)
    home_camera1.place(x=50,y=175)
    home_camera2= ctk.CTkCanvas(main_frame, width=640, height=360,bg=main_color,highlightbackground=main_color)
    home_camera2.place(x=50,y=625)
    update()

    # Start ANPR Function
    def start_anpr():
        def is_already_started():
            if os.path.exists("main_pid.txt"):
                with open("main_pid.txt", "r") as pid_file:
                    lines = pid_file.readlines()
                    for line in lines:
                        if line.strip() == "Status: Started":
                            return True
            return False
        if not is_already_started():
            subprocess.Popen([sys.executable, "main.py"],shell=True)
            ANPR_btn.configure(image=stop_logo,text='Stop ANPR')
            ANPR_btn.configure(command=stop_anpr)
        else:
            print('Main script already running!')
            ANPR_btn.configure(image=stop_logo,text='Stop ANPR')
            ANPR_btn.configure(command=stop_anpr)
    
    # Stop ANPR Function
    def stop_anpr():
        try: 
            stop_main_script_from_file()
            ANPR_btn.configure(image=start_logo,text='Start ANPR')
            ANPR_btn.configure(command=start_anpr)
        except:
            print('Main File Not started yet! Please wait')
    
    start_logo=ctk.CTkImage(light_image=Image.open('assets/icons/play.png'), 
                           dark_image=Image.open('assets/icons/play_dark.png'), size=(25,25))
    stop_logo=ctk.CTkImage(light_image=Image.open('assets/icons/stop.png'), 
                           dark_image=Image.open('assets/icons/stop_dark.png'), size=(25,25))
    ANPR_btn = ctk.CTkButton(main_frame, text='Start ANPR', width=100,height=50, font=(my_font_light,15),fg_color='transparent',text_color=('#636363','#BBBBBB'),
                               corner_radius=40,border_color=('#636363','#BBBBBB'),border_width=3, hover_color=('#BBBBBB','#636363'), image=start_logo, command=start_anpr)
    ANPR_btn.place(x=1350,y=900)


    #License Plate Displays
    home_frame_1 = ctk.CTkFrame(main_frame, width=200, height=250, fg_color='#064B71')
    home_frame_1.pack_propagate(0)
    home_frame_1.place(x=800,y=240)
    home_frame_1_title = ctk.CTkLabel(home_frame_1, height=50, text = 'License Plate', fg_color=main_color, text_color='white', font=(my_font_bold, 25), wraplength=200)
    home_frame_1_title.pack_propagate(0)
    home_frame_1_title.pack(fill='x')
    home_frame_1_LP_text = ctk.CTkLabel(home_frame_1, height=35, text = '', fg_color=main_color, text_color='white', font=(my_font_bold, 25), wraplength=200)
    home_frame_1_LP_text.pack_propagate(0)
    home_frame_1_LP_text.pack(side='bottom', fill='x')
    home_frame_1_LPpic = ctk.CTkImage(dark_image=Image.open("assets/icons/picinitial.png"),size=(200,120))
    home_frame_1_LPpic_label = ctk.CTkLabel(home_frame_1, image=home_frame_1_LPpic, text="")
    home_frame_1_LPpic_label.pack(anchor='c',pady=30)
    
    home_frame_3 = ctk.CTkFrame(main_frame, width=200, height=250, fg_color='#064B71')
    home_frame_3.pack_propagate(0)
    home_frame_3.place(x=800,y=695)
    home_frame_3_title = ctk.CTkLabel(home_frame_3, height=50, text = 'License Plate', fg_color=main_color, text_color='white', font=(my_font_bold, 25), wraplength=200)
    home_frame_3_title.pack_propagate(0)
    home_frame_3_title.pack(fill='x')
    home_frame_3_LP_text = ctk.CTkLabel(home_frame_3, height=35, text = '', fg_color=main_color, text_color='white', font=(my_font_bold, 25), wraplength=200)
    home_frame_3_LP_text.pack_propagate(0)
    home_frame_3_LP_text.pack(side='bottom', fill='x')
    home_frame_3_LPpic = ctk.CTkImage(dark_image=Image.open("assets/icons/picinitial.png"),size=(200,120))
    home_frame_3_LPpic_label = ctk.CTkLabel(home_frame_3, image=home_frame_3_LPpic, text="")
    home_frame_3_LPpic_label.pack(anchor='c',pady=30)
    
    #Total Count Display
    home_frame_2 = ctk.CTkFrame(main_frame, width=200, height=250, fg_color='#064B71', corner_radius=10)
    home_frame_2.pack_propagate(0)
    home_frame_2.place(x=1100,y=240)
    home_frame_2_title = ctk.CTkLabel(home_frame_2, height=50, text = 'Entry Count', fg_color=main_color, text_color='white', font=(my_font_bold, 25), wraplength=200)
    home_frame_2_title.pack_propagate(0)
    home_frame_2_title.pack(fill='x')
    home_frame_2_count = ctk.CTkLabel(home_frame_2, height=50, text = '', fg_color='transparent', text_color='white', font=(my_font_bold, 45), wraplength=200, justify='center')
    home_frame_2_count.pack_propagate(0)
    home_frame_2_count.pack(anchor='c',fill='x',pady=35)
    home_frame_2_sidetext = ctk.CTkLabel(home_frame_2, height=50, text = 'Vehicles Recorded Today', fg_color='transparent', text_color='white', font=(my_font_italic, 15), wraplength=200)
    home_frame_2_sidetext.pack(side='bottom',pady=25)

    home_frame_4 = ctk.CTkFrame(main_frame, width=200, height=250, fg_color='#064B71', corner_radius=10)
    home_frame_4.pack_propagate(0)
    home_frame_4.place(x=1100,y=695)
    home_frame_4_title = ctk.CTkLabel(home_frame_4, height=50, text = 'Exit Count', fg_color=main_color, text_color='white', font=(my_font_bold, 25), wraplength=200)
    home_frame_4_title.pack_propagate(0)
    home_frame_4_title.pack(fill='x')
    home_frame_4_count = ctk.CTkLabel(home_frame_4, height=50, text = '', fg_color='transparent', text_color='white', font=(my_font_bold, 45), wraplength=200, justify='center')
    home_frame_4_count.pack_propagate(0)
    home_frame_4_count.pack(anchor='c',fill='x',pady=35)
    home_frame_4_sidetext = ctk.CTkLabel(home_frame_4, height=50, text = 'Vehicles Recorded Today', fg_color='transparent', text_color='white', font=(my_font_italic, 15), wraplength=200)
    home_frame_4_sidetext.pack(side='bottom',pady=25)

    

    def random_datapoint1(**kwargs):
        enorex = "Entry"
        if not os.path.exists(f'output/ANPR {enorex} {date_today}.csv'):
            headers = ['SNo', 'Camera', 'Entry/Exit', 'Date', 'Time', 'LicensePlate', 'Confidence Score', 'Image Path', 'Cropped Image']
            # Create a new CSV file
            with open(f'output/ANPR {enorex} {date_today}.csv', mode='w', newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
        data1 = pd.read_csv(f'output/ANPR Entry {date_today}.csv', encoding='latin-1')
        last_row1 = data1.tail(1)
        return last_row1
    def random_datapoint2(**kwargs):
        enorex = "Exit"
        if not os.path.exists(f'output/ANPR {enorex} {date_today}.csv'):
            headers = ['SNo', 'Camera', 'Entry/Exit', 'Date', 'Time', 'LicensePlate', 'Confidence Score', 'Image Path', 'Cropped Image']
            # Create a new CSV file
            with open(f'output/ANPR {enorex} {date_today}.csv', mode='w', newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
        data2 = pd.read_csv(f'output/ANPR Exit {date_today}.csv', encoding='latin-1')
        last_row2 = data2.tail(1)
        return last_row2
    
    df1 = PeriodicDataFrame(random_datapoint1, interval='1s')
    df2 = PeriodicDataFrame(random_datapoint2, interval='1s')


    def data_process1(last_row1):
        license_plate1 = last_row1['LicensePlate'].values[0]
        count1 = last_row1['SNo'].values[0]
        imagepath1 = last_row1['Cropped Image'].values[0]
        update_gui1(license_plate1, count1, imagepath1)

    def update_gui1(license_plate1, count1, imagepath1):
        try:
            if home_frame_1_LP_text.winfo_exists():
                home_frame_1_LP_text.configure(text=license_plate1)
                home_frame_1_LPpic.configure(dark_image=Image.open(imagepath1))
                home_frame_2_count.configure(text=count1)
        except Exception as e:
            print(f"Error! {e}")

    def data_process2(last_row2):
        license_plate2 = last_row2['LicensePlate'].values[0]
        count2 = last_row2['SNo'].values[0]
        imagepath2 = last_row2['Cropped Image'].values[0]
        update_gui2(license_plate2, count2, imagepath2)

    def update_gui2(license_plate2, count2, imagepath2):
        try:
            if home_frame_3_LP_text.winfo_exists():
                home_frame_3_LP_text.configure(text=license_plate2)
                home_frame_3_LPpic.configure(dark_image=Image.open(imagepath2),size=(200,120))
                home_frame_4_count.configure(text=count2)
        except Exception as e:
            print(f"Error! {e}")
    # Subscribe to the streaming data and update the Tkinter window
    df_stream1 = df1.stream.sink(data_process1)
    df_stream2 = df2.stream.sink(data_process2)

    try:
        df_stream1.start()  
        df_stream2.start()
        app.mainloop()  # Start the Tkinter main loop
    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        df_stream1.stop()
        df_stream2.stop()
        
    
    
# !!! HOME PAGE PACKING !!! #
    
# ~~~ TOTAL DATA PAGE PACKING ~~~ #
def total_data_page():
    def change_table_to_entry():
        theme['total_data']='Entry'
        for fm in total_data_table_frame.winfo_children():
            fm.destroy()
        table()
    def change_table_to_exit():
        theme['total_data']='Exit'
        for fm in total_data_table_frame.winfo_children():
            fm.destroy()
        table()
    total_data_heading_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
    total_data_heading_frame.pack_propagate(0)
    total_data_heading_frame.pack(fill='x')
    total_data_heading = ctk.CTkLabel(total_data_heading_frame, text= 'Recent Data Reads', text_color=main_color, fg_color="transparent", corner_radius=15, font=(my_font_bold, 50),width=240, height=55, anchor='w')
    total_data_heading.place(x=20,y=75)
    csv_logo=ctk.CTkImage(Image.open('assets/icons/csv.png'),size=(15,15))
    total_data_csv_button = ctk.CTkButton(total_data_heading_frame, image=csv_logo, text='  Main CSV File', fg_color=main_color, corner_radius=25, font=(my_font_bold, 15), hover_color="#085F8E",height=35, anchor='w',command=lambda: csv_press())
    total_data_csv_button.place(x=1350,y=20)
    refresh_logo=ctk.CTkImage(Image.open('assets/icons/refresh.png'),size=(15,15))
    total_data_refresh_button = ctk.CTkButton(total_data_heading_frame, image=refresh_logo, text='       Refresh', fg_color=main_color, corner_radius=25, font=(my_font_bold, 15), hover_color="#085F8E",width = 160, height=35, anchor='w',command=lambda: refresh_press())
    total_data_refresh_button.place(x=1350,y=120)
    total_data_table_frame = ctk.CTkFrame(main_frame,fg_color='transparent')
    total_data_table_frame.pack(padx=20,pady=20,expand=True, fill='both')

    total_data_entry_button = ctk.CTkButton(total_data_heading_frame, text='Entry Data', fg_color=main_color, corner_radius=25, font=(my_font_bold, 15), hover_color="#085F8E"
                                            ,width = 50, height=35, anchor='w',command=lambda: change_table_to_entry())
    total_data_entry_button.place(x=100,y=150)
    total_data_exit_button = ctk.CTkButton(total_data_heading_frame, text='Exit Data', fg_color=main_color, corner_radius=25, font=(my_font_bold, 15), hover_color="#085F8E",
                                           width = 50, height=35, anchor='w',command=lambda: change_table_to_exit())
    total_data_exit_button.place(x=300,y=150)

    table_enorex = theme['total_data']
    
    def refresh_press():
        refreshselect_logo=ctk.CTkImage(Image.open('assets/icons/refreshselect.png'),size=(15,15))
        total_data_refresh_button.configure(border_width=2,border_color=main_color,fg_color='white',text_color=main_color, hover=False, image=refreshselect_logo)
        total_data_heading_frame.after(150,refresh_press_after)
    def refresh_press_after():
        total_data_refresh_button.configure(fg_color=main_color,text_color='white', hover=True, image=refresh_logo)
        for fm in total_data_table_frame.winfo_children():
            fm.destroy()
        table()
    def csv_press():
        csvselect_logo=ctk.CTkImage(Image.open('assets/icons/csvselect.png'),size=(15,15))
        total_data_csv_button.configure(border_width=2,border_color=main_color,fg_color='white',text_color=main_color, hover=False, image=csvselect_logo)
        total_data_heading_frame.after(150,csv_press_after)
    def csv_press_after():
        total_data_csv_button.configure(fg_color=main_color,text_color='white', hover=True, image=csv_logo)
        if os.path.exists(f'output/ANPR {date_today}.csv'):
            webbrowser.open(f'output/ANPR {table_enorex} {date_today}.csv')
        else:
            print("File not found!")
        
    def table():
        table_enorex = theme['total_data']
        value = []
        data = pd.read_csv(f'output/ANPR {table_enorex} {date_today}.csv')
        last_50_rows = data.tail(50)
        last_50_rows['datetime'] = pd.to_datetime(last_50_rows['Date'] + ' ' + last_50_rows['Time'])
        last_50_rows_sorted = last_50_rows.sort_values(by='datetime', ascending=False)
        last_50_rows_sorted = last_50_rows_sorted.drop(columns=['datetime'])

        value.append(last_50_rows_sorted.columns.tolist())
        for i, row in last_50_rows_sorted.iterrows():
            value.append(list(row))

        table_frame = ctk.CTkScrollableFrame(master=total_data_table_frame, fg_color="transparent")
        table_frame.pack(expand=True, fill="both")
        table = CTkTable(master=table_frame, text_color='black',values=value, colors=["#E6E6E6", "#EEEEEE"], header_color=main_color, hover_color="#478BB1",command=open)
        table.edit_row(0, text_color="#000", hover_color="#478BB1")
        table.pack(expand=True)
    def open(block):
        col = block['column']
        cell_value= block['value']
        if col == 7 or col == 8:
            if os.path.isfile(cell_value) and cell_value.lower().endswith('.jpg'):
                img = Image.open(cell_value)
                img.show()
            else:
                print("Invalid file path or file is not a JPEG.")
        elif col == 5:
            pyperclip.copy(cell_value)
            copiedtoclip = ctk.CTkLabel(total_data_heading_frame,font=(my_font_italic,15), text="*Copied to Clipboard!*", fg_color='transparent', text_color=('#636363','#BBBBBB'))
            copiedtoclip.place(x=697,y=150)
            total_data_heading_frame.after(3000,copiedtoclip.destroy)
        else:
            print('Image Column not selected')
    table()

    
# !!! TOTAL DATA PAGE PACKING !!! #

# ~~~ SEARCH PAGE PACKING ~~~ #
def search_page():
    
    def open_cal_from():
        global calendar_frame1
        calendar_frame1 = ctk.CTkFrame(main_frame,width=350,height=350,fg_color='transparent', corner_radius=30)
        calendar_frame1.place(x=575,y=350)
        global search_dateentry
        search_dateentry=Calendar(calendar_frame1, font=(my_font_light,10), background=main_color,  
                  foreground='#000000', todaybackground  ='#207244', borderwidth=10,date_pattern='dd-MM-yyyy',text_color='#000000',
                  selectbackground='#064B71')
        search_dateentry.pack()
        submit_date=ctk.CTkButton(calendar_frame1,text='Select Date',height=30,font=(my_font_light,15),fg_color='#BBBBBB',bg_color='transparent' ,
                                  text_color='#5C5C5C',corner_radius=40,hover_color='#C7C7BD', command=lambda:send_date_from())
        submit_date.pack(anchor='w',padx=30,pady=10)
        close_cal_btn=ctk.CTkButton(calendar_frame1,text='X',width=0, height=30,font=(my_font_light,15),fg_color='#BBBBBB', 
                                  text_color='#5C5C5C',corner_radius=500,hover_color='#C7C7BD', command=lambda:close_cal_from())
        close_cal_btn.place(x=225,y=238)
        if calendar_frame2.winfo_exists():
            calendar_frame2.destroy()

    def open_cal_to():
        global calendar_frame2
        calendar_frame2 = ctk.CTkFrame(main_frame,width=350,height=350,fg_color='transparent')
        calendar_frame2.place(x=875,y=350)
        global search_dateentry
        search_dateentry=Calendar(calendar_frame2, font=(my_font_light,10), background=main_color,  
                  foreground='#495053', todaybackground  ='#207244', borderwidth=10,date_pattern='dd-MM-yyyy',text_color='#000000',
                  selectbackground='#064B71')
        search_dateentry.pack()
        submit_date=ctk.CTkButton(calendar_frame2,text='Select Date',height=30,font=(my_font_light,15),fg_color='#BBBBBB', bg_color='transparent' ,
                                  text_color='#5C5C5C',corner_radius=40,hover_color='#C7C7BD', command=lambda:send_date_to())
        submit_date.pack(anchor='w',padx=30,pady=10)
        close_cal_btn=ctk.CTkButton(calendar_frame2,text='X',width=0, height=30,font=(my_font_light,15),fg_color='#BBBBBB',bg_color='transparent' , 
                                  text_color='#5C5C5C',corner_radius=500,hover_color='#C7C7BD', command=lambda:close_cal_to())
        close_cal_btn.place(x=225,y=238)
        if calendar_frame1.winfo_exists():
            calendar_frame1.destroy()

    def send_date_from():
        selected_date = search_dateentry.get_date()
        search_date_from.configure(text=selected_date)
        calendar_frame1.destroy()

    def send_date_to():
        selected_date = search_dateentry.get_date()
        search_date_to.configure(text=selected_date)
        calendar_frame2.destroy()
        
    def close_cal_from():
        calendar_frame1.destroy()

    def close_cal_to():
        calendar_frame2.destroy()

    def search_csv_by_date():
        def open(block):
            col = block['column']
            cell_value= block['value']
            if col == 7 or col == 8:
                if os.path.isfile(cell_value) and cell_value.lower().endswith('.jpg'):
                    img = Image.open(cell_value)
                    img.show()
                else:
                    print("Invalid file path or file is not a JPEG.")
            elif col == 5:
                pyperclip.copy(cell_value)
                copiedtoclip = ctk.CTkLabel(main_frame,font=(my_font_italic,15), text="*Copied to Clipboard!*", fg_color='transparent', text_color=('#636363','#BBBBBB'))
                copiedtoclip.place(x=690,y=333)
                main_frame.after(3000,copiedtoclip.destroy)
            else:
                print('Image Column not selected')
        for fm in search_result_frame.winfo_children():
            fm.destroy()
        search_string=search_searchbar.get()
        if len(search_string) == 0:
            search_searchbar_empty = ctk.CTkLabel(main_frame,font=(my_font_italic,15), text="*Please enter some text first*", fg_color='transparent', text_color=('#636363','#BBBBBB'))
            search_searchbar_empty.place(x=200,y=330)
            main_frame.after(3000,search_searchbar_empty.destroy)
            return
        date_str_from=search_date_from.cget('text')
        start_date = datetime.strptime(date_str_from, '%d-%m-%Y')
        date_str_to=search_date_to.cget('text')
        end_date = datetime.strptime(date_str_to, '%d-%m-%Y')
        date_strs = []
        if start_date > end_date:
            search_result_err4 = ctk.CTkLabel(search_result_frame,font=(my_font_light,30), 
                                                            text=f"From date {date_str_from} cannot be after To Date {date_str_to}", fg_color='transparent', text_color='#5C5C5C')
            search_result_err4.place(x=0,y=10)
            search_result_frame.after(5000,search_result_err4.destroy)
            return
        cr_date = start_date
        while cr_date <= end_date:
            date_strs.append(cr_date.strftime('%d-%m-%Y'))
            cr_date += timedelta(days=1)
        # Specify the directory where the CSV files are located
        directory = 'output/'

        # List to store search results
        search_results = []

        # Iterate through files in the directory
        for filename in os.listdir(directory):
            # Check if the file is a CSV file and contains the specified date in its name
            if filename.endswith('.csv'):
                if any(date_str in filename for date_str in date_strs):
                    file_path = os.path.join(directory, filename)
                    # Read the CSV file into a DataFrame
                    df = pd.read_csv(file_path)

                    # Check if 'License Plate' column exists in the DataFrame
                    if 'LicensePlate' in df.columns:
                        # Perform the search in the 'License Plate' column
                        result = df[df['LicensePlate'].str.contains(search_string, na=False, case=False)]
                        if not result.empty:
                            search_results.append(result)
                        else:
                            print(f"No matching records found in {filename} for search string '{search_string}'")
                            search_result_err1 = ctk.CTkLabel(search_result_frame,font=(my_font_light,30), 
                                                            text=f"No matching records found in {filename} for search string '{search_string}'", fg_color='transparent', text_color='#5C5C5C')
                            search_result_err1.place(x=0,y=10)
                            search_result_frame.after(5000,search_result_err1.destroy)
                    else:
                        print(f"'License Plate' column not found in {filename}")
                        search_result_err2 = ctk.CTkLabel(search_result_frame,font=(my_font_light,30), 
                                                            text=f"'License Plate' column not found in {filename}", fg_color='transparent', text_color='#5C5C5C')
                        search_result_err2.place(x=0,y=10)
                        search_result_frame.after(5000,search_result_err2.destroy)
                
        if search_results:
            value = []
            headers = ['SNo', 'Camera', 'Entry/Exit','Date','Time', 'LicensePlate', 'Confidence Score', 'Image Path','Cropped Image']
            value.append(headers)
            for df in search_results:
                # Convert DataFrame to a list of lists and append to value
                value.extend(df.values.tolist())
            value.sort(key=lambda x: x[3], reverse=True)
            
            table_frame = ctk.CTkScrollableFrame(master=search_result_frame, fg_color="transparent")
            table_frame.pack(expand=True, fill="both")
            table = CTkTable(master=table_frame, text_color='black',values=value, colors=["#E6E6E6", "#EEEEEE"], header_color=main_color, hover_color="#064B71",command=open)
            table.edit_row(0, text_color="#000", hover_color="#2A8C55")
            table.pack(expand=True,fill='both')
            
        else:
            print(f"No CSV file found for date {date_str_from} and {date_str_to} containing '{search_string}'")
            search_result_err3 = ctk.CTkLabel(search_result_frame,font=(my_font_light,30), 
                                                            text=f"No CSV file found for date {date_str_from} and {date_str_to} containing '{search_string}'", fg_color='transparent', text_color='#5C5C5C')
            search_result_err3.place(x=0,y=50)
            search_result_frame.after(5000,search_result_err3.destroy)
            return None
    
        
    search_heading = ctk.CTkLabel(main_frame, text= 'Search', text_color=main_color, fg_color="transparent", corner_radius=15, font=(my_font_bold, 50),width=240, height=55, anchor='w')
    search_heading.place(x=20,y=75)
    search_result_frame = ctk.CTkFrame(main_frame,fg_color='transparent',height=600)
    search_result_frame.pack_propagate(0)
    search_result_frame.pack(padx=50,pady=50, fill='both',side='bottom')
    search_searchbar = ctk.CTkEntry(main_frame, width=500, height=75, font=(my_font_light,30), 
                                      placeholder_text="Search your License Plate", fg_color='transparent', text_color=('#636363','#BBBBBB'), 
                                      placeholder_text_color=('#636363','#BBBBBB'),corner_radius=40,border_color=('#636363','#BBBBBB'),border_width=3)
    search_searchbar.place(x=150,y=250)
    search_date_from = ctk.CTkButton(main_frame, text=date_today,width=250,height=75, font=(my_font_light,30),fg_color='transparent',text_color=('#636363','#BBBBBB'),
                               corner_radius=40,border_color=('#636363','#BBBBBB'),border_width=3, hover_color=('#BBBBBB','#636363'),command=lambda: open_cal_from())
    search_date_from.place(x=700,y=250)
    search_date_to = ctk.CTkButton(main_frame, text=date_today,width=250,height=75, font=(my_font_light,30),fg_color='transparent',text_color=('#636363','#BBBBBB'),
                               corner_radius=40,border_color=('#636363','#BBBBBB'),border_width=3, hover_color=('#BBBBBB','#636363'),command=lambda: open_cal_to())
    search_date_to.place(x=1000,y=250)
    search_main_logo = ctk.CTkImage(light_image=Image.open('assets/icons/search_main_light.png'),size=(25,25),
                                    dark_image=Image.open('assets/icons/search_main_dark.png'))
    search_main = ctk.CTkButton(main_frame, image=search_main_logo, text='',width=0, height=75,fg_color='transparent',text_color=('#636363','#BBBBBB'),
                               corner_radius=100,border_color=('#636363','#BBBBBB'),border_width=3, hover_color=('#BBBBBB','#636363'),command=lambda:search_csv_by_date())
    search_main.place(x=1300,y=250)

    search_searchbar_title= ctk.CTkLabel(main_frame,font=(my_font_light,25), text="License Plate:", fg_color='transparent', text_color=('#636363','#BBBBBB'))
    search_searchbar_title.place(x=165,y=200)
    search_fromdate_title= ctk.CTkLabel(main_frame,font=(my_font_light,25), text="From:", fg_color='transparent', text_color=('#636363','#BBBBBB'))
    search_fromdate_title.place(x=715,y=200)
    search_todate_title= ctk.CTkLabel(main_frame,font=(my_font_light,25), text="To:", fg_color='transparent', text_color=('#636363','#BBBBBB'))
    search_todate_title.place(x=1015,y=200)

# !!! SEARCH PAGE PACKING !!! #
    
# ~~~ SETTINGS PAGE PACKING ~~~ #
    
def settings_page():    
    
    def switch_to_lightmode():
        theme['appearance_mode']="light"
        ctk.set_appearance_mode('light')
        save_theme(theme,json_file_path)

    def switch_to_darkmode():
        theme['appearance_mode']="dark"
        ctk.set_appearance_mode('dark')
        save_theme(theme,json_file_path)

    def change_entry_ip():
        theme['ip_adr1']=settings_entryfield.get()
        save_theme(theme,json_file_path)    

    def change_exit_ip():
        theme['ip_adr2']=settings_exitfield.get()
        save_theme(theme,json_file_path)      
    
    settings_heading = ctk.CTkLabel(main_frame, text= 'Settings', text_color=main_color, fg_color="transparent", corner_radius=15, font=(my_font_bold, 50),width=240, height=55, anchor='w')
    settings_heading.place(x=20,y=75)
    settings_main_frame = ctk.CTkScrollableFrame(main_frame,fg_color='transparent',width=1400,height=750)
    settings_main_frame.place(x=100,y=200)

    settings_heading.bind("<1>", lambda event: event.widget.focus_set())
    settings_main_frame.bind("<1>", lambda event: event.widget.focus_set())
    main_frame.bind("<1>", lambda event: event.widget.focus_set())

    settings_sp_main = ctk.CTkLabel(settings_main_frame,text='System Preferences',font=(my_font_bold,50),text_color=('#636363','#BBBBBB'),fg_color='transparent')
    settings_sp_main.pack(anchor='w',padx=5,pady=25)
    settings_sp_main.bind("<1>", lambda event: event.widget.focus_set())
    settings_apmode = ctk.CTkLabel(settings_main_frame,text='Appearance Mode',font=(my_font_light,40),text_color=('#636363','#BBBBBB'),fg_color='transparent')
    settings_apmode.pack(anchor='w',padx=150,pady=25)
    settings_apmode.bind("<1>", lambda event: event.widget.focus_set())
    settings_apmode_light = ctk.CTkButton(settings_main_frame,text='Light',font=(my_font_light,30),width=225,height=50,fg_color='transparent',text_color=('#636363','#BBBBBB'),
                               corner_radius=40,border_color=('#636363','#BBBBBB'),border_width=3, hover_color=('#BBBBBB','#636363'),command=lambda:switch_to_lightmode())
    settings_apmode_light.place(x = 645, y=152)
    settings_apmode_light.bind("<1>", lambda event: event.widget.focus_set())
    settings_apmode_dark = ctk.CTkButton(settings_main_frame,text='Dark',font=(my_font_light,30),width=225,height=50,fg_color='transparent',text_color=('#636363','#BBBBBB'),
                               corner_radius=40,border_color=('#636363','#BBBBBB'),border_width=3, hover_color=('#BBBBBB','#636363'),command=lambda:switch_to_darkmode())
    settings_apmode_dark.place(x = 950, y=152)
    settings_apmode_dark.bind("<1>", lambda event: event.widget.focus_set())

    settings_camera_main = ctk.CTkLabel(settings_main_frame,text='Camera Configuration',font=(my_font_bold,50),text_color=('#636363','#BBBBBB'),fg_color='transparent')
    settings_camera_main.pack(anchor='w',padx=5,pady=(40,25))
    settings_camera_main.bind("<1>", lambda event: event.widget.focus_set())

    settings_entry_title = ctk.CTkLabel(settings_main_frame,text='Entry ANPR Camera IP',font=(my_font_light,40),text_color=('#636363','#BBBBBB'),fg_color='transparent')
    settings_entry_title.pack(anchor='w',padx=150,pady=25)
    settings_entry_title.bind("<1>", lambda event: event.widget.focus_set())
    settings_entryfield = ctk.CTkEntry(settings_main_frame,placeholder_text=theme['ip_adr1'],font=(my_font_light,30),text_color=('#636363','#BBBBBB'),fg_color='transparent'
                                       ,placeholder_text_color=('#636363','#BBBBBB'),width=350,height=50,corner_radius=40)
    settings_entryfield.place(x=645,y=395)
    settings_entryfield_submit = ctk.CTkButton(settings_main_frame,text='Change',font=(my_font_light,20),width=50,height=50,fg_color='transparent',text_color=('#636363','#BBBBBB'),
                               corner_radius=40,border_color=('#636363','#BBBBBB'),border_width=3, hover_color=('#BBBBBB','#636363'),command=lambda:change_entry_ip())
    settings_entryfield_submit.place(x = 1050, y=395)
    settings_entryfield_submit.bind("<1>", lambda event: event.widget.focus_set())

    settings_exit_title = ctk.CTkLabel(settings_main_frame,text='ExitANPR Camera IP',font=(my_font_light,40),text_color=('#636363','#BBBBBB'),fg_color='transparent')
    settings_exit_title.pack(anchor='w',padx=150,pady=25)
    settings_exit_title.bind("<1>", lambda event: event.widget.focus_set())
    settings_exitfield = ctk.CTkEntry(settings_main_frame,placeholder_text=theme['ip_adr2'],font=(my_font_light,30),text_color=('#636363','#BBBBBB'),fg_color='transparent'
                                       ,placeholder_text_color=('#636363','#BBBBBB'),width=350,height=50,corner_radius=40)
    settings_exitfield.place(x=645,y=495)
    settings_exitfield_submit = ctk.CTkButton(settings_main_frame,text='Change',font=(my_font_light,20),width=50,height=50,fg_color='transparent',text_color=('#636363','#BBBBBB'),
                               corner_radius=40,border_color=('#636363','#BBBBBB'),border_width=3, hover_color=('#BBBBBB','#636363'),command=lambda:change_exit_ip())
    settings_exitfield_submit.place(x = 1050, y=495)
    settings_exitfield_submit.bind("<1>", lambda event: event.widget.focus_set())
    settings_cc_placeholder= ctk.CTkLabel(settings_main_frame,font=(my_font_italic,15), text="*Please refresh the application to show camera changes*", fg_color='transparent', text_color=('#636363','#BBBBBB'),bg_color='transparent')
    settings_cc_placeholder.place(x=150,y=535)
    
# !!! SETTINGS PAGE PACKING !!! 

switch_to_home(home_btn)
CheckStorage('output/')
MergeCSVs()
app.mainloop()
try:
    stop_main_script_from_file()
except:
    print("Main scirpt already stopped")