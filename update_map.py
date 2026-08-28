import re

with open("frontend/src/components/Map.tsx", "r") as f:
    text = f.read()

# 1. Update MapProps
props_replacement = """interface MapProps {
  wards: WardData[];
  selectedWardId: number | null;
  onSelectWard: (id: number) => void;
  colorMetric: 'mri_score' | 'wbgt' | 'heat_index' | 'utci';
  coolingSites?: any[];
  selectedCity: string;
}"""
text = re.sub(r"interface MapProps \{.*coolingSites\?: any\[\];\n\}", props_replacement, text, flags=re.DOTALL)

# 2. Update DashboardMap signature
text = text.replace("export function DashboardMap({ wards, selectedWardId, onSelectWard, colorMetric, coolingSites = [] }: MapProps) {", "export function DashboardMap({ wards, selectedWardId, onSelectWard, colorMetric, coolingSites = [], selectedCity }: MapProps) {")

# 3. Add CITIES and fix center
cities_code = """
  const CITIES: Record<string, [number, number]> = {
    'Nagpur': [21.1458, 79.0882],
    'Chennai': [13.0827, 80.2707],
    'Ahmedabad': [23.0225, 72.5714]
  };
  const currentCenter = CITIES[selectedCity] || CITIES['Nagpur'];
"""
text = re.sub(r"  const getWardColor = \(wardId: number\) => \{", cities_code + "\n  const getWardColor = (wardId: number) => {", text)

text = text.replace("center={NAGPUR_CENTER}", "center={currentCenter}")
text = text.replace("map.flyTo(NAGPUR_CENTER", "map.flyTo(currentCenter")

# 4. Pass selectedCity to MapController
text = text.replace("<MapController selectedWardId={selectedWardId} wards={wards} />", "<MapController selectedWardId={selectedWardId} wards={wards} selectedCity={selectedCity} />")

mapcontroller_replacement = """function MapController({ selectedWardId, wards, selectedCity }: { selectedWardId: number | null, wards: WardData[], selectedCity: string }) {
  const map = useMap();
  
  useEffect(() => {
    const CITIES: Record<string, [number, number]> = {
      'Nagpur': [21.1458, 79.0882],
      'Chennai': [13.0827, 80.2707],
      'Ahmedabad': [23.0225, 72.5714]
    };
    const currentCenter = CITIES[selectedCity] || CITIES['Nagpur'];

    if (selectedWardId) {
      const ward = wards.find(w => w.id === selectedWardId);
      if (ward) {
        map.flyTo([ward.centroid_lat, ward.centroid_lon], 13, {
          duration: 1.5,
          easeLinearity: 0.25
        });
      }
    } else {
      map.flyTo(currentCenter, 11, {
        duration: 1.5,
        easeLinearity: 0.25
      });
    }
  }, [selectedWardId, wards, map, selectedCity]);"""
text = re.sub(r"function MapController.*?\}, \[selectedWardId, wards, map\]\);", mapcontroller_replacement, text, flags=re.DOTALL)

with open("frontend/src/components/Map.tsx", "w") as f:
    f.write(text)
print("Updated Map.tsx")
