"""Per-script debug flag and logging.

責務:
    各スクリプト固有のデバッグフラグファイルの存在をチェックし、
    有効時のみ .debug.log ファイルにタイムスタンプ付きログを追記する。
    各スクリプトは個別のデバッグフラグ / ログファイルを持つ。
    フラグ: <script_key>.debug       (存在で有効化)
    ログ : <script_key>.debug.log   (デバッグ有効時に自動生成)
    script_key: "R-1:resolve-cascade-scope" → "resolve_cascade_scope"

入力 / 出力:
    各関数の docstring を参照。

副作用:
    debug_log が .debug.log ファイルへ追記する。

依存モジュール:
    os, json, datetime (はいずれも標準ライブラリ)。
"""

import os, json
from datetime import datetime

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _script_key(script):
    """script 識別子からファイルセーフなキーを抽出する。

    責務:
        "R-1:resolve-cascade-scope" のようなスクリプト識別子から
        ":" 以降の部分を取り出し、"-" を "_" に展開して返す。

    入力:
        script (str): "<プレフィックス>:<名前>" 形式または単笔名前。

    出力:
        str: ファイル名に使えるキー文字列。

    副作用:
        なし。

    依存モジュール:
        なし (組み込み str のみ)。
    """
    s = script.split(":", 1)[-1] if ":" in script else script
    return s.replace("-", "_")


def is_debug(script):
    """指定スクリプトのデバッグモードが有効かどうかを返す。

    責務:
        <script_key>.debug ファイルの存在を確認する。

    入力:
        script (str): スクリプト識別子 ("R-1:resolve-cascade-scope" 形式)。

    出力:
        bool: デバッグフラグファイルが存在する場合 True。

    副作用:
        なし。

    依存モジュール:
        - os (標準ライブラリ)、_script_key (同モジュール)。
    """
    key = _script_key(script)
    return os.path.exists(os.path.join(_SCRIPTS_DIR, f"{key}.debug"))


def debug_log(script, msg, **kw):
    """タイムスタンプ付きデバッグログエントリをスクリプト固有のログファイルに追記する。

    責務:
        <script_key>.debug ファイルが存在する場合のみ、
        [timestamp] [script] msg | {kw} 形式で .debug.log に追記する。

    入力:
        script (str) : スクリプト識別子。
        msg (str)    : ログメッセージ。
        **kw         : ログに付加する任意のキーワード引数。

    出力:
        なし (None)。

    副作用:
        - デバッグモード時に <script_key>.debug.log へ行を追記する。

    依存モジュール:
        - os, json, datetime (標準ライブラリ)、_script_key (同モジュール)。
    """
    key = _script_key(script)
    if not os.path.exists(os.path.join(_SCRIPTS_DIR, f"{key}.debug")):
        return
    log_path = os.path.join(_SCRIPTS_DIR, f"{key}.debug.log")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{script}] {msg}"
    if kw:
        line += " | " + json.dumps(kw, ensure_ascii=False, default=str)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
