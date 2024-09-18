import re
import os

input_folder = r"C:\Users\julia\Documents\Computer_Docs\Test_SRT\Input_SRT"
output_folder = r"C:\Users\julia\Documents\Computer_Docs\Test_SRT\Cleaned_SRT"

# Function to remove entries by Speaker1, handle implicit continuation of Speaker2,
# remove the "Speaker2:" tag, and renumber the subtitles for each SRT file
def filter_srt(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
            print(f"Processing file: {input_file}")  # Debugging message
            srt_block = []
            keep_block = False
            speaker2_active = False  # Track if Speaker2's dialogue is active
            subtitle_counter = 1  # To renumber the subtitles

            for line in infile:
                # Debugging: show each line being read
                print(f"Reading line: {line.strip()}")

                # If the line is a block number (new SRT block), process the previous block
                if re.match(r'^\d+\s*$', line.strip()):
                    if srt_block and keep_block:
                        # Remove "Speaker2:" from the block before writing and renumber it
                        srt_block = [re.sub(r'^Speaker2:\s*', '', l) for l in srt_block]
                        srt_block[0] = f"{subtitle_counter}\n"  # Renumber the subtitle
                        outfile.write("".join(srt_block))  # Write the previous block
                        subtitle_counter += 1  # Increment the subtitle number

                    srt_block = [line]  # Start a new block
                    keep_block = False  # Reset the keep flag for the new block
                else:
                    srt_block.append(line)  # Accumulate lines in the current block

                # Check if the current block contains "Speaker2"
                if "Speaker2:" in line:
                    keep_block = True
                    speaker2_active = True  # Mark Speaker2 as actively speaking

                # Check if the current block contains "Speaker1"
                elif "Speaker1:" in line:
                    keep_block = False  # Stop writing Speaker1's dialogue
                    speaker2_active = False  # Reset Speaker2 active flag

                # Continue writing if Speaker2 is still active but there's no explicit speaker tag
                elif speaker2_active:
                    keep_block = True

            # Write the last block if it should be kept and remove "Speaker2:" and renumber it
            if srt_block and keep_block:
                srt_block = [re.sub(r'^Speaker2:\s*', '', l) for l in srt_block]
                srt_block[0] = f"{subtitle_counter}\n"  # Renumber the last subtitle
                outfile.write("".join(srt_block))

        print(f"Filtered and renumbered SRT saved as {output_file}")

    except Exception as e:
        print(f"An error occurred while processing {input_file}: {e}")

# Bulk process SRT files from input_folder to output_folder
def bulk_process_srt(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # Check if input folder exists and contains files
    if not os.path.exists(input_folder):
        print(f"Input folder {input_folder} does not exist!")
        return

    # Iterate over all files in the input folder
    files_processed = 0
    for filename in os.listdir(input_folder):
        if filename.endswith(".srt"):  # Process only SRT files
            input_file = os.path.join(input_folder, filename)
            output_file = os.path.join(output_folder, filename)

            print(f"Processing file: {input_file}")
            filter_srt(input_file, output_file)
            files_processed += 1

    if files_processed == 0:
        print(f"No .srt files found in {input_folder}")
    else:
        print(f"Processed {files_processed} SRT files.")

# Example usage
bulk_process_srt(input_folder, output_folder)
