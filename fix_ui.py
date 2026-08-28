import os
import re

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace Generic Cyan/Blue with Accent
    content = content.replace("bg-cyan-500", "bg-accent")
    content = content.replace("text-cyan-500", "text-accent")
    content = content.replace("border-cyan-500", "border-accent")
    content = content.replace("text-cyan-400", "text-accent")
    content = content.replace("bg-cyan-900/10", "bg-accent/10")
    content = content.replace("bg-cyan-500/10", "bg-accent/10")
    content = content.replace("border-cyan-500/50", "border-accent")
    
    # 2. Fix the overlap bug in sidebar (change space-y-3 to flex flex-col gap-3)
    content = content.replace("flex-1 overflow-y-auto p-4 space-y-3", "flex-1 overflow-y-auto p-4 flex flex-col gap-3")
    
    # Ensure buttons don't shrink
    content = content.replace("w-full text-left p-4 rounded-2xl", "w-full text-left p-4 rounded-xl shrink-0")
    
    # 3. Chart Gridlines
    # For Recharts components, we should inject stroke="#6B7075" (tertiary text) instead of whatever they have.
    content = re.sub(r'(<CartesianGrid.*?)(/>)', r'\1 stroke="#262B31" \2', content)
    
    # Replace the "Live Stream Active" pulse
    content = content.replace("bg-red-900/20", "bg-surface-raised")
    content = content.replace("border-red-500/30", "border-subtle")
    content = content.replace("bg-red-500 animate-ping", "bg-accent animate-pulse")
    content = content.replace("text-red-400", "text-accent")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

process_file("frontend/src/App.tsx")
process_file("frontend/src/components/HospitalFeedback.tsx")

print("Files post-processed.")
