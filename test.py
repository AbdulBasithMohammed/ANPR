import os
import re
import pandas as pd

# Dictionary to store CSV files grouped by date
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
            dfs = [pd.read_csv(os.path.join('output/', file)) for file in files]
            merged_df = pd.concat(dfs)
            output_file_path = f'output/merged_{date}.csv'
            merged_df.to_csv(output_file_path, index=False)

            # Delete old files after merging
            for file in files:
                os.remove(os.path.join('output/', file))
            
            print(f"Merged files for {date} and saved as {output_file_path}")
        else:
            print(f"Not enough files to merge for {date}")
