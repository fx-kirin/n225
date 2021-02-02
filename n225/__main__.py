#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 fx-kirin <fx.kirin@gmail.com>
#
# Distributed under terms of the MIT license.

"""

"""

import os
import logging
import kanilog
from pathlib import Path

from . import download_kouseimeigara_pdfs, download_josuu_pdfs, parse_pdfs


def main():
    download_kouseimeigara_pdfs()
    download_josuu_pdfs()
    parse_pdfs()


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    kanilog.setup_logger(
        logfile="/tmp/%s.log" % (Path(__file__).name), level=logging.INFO
    )
    main()
