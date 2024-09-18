#.srt to .TextGrid bulk converter
#written in python 3


import codecs
import sys
import datetime
import re
import numpy
import os
from itertools import groupby
from collections import namedtuple
from pathlib import Path

# Define the input and output folders
input_folder = r"C:\Users\julia\Documents\Computer_Docs\Test_SRT\Test_Input_SRT"
output_folder = r"C:\Users\julia\Documents\Computer_Docs\Test_SRT\Test_Output_Textgrid"

# Ensure the output folder exists
Path(output_folder).mkdir(parents=True, exist_ok=True)

# Define a class for intervals based on the basic template for an SRT interval
class srtInterval:
    def __init__(self, number, range, content):
        self.number = number[:]
        self.range = range[:]
        self.startTime, self.endTime = range[:].split(" --> ")
        self.content = content.replace('"', '""')
    
    def __str__(self):
        return "index: "+str(self.number) + "\ntimes: " + str(self.range) +"\ncontent: " + self.content

def createMissingInterval(currentInterval, nextInterval):
    newNumber = currentInterval.number + ".5"
    newRange = currentInterval.endTime + " --> " + nextInterval.startTime
    newContent = "."
    return srtInterval(newNumber, newRange, newContent)

def updateIntervals(srtintervals):
    for i in range(len(srtintervals)):
        srtintervals[i].number = str(i+1)
    return srtintervals

def createInitialSilence(endTime):
    newRange = "00:00:00,000 --> " + endTime
    return srtInterval("0", newRange, ".")

def process_file(inFile, outFile, output_file_path):
    print(f"Processing file: {inFile}")

    # Read and clean up SRT input file
    srtintervals = []
    with codecs.open(inFile, 'r', 'utf-8') as iFile:
        lines = iFile.read().splitlines()
        if lines[-1] != "":
            lines.append("")
        
        linesTemp = []
        for i in range(len(lines) - 1):
            if lines[i] == '' and lines[i + 1] == '':
                print(f'There was a blank line at index {i} before another blank line. It was removed ')
            else:
                linesTemp.append(lines[i])
        linesTemp.append(lines[-1])
        lines = linesTemp

        lines[0] = lines[0].replace('\ufeff', "")
        lineCounter = 0
        while lineCounter < len(lines):
            tempIndex = lines[lineCounter]
            lineCounter += 1
            tempTime = lines[lineCounter]
            lineCounter += 1
            tempContent = lines[lineCounter]
            lineCounter += 1
            seeNewLine = len(lines[lineCounter]) < 1
            while not seeNewLine:
                tempContent += "\n" + lines[lineCounter]
                lineCounter += 1
                seeNewLine = len(lines[lineCounter]) < 1
            lineCounter += 1

            currentInterval = srtInterval(tempIndex, tempTime, tempContent)
            srtintervals.append(currentInterval)

    # Check for timing errors
    foundTimingError = False
    for i in range(len(srtintervals) - 1):
        currentInterval = srtintervals[i]
        nextInterval = srtintervals[i + 1]
        if currentInterval.endTime > nextInterval.startTime:
            print("Error, the following two consecutive intervals have contradictory times")
            print("Interval A:", currentInterval)
            print("Interval B", nextInterval)
            foundTimingError = True
            break
    if foundTimingError: return

    # Add missing intervals
    strIntervalsCounter = 0
    while strIntervalsCounter < len(srtintervals) - 1:
        i = strIntervalsCounter
        currentInterval = srtintervals[i]
        nextInterval = srtintervals[i + 1]
        if currentInterval.endTime != nextInterval.startTime:
            newInterval = createMissingInterval(currentInterval, nextInterval)
            srtintervals.insert(i + 1, newInterval)
        strIntervalsCounter += 1

    # Add initial silence if needed
    if srtintervals[0].startTime != "00:00:00,000":
        newInterval = createInitialSilence(srtintervals[0].startTime)
        srtintervals.insert(0, newInterval)

    # Update interval indexes
    srtintervals = updateIntervals(srtintervals)

    # Write cleaned SRT file
    with codecs.open(outFile, 'w', 'utf-8') as o:
        for line in srtintervals:
            o.writelines(line.number + '\n')
            o.writelines(line.range + '\n')
            o.writelines(line.content + '\n\n')

    # Convert cleaned SRT to TextGrid
    with open(outFile) as f:
        res = [list(g) for b, g in groupby(f, lambda x: bool(x.strip())) if b]

    output_file = open(output_file_path, 'w')

    Subtitle = namedtuple('Subtitle', 'number start end content')
    subs = []
    for sub in res:
        if len(sub) >= 3:
            sub = [x.strip() for x in sub]
            number, start_end, *content = sub
            start, end = start_end.split(' --> ')
            subs.append(Subtitle(number, start, end, content))

    listOfTimes = []
    for s in subs:
        listOfTimes.append(s.start)
        listOfTimes.append(s.end)

    mydates = [datetime.datetime.strptime(listOfTimes[x], "%H:%M:%S,%f").time() for x in range(len(listOfTimes))]
    milliseconds = numpy.array([x.microsecond for x in mydates]) / 1000000
    seconds = numpy.array([x.second for x in mydates])
    minutes = numpy.array([x.minute for x in mydates]) * 60
    hours = numpy.array([x.hour for x in mydates]) * 60 * 60
    times = milliseconds + seconds + minutes + hours
    numberOfIntervals = times.size // 2
    maxTime = max(times)

    text = []
    for s in subs:
        _ = ""
        for t in s.content:
            _ += t + " | "
        text.append(_[:-3])

    # Write TextGrid preamble
    output_file.write("File type = \"ooTextFile\"" + '\n')
    output_file.write("Object class = \"TextGrid\"" + '\n')
    output_file.write('\n')
    output_file.write("xmin = 0" + '\n')
    output_file.write("xmax = " + str(maxTime) + '\n')
    output_file.write("tiers? <exists>" + '\n')
    output_file.write("size = 1" + '\n')
    output_file.write("item []: " + '\n')
    output_file.write("\t item [1]:" + '\n')
    output_file.write("\t\t class = \"IntervalTier\"" + '\n')
    output_file.write("\t\t name = \"silences\"" + '\n')
    output_file.write("\t\t xmin = 0" + '\n')
    output_file.write("\t\t xmax = " + str(maxTime) + '\n')
    output_file.write("\t\t intervals: size = " + str(numberOfIntervals) + '\n')

    for i in range(1, numberOfIntervals + 1):
        output_file.write("\t\t intervals [" + str(i) + "]:" + "\n")
        output_file.write("\t\t\t xmin = " + str(times.item((i * 2) - 2)) + "\n")
        output_file.write("\t\t\t xmax = " + str(times.item((i * 2) - 1)) + "\n")
        output_file.write("\t\t\t text = \"" + text[i - 1] + "\"\n")

    output_file.close()

# Process each .srt file in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".srt"):
        inFile = os.path.join(input_folder, filename)
        outFile = os.path.join(output_folder, filename.replace(".srt", "_Cleaned.srt"))
        output_file_path = os.path.join(output_folder, filename.replace(".srt", ".TextGrid"))
        process_file(inFile, outFile, output_file_path)

print("Processing complete.")
