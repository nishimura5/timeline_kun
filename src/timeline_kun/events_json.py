
def make_events_json(file_prefix):
    json_content = """
{
  "trial_type": {
    "Description": "Type of event (includes user-defined tasks and control events)",
    "HED": {
      "task_skip": "Experiment-control, Action/Skip",
      "video_record_start": "Experiment-control, Video/Start",
      "session_end": "Experiment-end"
    }
  },
  "onset": {
    "Description": "Event onset time in seconds"
  },
  "duration": {
    "Description": "Event duration in seconds"
  }
}
"""
    json_file_path = f"{file_prefix}_events.json"
    with open(json_file_path, "w") as f:
        f.write(json_content)
