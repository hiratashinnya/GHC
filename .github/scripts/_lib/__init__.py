"""_lib — Shared library package for workflow automation scripts.

Modules:
  _config      : Workflow constants (phases, process files, status emoji)
  _debug       : Per-script debug flag and logging
  _io          : File I/O and JSON output helpers
  _frontmatter : YAML frontmatter parsing and updating
  _paths       : Phase / process path helpers
  _dashboard   : Dashboard matrix and bottleneck builders
"""

from ._config import *
from ._debug import *
from ._io import *
from ._frontmatter import *
from ._paths import *
from ._dashboard import *
