"""Offline evidence review fault tests, never presented as simulator execution."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from review_research_v3 import checked_path, relocate_and_verify, sha256_file, validate_identity


class ReviewIdentityTests(unittest.TestCase):
    def header(self):
        return {'schema_version': 3, 'split': 'validation', 'source_commit': 'a' * 40,
                'design_sha256': 'design', 'runtime_sha256': 'runtime',
                'status': 'complete', 'complete_split': True,
                'working_tree_dirty': False, 'integrity_passed': True,
                'files': {'module': 'hash'}, 'cases': ['case'], 'gate': {'met': False}}

    def check(self, report):
        return validate_identity(report, 'validation', 'a'*40, 'design', 'runtime', {'module':'hash'}, ['case'])

    def test_complete_negative_is_a_reviewable_research_result(self):
        self.check(self.header())

    def test_wrong_source_lock_or_split_is_rejected(self):
        for key in ('source_commit', 'runtime_sha256', 'design_sha256', 'split'):
            value = self.header();value[key] = 'wrong'
            with self.subTest(key=key), self.assertRaises(ValueError):self.check(value)

    def test_missing_dirty_or_partial_evidence_never_qualifies(self):
        for key,new in (('status','incomplete'),('complete_split',False),('working_tree_dirty',True),('integrity_passed',False)):
            value=self.header();value[key]=new
            with self.subTest(key=key), self.assertRaises(ValueError):self.check(value)
        value=self.header();del value['integrity_passed']
        with self.assertRaises(ValueError):self.check(value)

    def test_bool_integer_confusion_and_membership_drift_are_rejected(self):
        for key,new in (('complete_split',1),('working_tree_dirty',0),('cases',['another']),('files',{})):
            value=self.header();value[key]=new
            with self.subTest(key=key), self.assertRaises(ValueError):self.check(value)

    def test_heldout_without_execution_runtime_lock_is_rejected(self):
        value=self.header();value['runtime_sha256']=None
        with self.assertRaisesRegex(ValueError,'runtime lock'):
            validate_identity(value,'validation','a'*40,'design',None,{'module':'hash'},['case'])

    def test_train_and_short_source_cannot_be_reviewed(self):
        with self.assertRaises(ValueError):validate_identity(self.header(),'train','a'*40,'d','r',{},[])
        with self.assertRaises(ValueError):validate_identity(self.header(),'validation','abc','d','r',{},[])


class ReviewPathTests(unittest.TestCase):
    def test_path_traversal_absolute_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('../secret','/tmp/secret','nested/file','..'):
                with self.subTest(name=name), self.assertRaises(ValueError):checked_path(root,name)
            (root/'link').symlink_to(root/'target')
            with self.assertRaises(ValueError):checked_path(root,'link')

    def fixture(self, root):
        folder=root/'case-r0-a0';folder.mkdir()
        (folder/'console.log').write_text('could not connect to display')
        # A committed infrastructure attempt is enough to test relocation/hashes.
        attempt={'case_id':'case','repeat':0,'attempt':0,'output':'/original/ci/case-r0-a0',
                 'watchdog':False,'returncode':1,'classification':'infrastructure','result':None,
                 'files_sha256':{'console.log':sha256_file(folder/'console.log')}}
        return {'attempts':[attempt]},[{'id':'case'}],folder

    def test_relocation_never_changes_original_raw_report(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);report,cases,folder=self.fixture(root);before=deepcopy(report)
            relocated=relocate_and_verify(report,root,cases)
            self.assertEqual(report,before)
            self.assertEqual(relocated['attempts'][0]['output'],str(folder.resolve()))

    def test_corrupted_raw_file_is_rejected_before_replay(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);report,cases,folder=self.fixture(root)
            (folder/'console.log').write_text('modified')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):relocate_and_verify(report,root,cases)

    def test_unknown_case_repeat_retry_and_directory_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);report,cases,folder=self.fixture(root)
            for key,new in (('case_id','other'),('repeat',2),('attempt',2),('output','/wrong-dir'),('watchdog','false')):
                value=deepcopy(report);value['attempts'][0][key]=new
                with self.subTest(key=key), self.assertRaises(ValueError):relocate_and_verify(value,root,cases)

    def test_false_failure_classification_and_pair_header_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);report,cases,folder=self.fixture(root)
            value=deepcopy(report);value['attempts'][0]['classification']='valid'
            with self.assertRaisesRegex(ValueError,'classification mismatch'):relocate_and_verify(value,root,cases)
            (folder/'result.json').write_text(json.dumps({'status':'incomplete'}))
            with self.assertRaisesRegex(ValueError,'Pair result differs'):relocate_and_verify(report,root,cases)


if __name__ == '__main__':unittest.main()
