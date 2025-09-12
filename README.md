# Timeline-kun 1.0.0

Timeline-kun is an integrated graphical interface tool for planning and executing experimental protocols.

## Screen shot

<p align="center">
<img src="https://www.design.kyushu-u.ac.jp/~eigo/image/timeline-kun/timeline_kun_020.png" width="70%">
<br>
<img src="https://www.design.kyushu-u.ac.jp/~eigo/image/timeline-kun/timeline_kun_020_2.png" width="70%">
<br>
<img src="https://www.design.kyushu-u.ac.jp/~eigo/image/timeline-kun/timeline_kun_020_3.png" width="70%">
</p>

## Key Features

Timeline-kun integrates three primary functionalities:

1. **Simplifying the planning of complex experimental schedules**
   - Visually represents experimental schedules
   - Stores schedule data in CSV format (time values formatted as 'H:MM:SS' for Excel compatibility)
   - Allows intuitive insertion, deletion, and reordering of events using Excel
   - Supports UTF-8 encoded CSV files, enabling editing in plain text editors
   - Provides SVG export function suitable for experimental planning discussions and record-keeping

2. **Integrating schedule planning and execution in a single tool**
   - Experimental schedules created with this tool can be directly used as timers
   - Timer interface displays the current event, upcoming event, and remaining time in a clear layout
   - Timer can be started from any point, allowing test executions or real-time schedule modifications
   - Supports custom alarm sounds using 3-second WAV files

3. **Improving methodological transparency and reproducibility**
   - Log function records timer operations in CSV format, capturing both planned and actual times
   - Deviations due to interruptions or delays can be reviewed later
   - Output files are compatible with standard analysis tools
   - SVG diagrams can be used in academic papers and edited with vector tools

## Installation and Execution

### Windows
1. Download and extract the ZIP file from the [latest release](https://github.com/nishimura5/timeline_kun/releases)
2. Double-click "TimelineKun.exe" to run the application

### Running from development environment
1. Clone the repository: `git clone https://github.com/nishimura5/timeline_kun.git`
2. Set up the environment using uv (simply run "uv sync" in the directory containing pyproject.toml)
3. Run "uv run python src/app_previewer.py" in the directory containing pyproject.toml to launch

*Note: macOS users will need to install tcl-tk and configure appropriate environment variables before installation as this tool relies on tkinter.*

## Timeline CSV File Format

The timeline CSV file uses the following columns:

- **title**: The name of the event displayed on the timer screen (duplicate names are allowed)
- **member**: The participant or team responsible for the event
- **start**: The start time of the event (formatted as H:MM:SS)
- **duration**: The duration of the event (formatted as H:MM:SS)
- **fixed**: Specifies whether the start time or duration is fixed (values: "duration" or "start")
- **instruction**: Additional instructions or comments
- **end**: Optional. End time of the event (formatted as H:MM:SS)

### CSV File Example (Timeline CSV)

```
title,member,start,duration,fixed,instruction
TASK A,MEMBER1,0:00:00,,start,Prepare for TASK B
TASK B,MEMBER1,0:04:00,0:05:00,start,Prepare for TASK C
TASK C,MEMBER1,,0:05:00,duration,
```

| title  | member  | start   | duration | fixed    | instruction |
| ------ | ------- | ------- | -------- | -------- | ----------- |
| TASK A | MEMBER1 | 0:00:00 |          | start    | Prepare for TASK B(recording) |
| TASK B | MEMBER1 | 0:04:00 | 0:05:00  | start    | Prepare for TASK C |
| TASK C | MEMBER1 |         | 0:05:00  | duration |             |
| ...    | ...     | ...     | ...      | ...      | ...         |

CSVは日本語にも対応しています。

### Scheduling Methods

There are two primary methods for determining event timing in Timeline-kun, which can be used exclusively or in combination:

1. **Duration-fixed scheduling**: When an event has a fixed duration but its start time depends on when the previous event ends. With this approach, the 'start' field is left empty, and events flow sequentially based on their durations. Set the value "duration" in the "fixed" column.

2. **Start-time-fixed scheduling**: When events must begin at specific elapsed times from the experiment start. In this approach, the 'duration' field can be left empty for events where only the start time matters (except in the last row). Set the value "start" in the "fixed" column.

## Usage Procedure

### Timeline creation and visualization:

1. Press the "Create CSV" button to create timeline data
2. Press the "Send to Excel" button to edit the timeline data in Excel
3. Press the "Reload" button to visualize the timeline data and check for any input errors
4. If you wish to start timing from the middle of the timeline, select the desired event from the table, right-click, and select the "Set start point" menu
5. Press the "Send to Timer" button to launch the timer

### Timer operation:

1. Press the "Sound test" button to check the speaker volume
2. Press the "Start" button to begin the timer
3. Press the "Skip" button to skip the current event
4. To end the timer, simply close the window

## Tips

- Time display format can be selected between "MM:SS" (like 90:00) and "H:MM:SS" (like 1:30:00)
- Custom WAV files can be used by replacing the file in the "sound" folder
- Users can select timer text colors from orange, cyan, and light green. Up to three timers can be operated simultaneously on a single PC
- SVG diagrams are editable using vector graphics tools such as Affinity Designer or Adobe Illustrator

## GoPro Control

For GoPro models starting from HERO11 that support BLE communication, recording can be automatically started 4 seconds before a specified event (for the first event, recording starts simultaneously with the event). By entering "(recording)" in the event instruction, that event will be marked for recording. It is possible to send commands to start and stop recording on multiple GoPro devices. The target GoPro devices for control are specified in ble_devices.toml. Below is an example configuration where each of the three timers is assigned to a different GoPro. The parameter stop_delay_sec specifies the delay time (in seconds) between the end of an event and stopping the recording.

```
[orange]
ble_names = ["GoPro 2700", "GoPro 4256"]
stop_delay_sec = 2

[cyan]
ble_names = ["GoPro 1320"]
stop_delay_sec = 2

[lightgreen]
ble_names = []
stop_delay_sec = 2
```

## Log File Format

Timer execution logs conform to the BIDS (Brain Imaging Data Structure) events.tsv format.

## Sound File

The timer application will load a 3-second wav file and play it as an alarm. The wav file will be stored in the "sound" folder with the following file names:

- countdown3_orange.wav
- countdown3_cyan.wav
- countdown3_lightgreen.wav

MMCV: ずんだもん


