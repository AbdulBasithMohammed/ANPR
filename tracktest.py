import cv2
import time
from ultralytics import YOLO

# Load the YOLOv8 model
model = YOLO('yolov8n.pt')


def AverageTimer(video_path,file_path):
    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Get the width and height of the video
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    cap.set(cv2.CAP_PROP_FPS,fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,2)

    start_times = {}
    end_times = {}
    total_time = {}
    reset_interval = 600
    last_reset_time = time.time()

    file = open(file_path,'w')

    # Loop through the video frames
    while cap.isOpened():
        # Read a frame from the video
        success, frame = cap.read()

        if success:
            # Run YOLOv8 tracking on the frame, persisting tracks between frames
            results = model.track(frame, persist=True, classes=[2,3,5,7], tracker="bytetrack.yaml")

            # Get the boxes and track IDs
            track_ids = results[0].boxes.id.int().cpu().tolist()

            # Updating track start times
            for track_id in track_ids:
                if track_id not in start_times:
                    start_times[track_id] = time.perf_counter()
                    

            # Updating track end times and calculating duration
            for track_id in list(start_times.keys()):
                if track_id not in track_ids:
                    end_times[track_id] = time.perf_counter()
                    duration = end_times[track_id] - start_times[track_id]
                    if track_id in total_time:
                        total_time[track_id] += duration
                    else:
                        total_time[track_id] = duration

            # Remove start and end times
            for track_id in list(start_times.keys()):
                if track_id not in track_ids:
                    start_times.pop(track_id)
            for track_id in list(end_times.keys()):
                if track_id in total_time:
                    end_times.pop(track_id)
            
            # Resetting total_time dictionary to get rid of historic data
            if time.time() - last_reset_time >= reset_interval:
                total_time = {}
                last_reset_time= time.time()
            
            # Calculating Average Time based on all recorded durations
            time_sum = sum(total_time.values())
            total_len = len(total_time)
            if total_len > 0:
                avg_time = time_sum / total_len
            else:
                avg_time = 0

            print('START\n',start_times)
            print('END\n',end_times)
            print('TOTAL TIME\n',total_time)
            print('AVG TIME\n',avg_time)

            # Write the average time to the text file
            file.seek(0)  # Move the file cursor to the beginning of the file
            file.write(f"{avg_time:.2f}")  # Write the new average time
            file.truncate()  # Remove any extra characters after the new average time

            # Visualize the results on the frame
            annotated_frame = results[0].plot()

            # Display the resized frame
            cv2.imshow("YOLOv8 Tracking", annotated_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Break the loop if the end of the video is reached
            break

    # Release the video capture object and close the display window
    cap.release()
    cv2.destroyAllWindows()

AverageTimer("exitramp.mp4","Zone1.txt")
# "beforeexitramp.mp4","Zone1.txt"
# "exitramp.mp4","Zone2.txt"
# "afterexitramp.mp4","Zone3.txt"
# "exitdriveway.mp4","Zone4.txt"