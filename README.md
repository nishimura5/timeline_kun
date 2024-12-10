# Timeline-kun 0.2.0
Timeline-kun is an application that generates timers from experimental timelines created in CSV format. It automates complex experiment schedule management, helping to reduce the burden on both experimenters and participants.

## Screen shot

<p align="center">
<img src="https://www.design.kyushu-u.ac.jp/~eigo/image/timeline_kun_020.png" width="70%">
<br>
<img src="https://www.design.kyushu-u.ac.jp/~eigo/image/timeline_kun_020_2.png" width="70%">
<br>
<img src="https://www.design.kyushu-u.ac.jp/~eigo/image/timeline_kun_020_3.png" width="70%">
</p>

## Interface

### CSV file

Clicking the "Create CSV" button will create a CSV file template in the appropriate format.

 - Encoding: UTF-8 (or Shift-JIS, as needed)
 - Header: The first line must contain column headers.
 - Delimiter: Comma-separated (,).
 - Blank cell: Leave cells blank (,,).

| Column name | member                                                                |
| ----------- | --------------------------------------------------------------------- |
| title       | The name or identifier of the task.                                   |
| member      | The participant or team responsible for the task.                     |
| start       | The start time of the task (formatted as H:MM:SS).                    |
| duration    | The duration of the task (formatted as H:MM:SS).                      |
| end         | Optional. The end time of the task (formatted as H:MM:SS)             |
| fixed       | Specifies if the start time or duration is fixed (start or duration). |
| instruction | Additional instructions or comments related to the task.              |

Example is below.

| title  | member  | start   | duration | fixed    | instruction |
| ------ | ------- | ------- | -------- | -------- | ----------- |
| TASK A | MEMBER1 | 0:00:00 |          | start    |             |
| TASK B | MEMBER1 | 0:04:00 | 0:05:00  | start    |             |
| TASK C | MEMBER1 |         | 0:05:00  | duration |             |
| ...    | ...     | ...     | ...      | ...      | ...         |

日本語環境にも対応しています。

### Log file

The timer application outputs a log file in CSV format.

- File name: "log_{date}_{source csv file name}.csv"
- Delimiter: Comma-separated (,).

Example is below.

| datetime  | start  | member | title |
| ------ | ------- | ------- | -------- |
| 2024-10-24 17:26:32 | 0:00:00 | MEMBER1 | TASK A |
| 2024-10-24 17:30:32 | 0:04:00 | MEMBER1 | TASK B |
| 2024-10-24 17:35:32 | 0:09:00 | MEMBER1 | TASK C |
| ...    | ...     | ...     | ...      |

### Sound file

The timer application will load a 3-second wav file and play it as an alarm. The wav file will be stored in the “sound” folder with the following file name.

 - countdown3_orange.wav
 - countdown3_cyan.wav
 - countdown3_lightgreen.wav
