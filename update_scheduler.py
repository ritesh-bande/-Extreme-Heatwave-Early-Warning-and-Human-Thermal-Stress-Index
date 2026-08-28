import json
import re

with open("backend_sample_wards.json", "r") as f:
    wards = json.load(f)

with open("backend/app/tasks/scheduler.py", "r") as f:
    content = f.read()

new_assignment = "SAMPLE_WARDS = " + json.dumps(wards, indent=4) + "\n"
pattern = r"SAMPLE_WARDS = \[.*?\]\n"
content = re.sub(pattern, new_assignment, content, flags=re.DOTALL)

with open("backend/app/tasks/scheduler.py", "w") as f:
    f.write(content)

print("Updated scheduler.py")
