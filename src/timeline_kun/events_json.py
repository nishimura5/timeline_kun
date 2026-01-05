import os


def make_events_json(tar_path):
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
    if os.path.exists(tar_path):
        return
    with open(tar_path, "w") as f:
        f.write(json_content)
