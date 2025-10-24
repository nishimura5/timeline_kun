# Timeline-kun 1.0.0

[![DOI](https://zenodo.org/badge/DOI/10.48708/7325764.svg)](https://doi.org/10.48708/7325764)
[![BIDS Compatible](https://img.shields.io/badge/BIDS-compatible-brightgreen)](https://bids.neuroimaging.io/)
[![GoPro](https://img.shields.io/badge/GoPro-HERO11%20%2B-4cbee0?logo=gopro&logoColor=white)](https://gopro.com)
[![Release](https://img.shields.io/github/v/release/nishimura5/timeline_kun)](https://github.com/nishimura5/timeline_kun/releases)

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

Timeline-kun integrates four primary functionalities:

1. **Simplifying the planning of complex experimental schedules**
   - Visually represents experimental schedules
   - Stores schedule data in CSV format
   - Allows intuitive insertion, deletion, and reordering of events using Excel

2. **Integrating schedule planning and execution in a single tool**
   - Experimental schedules created with this tool can be directly used as timers
   - Timer can be started from any point, allowing test executions or real-time schedule modifications
   - Supports custom alarm sounds using 3-second WAV files

3. **Controlling GoPro devices**
   - Start and stop recording based on schedules via BLE
   - Simultaneous control of multiple devices
   - Support for long standby times through keep-alive signals sent every 3 seconds
   
4. **Improving methodological transparency and reproducibility**
   - TSV log records in BIDS compliant events.tsv format
   - Deviations due to interruptions or running ahead can be reviewed later
   - Provides SVG export function suitable for experimental planning discussions and record-keeping

## Installation and Execution

### Windows
1. Download and extract the ZIP file from the [latest release](https://github.com/nishimura5/timeline_kun/releases)
2. Double-click "TimelineKun.exe" to run the application

### From PyPI
```
uv add timeline-kun
uv run timeline-kun
```
or
```
pip install timeline-kun
python -m timeline_kun
```

### Running from development environment
1. Clone the repository: `git clone https://github.com/nishimura5/timeline_kun.git`
2. Set up the environment using uv (simply run "uv sync" in the directory containing pyproject.toml)
3. Run below in the directory containing pyproject.toml to launch

```
uv run python -m timeline_kun
```

*Note: macOS users will need to install tcl-tk and configure appropriate environment variables before installation as this tool relies on tkinter.*

## Timeline CSV File Format

The timeline CSV file uses the following columns:

- **title**: The name of the event displayed on the timer screen
- **member**: The participant or team responsible for the event
- **start**: The start time of the event (formatted as H:MM:SS)
- **duration**: The duration of the event (formatted as H:MM:SS)
- **fixed**: Specifies whether the start time or duration is fixed (values: "duration" or "start")
- **instruction**: Additional instructions or comments
- **end**: Optional. End time of the event (formatted as H:MM:SS)

### For LLM-based Generation

For LLM-based generation (like [ChatGPT](https://chatgpt.com) or [Claude](https://claude.ai)), you can use [this JSON schema](https://github.com/nishimura5/timeline_kun/blob/main/schemas/timeline_kun_csv.schema.json).

To use it, either download the JSON file from the link or copy-paste its contents directly into your prompt, then instruct the LLM to generate your experimental timeline.

### CSV File Example (Timeline CSV)

```
title,member,start,duration,fixed,instruction
TASK A,MEMBER1,0:00:00,,start,Prepare for TASK B (recording)
TASK B,MEMBER1,0:04:00,0:05:00,start,Prepare for TASK C
TASK C,MEMBER1,,0:05:00,duration,
```

| title  | member  | start   | duration | fixed    | instruction |
| ------ | ------- | ------- | -------- | -------- | ----------- |
| TASK A | MEMBER1 | 0:00:00 |          | start    | Prepare for TASK B (recording) |
| TASK B | MEMBER1 | 0:04:00 | 0:05:00  | start    | Prepare for TASK C |
| TASK C | MEMBER1 |         | 0:05:00  | duration |             |
| ...    | ...     | ...     | ...      | ...      | ...         |

For Japanese user: Excelで編集したCSVファイル（つまりShift-JISでエンコーディングされたCSVファイル）も読み込むことができます。最初にUTF-8での読み込みを試みて、失敗するとShift-JISにフォールバックします。

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

Timer execution logs conform to the BIDS (Brain Imaging Data Structure) events.tsv format. The log files are stored in the same directory as the Timeline CSV file, with file names in the format:

\<timeline_csv_name\>_00_events.tsv.

Each time the timer is started, the number (00) is incremented and saved.

A sample log is shown below:

```
onset	duration	trial_type
0.0	60.0	TASK A
66.2	0.0	video_record_start
60.0	10.1	Intermission
70.0	89.9	TASK B
179.6	0.0	task_skip
160.0	22.7	TASK C
182.6	60.0	TASK D
242.6	20.0	Intermission
262.7	60.0	TASK E
322.7	0.0	session_end
```

## Sound File

The timer application will load a 3-second wav file and play it as an alarm. The wav file will be stored in the "sound" folder with the following file names:

- countdown3_orange.wav
- countdown3_cyan.wav
- countdown3_lightgreen.wav

MMCV: ずんだもん

## Citation

Please acknowledge and cite the use of this software and its authors when results are used in publications or published elsewhere.

```
Nishimura, E. (2025). Timeline-kun (Version 1.0) [Computer software]. Kyushu University, https://doi.org/10.48708/7325764
```

```
@misc{timeline-kun-software,
  title = {Timeline-kun},
  author = {Nishimura, Eigo},
  year = {2025},
  publisher = {Kyushu University},
  doi = {10.48708/7325764},
  note = {Available at: \url{https://hdl.handle.net/2324/7325764}},
}
```
