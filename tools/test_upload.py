import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from upload_r2 import upload
class Budget:
    def __init__(self):self.calls=0
    def use(self):self.calls+=1
class Client:
    def __init__(self,contents):self.contents=contents;self.puts=[]
    def list_objects_v2(self,**kwargs):return {'Contents':self.contents,'IsTruncated':False}
    def put_object(self,**kwargs):self.puts.append({k:v for k,v in kwargs.items() if k!='Body'})
class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.path=Path(self.temp.name)/'image.jpg';self.path.write_bytes(b'\xff\xd8x');self.key='images/'+'a'*64+'.jpg';self.objects={self.key:{'path':self.path,'bytes':3,'sha256':'a'*64}}
    def tearDown(self):self.temp.cleanup()
    def test_new_and_existing(self):
        for existing,expected in [([],1),([{'Key':self.key,'Size':3}],0)]:
            c=Client(existing);b=Budget();r=upload(c,'bucket',self.objects,b);self.assertEqual(r['uploaded'],expected);self.assertEqual(len(c.puts),expected);self.assertEqual(b.calls,expected+1)
            if expected:self.assertEqual(c.puts[0]['StorageClass'],'STANDARD')
    def test_foreign_bucket_never_writes(self):
        c=Client([{'Key':'other-project/private.txt','Size':10}]);
        with self.assertRaises(ValueError):upload(c,'bucket',self.objects,Budget())
        self.assertEqual(c.puts,[])
    def test_storage_budget_never_writes(self):
        c=Client([{'Key':'images/'+'b'*64+'.jpg','Size':1_000_000_000}]);
        with self.assertRaises(ValueError):upload(c,'bucket',self.objects,Budget())
        self.assertEqual(c.puts,[])
    def test_existing_size_mismatch_never_overwrites(self):
        c=Client([{'Key':self.key,'Size':1}]);
        with self.assertRaises(ValueError):upload(c,'bucket',self.objects,Budget())
        self.assertEqual(c.puts,[])
    def test_failed_upload_is_not_retried(self):
        class Failing(Client):
            def put_object(self,**kwargs):self.puts.append(kwargs['Key']);raise RuntimeError('network')
        c=Failing([])
        with self.assertRaises(RuntimeError):upload(c,'bucket',self.objects,Budget())
        self.assertEqual(len(c.puts),1)
if __name__=='__main__':unittest.main()
