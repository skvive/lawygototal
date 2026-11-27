"""Queue orchestration tests: no network, synthetic mapping and canonical provenance."""
import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch
import legal_wiki_queue as q
import db_engine
class Result:
    def __init__(self,rows=()):self.rows=list(rows)
    def fetchone(self):return self.rows[0] if self.rows else None
    def fetchall(self):return self.rows
class FakeDB:
    def __init__(self):
        self.rows=[{"id":1,"target":"eflaw","external_id":"100"},{"id":2,"target":"eflaw","external_id":"100"}]
        self.links=[];self.status=[]
    def execute(self,sql,args=()):
        if "FROM legal_wiki.legal_sources" in sql:return Result([{"id":7}])
        if "JOIN legal_wiki.reference_job_mappings" in sql:return Result(self.rows)
        if "status='running'" in sql:return Result([{"id":args[0]}])
        if "FROM legal_wiki.raw_ingestion_payloads" in sql:return Result([{"id":55}])
        if "import_normalized" in sql:return Result([{"imported":1}])
        if "FROM legal_wiki.reference_job_mappings" in sql:return Result([{"target":"eflaw","external_id":"100"}])
        if "INSERT INTO legal_wiki.reference_job_results" in sql:self.links.append(args);return Result()
        if "SET status='success'" in sql:self.status.append((args[0],"success"));return Result()
        if "SET status='failed'" in sql:self.status.append((args[0],"failed"));return Result()
        raise AssertionError(sql)
class QueueTests(unittest.TestCase):
    def test_missing_credential(self):
        with patch.object(db_engine,"USE_POSTGRES",True),patch.dict(os.environ,{"LAW_GO_OC":""}),patch.object(q,"run") as run:
            with self.assertRaises(q.IntakeError):q.batch()
            run.assert_not_called()
    def test_reuse_and_provenance(self):
        db=FakeDB()
        @contextmanager
        def open_db():yield db
        with patch.object(db_engine,"USE_POSTGRES",True),patch.object(db_engine,"open_db",open_db),patch.dict(os.environ,{"LAW_GO_OC":"fixture-only"}),patch.object(q,"run",return_value={"job_id":9,"sha256":"test"}) as run,patch.object(q,"stage") as stage,patch.object(q,"import_checked") as importer:
            results=q.batch()
            run.assert_called_once_with("eflaw","100")
            stage.assert_called_once_with(55)
            importer.assert_called_once_with(db,55)
            self.assertEqual(db.links,[(1,55),(2,55)])
            self.assertEqual(db.status,[(1,"success"),(2,"success")])
            self.assertTrue(all(not x["verified"] for x in results))
