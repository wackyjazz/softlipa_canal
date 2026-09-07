import hashlib,tempfile,unittest
from pathlib import Path
from upload_r2_oauth import validate_inventory
class InventoryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'x.avif';self.path.write_bytes(b'example');self.key='images/'+hashlib.sha256(b'example').hexdigest()+'.avif';self.objects={self.key:{'path':self.path,'bytes':7}};self.item={'storage_class':'Standard','size':7,'etag':hashlib.md5(b'example').hexdigest()}
 def test_new(self):self.assertEqual(validate_inventory({},self.objects),self.objects)
 def test_existing_verified_skip(self):self.assertEqual(validate_inventory({self.key:self.item},self.objects),{})
 def test_foreign_rejected(self):
  with self.assertRaises(ValueError):validate_inventory({'unrelated.txt':self.item},self.objects)
 def test_mismatch_rejected(self):
  with self.assertRaises(ValueError):validate_inventory({self.key:{**self.item,'etag':'wrong'}},self.objects)
 def test_nonstandard_rejected(self):
  with self.assertRaises(ValueError):validate_inventory({self.key:{**self.item,'storage_class':'InfrequentAccess'}},self.objects)
if __name__=='__main__':unittest.main()
