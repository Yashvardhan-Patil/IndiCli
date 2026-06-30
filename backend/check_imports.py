import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.dataset_manager import DatasetManager

dm = DatasetManager('../../processed/csv/master_climate_dataset.csv')
dm.load()
meta = dm.get_meta()
print("Dataset loaded OK")
print("Rows:", meta['total_rows'])
print("Dates:", meta['date_start'], "to", meta['date_end'])
print("Lat:", meta['lat_min'], "to", meta['lat_max'])

qr = dm.get_quality_report()
print("Quality - completeness:", qr['completeness_pct'], "%")
print("ALL BACKEND IMPORTS OK")
