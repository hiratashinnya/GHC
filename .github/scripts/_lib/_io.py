"""File I/O and JSON output helpers.

責務:
    テキストファイルの読み書き、JSON を stdout へ出力するユーティリティ進攷
    エラー終了トリガーなど、ワークフロースクリプト共通の I/O 機能を提供する。

入力 / 出力:
    各関数の docstring を参照。

副作用:
    write_text / out_err はファイルシステムや stdout に書き込む。

依存モジュール:
    os, sys, json (はいずれも標準ライブラリ)。
"""

import os, sys, json
from typing import NoReturn


def read_text(path):
    """UTF-8 テキストファイルを読み込んで内容を返す。読み取り失敗時は None 。

    責務:
        指定パスのファイルを UTF-8 で開き、内容文字列を返す。
        エラー時は例外を捕捉して None を返す。

    入力:
        path (str | Path): 読み込むファイルパス。

    出力:
        str | None: ファイル内容または読み取り失敗時は None。

    副作用:
        なし。

    依存モジュール:
        なし (組み込み open のみ)。
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def write_text(path, text):
    """テキストをファイルに書き込む。親ディレクトリがなければ作成する。

    責務:
        指定パスに text を UTF-8 / LF 改行で書き込む。
        親ディレクトリが存在しない場合は自動生成する。

    入力:
        path (str | Path): 書き込む先ファイルパス。
        text (str)       : 書き込む文字列。

    出力:
        なし (None)。

    副作用:
        - ファイルを上書きまたは新規作成する。
        - 必要な親ディレクトリを作成する (os.makedirs)。

    依存モジュール:
        - os (標準ライブラリ)。
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def norm(p):
    """パスをフォワードスラッシュ表記に正規化する。

    責務:
        Windows のバックスラッシュをフォワードスラッシュに展開し、
        クロスプラットフォームで一貫したパス文字列を返す。

    入力:
        p (str | Path): 変換対象のパス。

    出力:
        str: バックスラッシュをフォワードスラッシュに置換した文字列。

    副作用:
        なし。

    依存モジュール:
        なし (組み込み str のみ)。
    """
    return str(p).replace("\\", "/")


def out_json(data):
    """JSON 構造体をインデント付きで stdout に印字する。

    責務:
        全スクリプトの出力形式を一元化する。
        非 ASCII 文字もエスケープせずそのまま出力する。

    入力:
        data (dict | list): JSON 直列化可能なデータ。

    出力:
        なし (stdout への副作用のみ)。

    副作用:
        - stdout に JSON を印字する。

    依存モジュール:
        - json (標準ライブラリ)。
    """
    print(json.dumps(data, ensure_ascii=False, indent=2))


def out_err(msg, code=1) -> NoReturn:
    """JSON エラーを stdout に出力し終了する。

    責務:
        { success: false, error: msg } を stdout へ印字し、
        指定の終了コードでプロセスを終了させる。

    入力:
        msg (str)  : エラーメッセージ。
        code (int) : 終了コード (デフォルト: 1)。

    出力:
        なし (出力のみ)。この関数は常に sys.exit するため戈り値はない。

    副作用:
        - stdout に JSON を印字する。
        - sys.exit(code) でプロセスを終了する。

    依存モジュール:
        - out_json (同モジュール内)、sys (標準ライブラリ)。
    """
    out_json({"success": False, "error": msg})
    sys.exit(code)
