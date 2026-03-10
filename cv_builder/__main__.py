"""Allow the package to be run as ``python -m cv_builder``."""

import sys

from cv_builder.main import main

sys.exit(main())
