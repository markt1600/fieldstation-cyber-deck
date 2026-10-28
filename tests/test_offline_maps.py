from pathlib import Path
import sys,tempfile,json,unittest,sqlite3
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import offline_maps as m
class MapsTests(unittest.TestCase):
 def test_address_queries(self):
  old=m.ROOT
  try:
   with tempfile.TemporaryDirectory() as d:
    m.ROOT=Path(d)
    with sqlite3.connect(m.ROOT/'addresses.sqlite3') as c:
     c.execute('CREATE TABLE places(id INTEGER PRIMARY KEY,name,context,kind,number,lon,lat)')
     c.execute('CREATE VIRTUAL TABLE search USING fts5(text)')
     c.execute("INSERT INTO places VALUES(1,'61 Example Road','123456','address','61',103.8,1.3)")
     c.execute("INSERT INTO search(rowid,text) VALUES(1,'61 example road 123456')")
    c.close()
    self.assertEqual(m.address_search('61 Example Rd Singapore',103.8,1.3)[0]['name'],'61 Example Road')
    self.assertEqual(m.address_search('123456')[0]['kind'],'address')
    self.assertEqual(m.address_search('999 Missing Street'),[])
    self.assertEqual(m.address_search('" OR *'),[])
  finally:m.ROOT=old
 def test_files_and_partial_downloads(self):
  old=m.ROOT
  with tempfile.TemporaryDirectory() as d:
   m.ROOT=Path(d);(m.ROOT/'assets').mkdir();(m.ROOT/'assets/map.js').write_text('ok');(m.ROOT/'world.pmtiles').write_bytes(b'PMTiles');(m.ROOT/'secret.key').write_text('secret');(m.ROOT/'manifest.json').write_text(json.dumps({'regions':[{'id':'world'},{'id':'missing'}]}))
   self.assertEqual(len(m.manifest()['regions']),1)
   self.assertIsNotNone(m.file_path('/map-data/world.pmtiles'))
   self.assertIsNotNone(m.file_path('/map-data/assets/map.js'))
   for p in ['../secret.key','secret.key','assets/%2e%2e/secret.key','missing.pmtiles']:
    self.assertIsNone(m.file_path('/map-data/'+p))
  m.ROOT=old
 def test_reject_unsupported_routes(self):
  for params in [{'points':['nan,1|103,1']},{'points':['0,0|1,1']},{'points':['103,1|104,1'],'profile':['../../x']}]:
   with self.assertRaises(ValueError):m.route(params)
if __name__=='__main__': unittest.main()
