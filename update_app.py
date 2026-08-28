import re

with open("frontend/src/App.tsx", "r") as f:
    text = f.read()

# 1. Add state
state_code = """
  const [selectedCity, setSelectedCity] = useState('Nagpur');
"""
text = text.replace("const [now, setNow] = useState(new Date());", "const [now, setNow] = useState(new Date());\n" + state_code)

# 2. Add filtering
filter_code = """
  const cityWards = processedWards.filter(w => w.name.includes(selectedCity));
  const rawWard = selectedWardId ? cityWards.find(w => w.id === selectedWardId) : cityWards[0];
"""
text = re.sub(r"const rawWard = selectedWardId \? wards\.find.*? wards\[0\];", filter_code, text)

# 3. Use cityWards in sidebar
text = text.replace("{[...processedWards].sort", "{[...cityWards].sort")
text = text.replace("{wards.length} Wards Polled", "{cityWards.length} Wards Polled")

# 4. Pass cityWards and selectedCity to DashboardMap
text = text.replace("wards={processedWards}", "wards={cityWards}\n                    selectedCity={selectedCity}")

# 5. Add Dropdown to UI
dropdown_ui = """
          <select 
            value={selectedCity} 
            onChange={e => { setSelectedCity(e.target.value); setSelectedWardId(null); }}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-[10px] text-white uppercase tracking-widest mt-2 outline-none"
          >
            <option value="Nagpur">Nagpur</option>
            <option value="Chennai">Chennai</option>
            <option value="Ahmedabad">Ahmedabad</option>
          </select>
        </div>
"""
text = text.replace("</p>\n        </div>", "</p>\n" + dropdown_ui)

with open("frontend/src/App.tsx", "w") as f:
    f.write(text)

print("Updated App.tsx")
