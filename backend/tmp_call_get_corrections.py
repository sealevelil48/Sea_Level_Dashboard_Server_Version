from shared.baseline_integration import get_corrections_api
from shared.data_processing import load_data_from_db

print('Loading All Stations...')
all_df = load_data_from_db('2025-11-06', '2025-11-06', 'All Stations')
print('All rows:', len(all_df))
res = get_corrections_api(all_df)
print('Total suggestions (all):', res.get('total_suggestions'))
for s in res.get('suggestions', []):
    print(s)

# Filter for Haifa
haifa = [s for s in res.get('suggestions', []) if s.get('station') == 'Haifa']
print('\nFiltered Haifa suggestions count:', len(haifa))
for s in haifa:
    print(s)
