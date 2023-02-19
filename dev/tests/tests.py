from __future__ import absolute_import, print_function

import os
import sys
import unittest
from decimal import Decimal

from tests.models import ImportExample

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.test import TestCase

from django_import.models import ImportJob


class ModuleTest(TestCase):
    def setUp(self):
        self.u1 = User.objects.create(username='u1')
        self.u2 = User.objects.create(username='u2')

    def tearDown(self):
        for j in ImportJob.objects.all():
            try:
                os.remove(j.upload_file.path)
            except Exception:
                pass
        ImportJob.objects.all().delete()

    def test_001_basic_import(self):
        """Test the most general basic import example"""
        options = {
            "reflections": {
                "user": {
                    "parameters": {
                        "lookup_field": "username"
                    },
                    "function": "lookup"
                },
                "kind": {
                    "parameters": {
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        },
                        "column": "type"
                    },
                    "function": "enum"
                }
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test.csv'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test.csv'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvbncv', {'name': 'cvbncv', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2}),
            ('etewrt', {'name': 'etewrt', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1}),
        ]))

    def test_002_twice_import(self):
        """Test whether the identity works"""
        options = {
            "reflections": {
                "user": {
                    "parameters": {
                        "lookup_field": "username"
                    },
                    "function": "lookup"
                },
                "kind": {
                    "parameters": {
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        },
                        "column": "type"
                    },
                    "function": "enum"
                }
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test.csv'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test.csv'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvbncv', {'name': 'cvbncv', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2}),
            ('etewrt', {'name': 'etewrt', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1}),
        ]))

        job.save()
        self.assertEqual(job.logs.all().count(), 2)
        self.assertEqual(ImportExample.objects.all().count(), 2)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvbncv', {'name': 'cvbncv', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2}),
            ('etewrt', {'name': 'etewrt', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1}),
        ]))

    def test_003_double_import(self):
        """Test duplicates while no identity after double import"""
        options = {
            "reflections": {
                "user": {
                    "parameters": {
                        "lookup_field": "username"
                    },
                    "function": "lookup"
                },
                "kind": {
                    "parameters": {
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        },
                        "column": "type"
                    },
                    "function": "enum"
                }
            },
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test.csv'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test.csv'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvbncv', {'name': 'cvbncv', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2}),
            ('etewrt', {'name': 'etewrt', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1}),
        ]))

        job.save()
        self.assertEqual(job.logs.all().count(), 2)
        self.assertEqual(ImportExample.objects.all().count(), 4)
        for example in [dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id']) for e in ImportExample.objects.all()]:
            self.assertIn(example, [
                {'name': 'cvbncv', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2},
                {'name': 'etewrt', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1},
            ])

    def test_004_complex_import(self):
        options = {
            "format": "csv",
            "parameters": {
                "delimiter": ";"
            },
            "mode": "rt",
            "reflections": {
                "name": {
                    "function": "substr",
                    "parameters": {
                        "start": 0,
                        "length": 3
                    }
                },
                "user": {
                    "parameters": {
                        "lookup_field": "username"
                    },
                    "function": "lookup"
                },
                "weight": {
                    "function": "combine",
                    "parameters": {
                        "reflections": [
                            {
                                "function": "replace",
                                "parameters": {
                                    "search": ",",
                                    "replace": "."
                                }
                            },
                            {
                                "function": "clean"
                            }
                        ]
                    }
                },
                "price": {
                    "function": "combine",
                    "parameters": {
                        "reflections": [
                            {
                                "function": "replace",
                                "parameters": {
                                    "search": ",",
                                    "replace": "."
                                }
                            },
                            {
                                "function": "clean"
                            }
                        ]
                    }
                },
                "kind": {
                    "function": "enum",
                    "parameters": {
                        "column": "type",
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        }
                    }
                }
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test-ru.csv'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test-ru.csv'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvb', {'name': 'cvb', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2}),
            ('ete', {'name': 'ete', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1}),
        ]))

    def test_005_xls_import(self):
        """Test the XLS import example"""
        options = {
            "format": "excel",
            "reflections": {
                "user": {
                    "parameters": {
                        "lookup_field": "username"
                    },
                    "function": "lookup"
                },
                "kind": {
                    "parameters": {
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        },
                        "column": "type"
                    },
                    "function": "enum"
                }
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test.xls'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test.xls'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvbncv', {'name': 'cvbncv', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2}),
            ('etewrt', {'name': 'etewrt', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1}),
        ]))

    @unittest.skipIf(sys.version_info < (3, 8), "pandas with python<3 doesn't support xlsx")
    def test_006_xlsx_import(self):
        """Test the XLSX import example"""
        options = {
            "format": "excel",
            "reflections": {
                "user": {
                    "parameters": {
                        "lookup_field": "username"
                    },
                    "function": "lookup"
                },
                "kind": {
                    "parameters": {
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        },
                        "column": "type"
                    },
                    "function": "enum"
                }
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test.xlsx'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test.xlsx'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvbncv', {'name': 'cvbncv', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2}),
            ('etewrt', {'name': 'etewrt', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1}),
        ]))

    @unittest.skipIf(sys.version_info < (3, 8), "pandas with python<3 doesn't support xlsx")
    def test_007_odf_xlsx_import(self):
        """Test the ODF XLSX import example"""
        options = {
            "format": "excel",
            "reflections": {
                "user": {
                    "parameters": {
                        "lookup_field": "username"
                    },
                    "function": "lookup"
                },
                "kind": {
                    "parameters": {
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        },
                        "column": "type"
                    },
                    "function": "enum"
                }
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test-odf.xlsx'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test-odf.xlsx'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvbncv', {'name': 'cvbncv', 'quantity': 112, 'weight': 54.333, 'price': Decimal('34.12'), 'kind': 'wood', 'user': self.u2}),
            ('etewrt', {'name': 'etewrt', 'quantity': 123, 'weight': 10.3, 'price': Decimal('11.11'), 'kind': 'steel', 'user': self.u1}),
        ]))

    def test_008_absent_headers(self):
        """Test for the headers generation"""
        options = {
            "parameters": {
                "header": None,
            },
            "reflections": {
                "name": {
                    "parameters": {
                        "column": "0001"
                    },
                    "function": "direct"
                },
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test.csv'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test.csv'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 3)
        examples = set([e.name for e in ImportExample.objects.all()])
        self.assertEqual(examples, set(['cvbncv', 'etewrt', 'name']))

    def test_009_changed_headers(self):
        """Test for the headers replacing"""
        options = {
            "parameters": {
                "header": None,
            },
            "headers": [
                "name", "nop2", "nop3", "nop4", "nop5", "nop6"
            ],
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test.csv'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test.csv'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 3)
        examples = set([e.name for e in ImportExample.objects.all()])
        self.assertEqual(examples, set(['cvbncv', 'etewrt', 'name']))

    def test_010_avoid_reflection(self):
        """Test `avoid` reflection"""
        options = {
            "format": "csv",
            "parameters": {
                "delimiter": ";"
            },
            "mode": "rt",
            "reflections": {
                "name": {
                    "function": "substr",
                    "parameters": {
                        "start": 0,
                        "length": 3
                    }
                },
                "user": {
                    "parameters": {
                        "lookup_field": "username"
                    },
                    "function": "lookup"
                },
                "weight": "avoid",
                "price": "avoid",
                "kind": {
                    "function": "enum",
                    "parameters": {
                        "column": "type",
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        }
                    }
                }
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test-ru.csv'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test-ru.csv'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvb', {'name': 'cvb', 'quantity': 112, 'weight': None, 'price': None, 'kind': 'wood', 'user': self.u2}),
            ('ete', {'name': 'ete', 'quantity': 123, 'weight': None, 'price': None, 'kind': 'steel', 'user': self.u1}),
        ]))

    def test_011_update_reflection(self):
        """Test `update` reflection with property"""
        options = {
            "format": "csv",
            "parameters": {
                "delimiter": ";"
            },
            "mode": "rt",
            "reflections": {
                "name": {
                    "function": "substr",
                    "parameters": {
                        "start": 0,
                        "length": 3
                    }
                },
                "user": "avoid",
                "user_name": {
                    "function": "update",
                    "parameters": {
                        "column": "user"
                    }
                },
                "weight": "avoid",
                "price": "avoid",
                "kind": {
                    "function": "enum",
                    "parameters": {
                        "column": "type",
                        "mapping": {
                            "S": "steel",
                            "W": "wood",
                            "O": "oil"
                        }
                    }
                }
            },
            "identity": [
                "name"
            ]
        }
        with open(os.path.join(settings.BASE_DIR, 'tests/data/test-ru.csv'), 'rb') as test_file:
            meta = ImportExample._meta
            ct = ContentType.objects.get_by_natural_key(meta.app_label, meta.model_name)
            job = ImportJob.objects.create(upload_file=File(test_file, name='test-ru.csv'), model=ct, options=options)
        self.assertEqual(job.logs.all().count(), 1)
        log = job.logs.all()[0]
        self.assertEqual(log.is_finished, True)
        self.assertEqual(ImportExample.objects.all().count(), 2, log.import_log)
        examples = dict([(e.name, dict([(f.name, getattr(e, f.name)) for f in e._meta.get_fields() if f.name != 'id'])) for e in ImportExample.objects.all()])
        self.assertEqual(examples, dict([
            ('cvb', {'name': 'cvb', 'quantity': 112, 'weight': None, 'price': None, 'kind': 'wood', 'user': self.u2}),
            ('ete', {'name': 'ete', 'quantity': 123, 'weight': None, 'price': None, 'kind': 'steel', 'user': self.u1}),
        ]))
