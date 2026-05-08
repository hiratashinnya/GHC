#!/usr/bin/env python3
"""_lib — ワークフロー自動化スクリプト共通ライブラリパッケージ

責務:
    SDLC ワークフロースクリプト群で共通利用するユーティリティを提供する。
    各サブモジュールの公開シンボルをフラットにエクスポートする。

入力:
    なし (パッケージインポート時に自動的にサブモジュールがロードされる)。

出力:
    エクスポートされるシンボル:
      _config 由来             : PHASES, PHASE_TO_INDEX, PHASE_LABEL, PROC_FILE,
                                  DD_OVERVIEW, DD_VALIDATION, STATUS_EMOJI, NOT_STARTED,
                                  PROCESS_NAMES
      _debug 由来              : is_debug, debug_log
      _io 由来                 : read_text, write_text, norm, out_json, out_err
      _frontmatter 由来        : parse_fm, scan_fm, update_fm, add_tags, append_changelog
      _paths 由来              : phase_path, proc_filepath, list_dd_components,
                                  list_dd_comp_ids, classify_changed_file
      _md 由来                 : replace_section, replace_table_row
      _dashboard 由来          : build_status_matrix_md, build_component_table_md,
                                  find_bottleneck_lines
      _dashboard_targeted 由来 : build_phase_row, build_component_row,
                                  patch_bottleneck_line

副作用:
    なし (インポート自体は副作用なし)。

依存モジュール:
    - ._config, ._debug, ._io, ._frontmatter, ._paths, ._md,
      ._dashboard, ._dashboard_targeted (内部モジュール)
"""

from ._config import *
from ._debug import *
from ._io import *
from ._frontmatter import *
from ._paths import *
from ._md import *
from ._dashboard import *
from ._dashboard_targeted import *
