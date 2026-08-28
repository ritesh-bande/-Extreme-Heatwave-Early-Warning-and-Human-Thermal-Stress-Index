import os
import re

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Structural UI
    content = content.replace("bg-slate-900/80", "card-surface")
    content = content.replace("bg-slate-900/50", "card-surface bg-opacity-50")
    content = content.replace("backdrop-blur-md", "")
    content = content.replace("border-slate-800", "border-subtle")
    content = content.replace("bg-slate-950", "bg-base")
    content = content.replace("shadow-xl", "shadow-sm")
    content = content.replace("shadow-2xl", "shadow-sm")
    content = content.replace("shadow-[0_0_15px_rgba(6,182,212,0.15)]", "shadow-sm border-accent")
    
    # Typography Labels
    content = re.sub(r'text-\[9px\]', 'text-xs', content)
    content = re.sub(r'text-\[10px\]', 'text-xs', content)
    content = re.sub(r'text-\[11px\]', 'text-xs', content)
    content = content.replace("tracking-widest", "tracking-ui")
    content = content.replace("text-slate-400", "text-secondary")
    content = content.replace("text-slate-500", "text-tertiary")
    content = content.replace("text-white", "text-primary")
    
    # Specific removals
    # Remove ambient glow
    content = re.sub(r'<div className="fixed.*?blur-\[120px\].*?</div>', '', content)
    
    # MRI Main gauge glow fix (only allow 10% opacity behind gauge)
    # Actually, let's just strip all `blur-[50px]` and `blur-[80px]`
    content = re.sub(r'blur-\[50px\]', 'blur-[20px] opacity-10', content)
    
    # Add tabular-data to numeric values
    # In App.tsx:
    content = re.sub(r'(<AnimatedNumber.*?>)', r'<span className="tabular-data">\1</span>', content)
    # We will do a generic font-mono fix for numbers manually if needed, but adding tabular-data explicitly to big numbers.
    content = content.replace('text-2xl', 'text-2xl tabular-data')
    content = content.replace('text-3xl', 'text-3xl tabular-data')
    content = content.replace('text-4xl', 'text-3xl tabular-data')
    content = content.replace('text-6xl', 'text-3xl tabular-data')
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

process_file("frontend/src/App.tsx")
process_file("frontend/src/components/CitizenRegistration.tsx")
process_file("frontend/src/components/HospitalFeedback.tsx")
process_file("frontend/src/components/IVRPlayer.tsx")
process_file("frontend/src/components/Map.tsx")

print("Files processed.")
