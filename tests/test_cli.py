# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import subprocess
import sys

from spdx3merge import VERSION


def test_help():
    subprocess.run(["spdx3merge", "--help"], check=True)


def test_module():
    subprocess.run([sys.executable, "-m", "spdx3merge", "--help"], check=True)


def test_version():
    p = subprocess.run(
        ["spdx3merge", "--version"],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.stdout.strip() == VERSION
