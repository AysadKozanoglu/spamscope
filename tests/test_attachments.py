#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://twitter.com/fedelemantuano)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import unittest
from collections import deque
from mailparser import MailParser

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
mail = os.path.join(base_path, 'samples', 'mail_malformed_1')
sys.path.append(root)
from src.modules.attachments import MailAttachments
from src.modules.attachments.attachments import HashError


class TestAttachments(unittest.TestCase):

    def setUp(self):
        # Init
        p = MailParser()
        p.parse_from_file(mail)
        self.attachments = p.attachments_list

    def test_withhashes(self):
        t = MailAttachments.withhashes(self.attachments)
        self.assertIsInstance(t, MailAttachments)
        self.assertEqual(len(t), 1)

        for i in t:
            self.assertIn("md5", i)
            self.assertIn("sha1", i)
            self.assertIn("sha256", i)
            self.assertIn("sha512", i)
            self.assertIn("ssdeep", i)
            self.assertIn("filename", i)
            self.assertIn("payload", i)
            self.assertIn("mail_content_type", i)
            self.assertIn("content_transfer_encoding", i)

    def test_pophash(self):
        t = MailAttachments.withhashes(self.attachments)
        md5 = "1e38e543279912d98cbfdc7b275a415e"

        self.assertEqual(len(t), 1)

        with self.assertRaises(HashError):
            t.pophash("fake")

        t.pophash(md5)
        self.assertEqual(len(t), 0)

    def test_filter(self):
        t = MailAttachments.withhashes(self.attachments)
        check_list = deque(maxlen=10)
        md5 = "1e38e543279912d98cbfdc7b275a415e"

        check_list.append(md5)
        self.assertIn("payload", t[0])
        self.assertNotIn("is_filtered", t[0])

        r = t.filter(check_list, hash_type="md5")
        self.assertNotIn("payload", t[0])
        self.assertIn("is_filtered", t[0])
        self.assertEqual(True, t[0]["is_filtered"])
        self.assertIn(md5, r)

        check_list.extend(r)
        self.assertEqual(2, len(check_list))

        # It should not fail
        t.run()

        t = MailAttachments.withhashes(self.attachments)
        check_list = deque(maxlen=10)
        md5 = "1e38e543279912d98cbfdc7b275a415f"
        check_list.append(md5)

        r = t.filter(check_list, hash_type="md5")
        self.assertIn("payload", t[0])
        self.assertIn("is_filtered", t[0])
        self.assertEqual(False, t[0]["is_filtered"])
        self.assertNotIn(md5, r)

    def test_run(self):
        t = MailAttachments.withhashes(self.attachments)
        t()

        for i in t:
            self.assertIn("extension", i)
            self.assertIn("size", i)
            self.assertIn("Content-Type", i)
            self.assertIn("is_archive", i)
            self.assertIn("files", i)

            self.assertEqual(i["extension"], ".zip")
            self.assertTrue(i["is_archive"])
            self.assertEqual(len(i["files"]), 1)

            for j in i["files"]:
                self.assertIn("filename", j)
                self.assertIn("extension", j)
                self.assertIn("size", j)
                self.assertIn("Content-Type", j)
                self.assertIn("payload", j)
                self.assertIn("md5", j)

    def test_reload(self):
        dummy = {"key1": "value1", "key2": "value2"}
        t = MailAttachments.withhashes(self.attachments)
        t.reload(**dummy)
        self.assertEqual(t.key1, "value1")
        self.assertEqual(t.key2, "value2")
        self.assertEqual(len(t), 1)

        t()
        t.removeall()
        self.assertEqual(len(t), 0)


if __name__ == '__main__':
    unittest.main()
