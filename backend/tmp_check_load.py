from shared.data_processing import load_data_from_db

print('Loading All Stations...')
try:
    df = load_data_from_db('2025-11-06', '2025-11-06', 'All Stations')
except Exception as e:
    print(f'Error loading All Stations: {e}')
    df = None

print('Type:', type(df))
if df is not None:
    try:
        print('Rows:', len(df))
        print(df.head())
    except Exception as e:
        print(f'Error reading df: {e}')
else:
    print('Skipping data access checks due to load failure')
print('\nLoading Haifa only...')
df2 = load_data_from_db('2025-11-06', '2025-11-06', 'Haifa')
print('Type:', type(df2))
try:
    print('Rows:', len(df2))
    print(df2.head())
except Exception as e:
    print('Error reading df2:', e)
