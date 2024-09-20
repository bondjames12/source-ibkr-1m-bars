#
# Copyright (c) 2024 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from .source import SourceIbkr_1mBars

def run():
    source = SourceIbkr_1mBars()
    launch(source, sys.argv[1:])
