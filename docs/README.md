# Timeline-kun 0.2
Timeline-kun is an application that generates timers from experimental timelines created in CSV format. It automates complex experiment schedule management, helping to reduce the burden on both experimenters and participants.

## Screen shot

<p align="center">
<img src="https://www.design.kyushu-u.ac.jp/~eigo/image/timeline_kun_cap.png" width="80%">
<img src="https://www.design.kyushu-u.ac.jp/~eigo/image/timeline_kun_cap2.png" width="80%">  
</p>

## Interface

### CSV file

Clicking the "Create CSV" button will create a CSV file template in the appropriate format.

 - Encoding: UTF-8 (or Shift-JIS)
 - The first line: header

| title  | member  | start   | duration | fixed    | instruction |
| ------ | ------- | ------- | -------- | -------- | ----------- |
| TASK A | MEMBER1 | 0:00:00 |          | start    |             |
| TASK B | MEMBER1 | 0:04:00 | 0:05:00  | start    |             |
| TASK C | MEMBER1 |         | 0:05:00  | duration |             |
| ...    | ...     | ...     | ...      | ...      | ...         |
