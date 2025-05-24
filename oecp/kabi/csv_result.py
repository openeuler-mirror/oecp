# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# **********************************************************************************
"""

import os
import csv
import logging
from datetime import datetime, timezone

logger = logging.getLogger("oecp")


class CsvResult:
    def __init__(self):
        self.file_path = "/tmp/oecp/kabi-result-%s.csv" % datetime.now(tz=timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        # Create an empty CSV file if it doesn't exist
        if not os.path.exists(self.file_path):
            with open(self.file_path, mode='w', newline='', encoding='utf-8') as file:
                pass

    def create(self, column_name, data):
        """
        Append a new column to the CSV file.
        @param column_name: Name of the new column
        @param data: List of data to append under the new column
        @return: None
        """
        # Read existing data
        rows = []
        if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
            with open(self.file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)

        # Write headers if the file was empty
        if not rows:
            rows.append([column_name])
            for item in data:
                rows.append([item])
        else:
            rows[0].append(column_name)
            for i in range(1, len(data) + 1):
                rows[i].append(data[i - 1])
        # Write back to the CSV file
        with open(self.file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

        logger.info(f"Column '{column_name}' added to {self.file_path}")
