# Streamlining Time Management for Experiments and Workshops

When you run experiments or workshops, you often have to manage sequences such as a 5-minute session, a 1-minute changeover, and then a 10-minute discussion. It is easy to stumble during both planning and execution when you try to handle this kind of time management by hand. Timeline-kun is a tool designed to support this sort of scheduling.

Timeline-kun is a desktop application that generates timers based on a schedule defined in a CSV file. You can download the Windows version here: [TimelineKun100.zip](https://github.com/nishimura5/timeline_kun/releases/download/v.1.0.0/TimelineKun100.zip). Unzip the archive and run the application.

## Example CSV Format

Create a CSV file in the following format:

| title        | member  | start | duration | fixed    | instruction                          |
|-------------|---------|-------|----------|----------|--------------------------------------|
| Session 1   | Member  |       | 0:05:00  | duration | 5-minute session                     |
| Changeover  | Manager |       | 0:01:00  | duration | Please perform the changeover        |
| Session 2   | Member  |       | 0:05:00  | duration | 5-minute session                     |
| Changeover  | Manager |       | 0:01:00  | duration | Please perform the changeover        |
| Session 3   | Member  |       | 0:05:00  | duration | 5-minute session                     |
| Discussion  | Manager |       | 0:10:00  | duration | 10-minute discussion                 |

When you load this CSV file into Timeline-kun, the application will display the schedule and the total required time. This makes it easy to grasp the overall duration and time allocation for each session at a glance.

![Screenshot of Timeline-kun main screen](./image/lecture/timeline_kun_chatgpt_1.webp)

If you click the **Send to timer** button in the upper-right corner, the timer screen appears and the countdown begins.

![Screenshot of Timeline-kun timer screen](./image/lecture/timeline_kun_chatgpt_2.webp)

## Preparing a Schema for ChatGPT

You can edit CSV files easily in Excel or a text editor, and for small adjustments you can also edit them directly within the Timeline-kun application. However, when you need to create a complex schedule, it is even more convenient to make use of ChatGPT.

Here we show an example prompt for ChatGPT that generates a CSV file for Timeline-kun.

Before the prompt itself, we first explain the schema. What we want is CSV data that follows the format that Timeline-kun can read. The column names (the first-row headers such as `title` and `member`) must be exact, and time formats (`h:mm:ss`) must not be ambiguous.

In such cases, providing a schema helps improve the accuracy of the generated data. Timeline-kun publishes a schema tailored for ChatGPT. It looks like the following JSON, which defines the meaning and format of each CSV column, along with examples.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Timeline-kun CSV",
  "description": "An array of CSV rows for Timeline-kun",
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "title": { "type": "string", "description": "Event name" },
      "member": { "type": "string", "description": "Person or group" },
      "start": { "type": "string", "pattern": "^\d{1,2}:[0-5]\d:[0-5]\d$", "description": "Start time H:MM:SS" },
      "duration": { "type": "string", "pattern": "^\d{1,2}:[0-5]\d:[0-5]\d$", "default": "0:00:05", "description": "Duration H:MM:SS" },
      "fixed": { "type": "string", "enum": ["start","duration"]},
      "instruction": { "type": "string", "description": "Notes" }
    },
    "required": ["title","member","fixed"],
    "allOf": [
      {
        "if": { "properties": { "fixed": { "const": "start" } } },
        "then": { "required": ["start"] }
      },
      {
        "if": { "properties": { "fixed": { "const": "duration" } } },
        "then": { "required": ["duration"] }
      }
    ]
  },
  "x-notes": {
    "csvHeaderOrder": ["title","member","start","duration","fixed","instruction"],
    "rowOrdering": "Array order is execution order. Do not reorder rows.",
    "instructionTrigger": "The instruction field triggers recording only if it contains the exact substring '(recording)' with matching case",
    "rowRules": [
      "All column values may be duplicated across rows",
      "If duration is not specified, default to 0:00:05"
    ],
    "examples": [
      { "title": "Wake up",    "member": "all member", "start": "0:00:00", "fixed": "start", "instruction": "Good morning! (recording)" },
      { "title": "Stand by",   "member": "group A",    "start": "0:10:00", "fixed": "start" },
      { "title": "Walking",    "member": "group B",    "start": "0:11:00", "duration": "0:05:00", "fixed": "start" },
      { "title": "Stand by",   "member": "sub-001",    "duration": "0:00:20", "fixed": "duration" },
      { "title": "Monitoring", "member": "sub-001/ses-01",    "duration": "0:20:00", "fixed": "duration", "instruction": "Skip when core body temperature reaches 38.5°C" }
    ]
  }
}
```

You can either copy and paste this JSON directly into your prompt, or download the schema file from GitHub and upload it to ChatGPT:  
Right-click this link and choose **Save link as…** to save it locally:  
[timeline_kun_csv.schema.json](https://raw.githubusercontent.com/nishimura5/timeline_kun/refs/heads/main/schemas/timeline_kun_csv.schema.json)

### Example Prompt for ChatGPT

Here is an example of a prompt you might actually send to ChatGPT:

```text
Please generate a CSV file according to this schema.
Three 5-minute sessions, with 1-minute changeover times in between, and a 10-minute discussion at the end.
Please provide the result as a CSV file. The language should be Japanese.
```

### Example ChatGPT Response

An example response from ChatGPT might look like this (visualized here as a table):

![Screenshot of a ChatGPT response](./image/lecture/timeline_kun_chatgpt_3.webp)

```csv
title,member,start,duration,fixed,instruction
Session 1,Group A,0:00:00,0:05:00,start,Start recording (recording)
Changeover 1,All,0:05:00,0:01:00,start,
Session 2,Group B,0:06:00,0:05:00,start,
Changeover 2,All,0:11:00,0:01:00,start,
Session 3,Group C,0:12:00,0:05:00,start,
Discussion,All,0:17:00,0:10:00,start,Wrap-up discussion
```

As long as your instructions are consistent and contain no omissions, even a concise prompt like the one above can produce an accurate CSV file. After adjusting the `title` or `instruction` fields as needed, you can use the result directly as a timer schedule in Timeline-kun.

Using schemas like this is not limited to Timeline-kun. By providing a clear schema to ChatGPT, you can obtain higher-quality structured data for many different applications. Give it a try!
