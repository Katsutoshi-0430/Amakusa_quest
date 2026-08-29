# -*- coding: utf-8 -*-
"""
天草つながりクエスト
アンケート StreamlitAPIException 修正版（新規エントリーファイル）

重要:
- 元の Amakusa_quest_survey_note_save_verified.py は一切書き換えません。
- このファイルを同じフォルダに追加し、Streamlit の Main file path を
  このファイルへ変更して使います。
- Supabase のテーブル・既存回答・クエスト進捗データは変更しません。

原因:
元コードでは、画面上部からアンケートを開いた際に render_survey() が実行され、
さらに下部の「アンケート」タブでも render_survey() が実行されます。
render_survey() 内部は st.form("survey") を使っているため、
同一 Streamlit run 内で同じフォームキーが2回生成され、
StreamlitAPIException が発生します。

修正:
上部アンケートが開いている間は、下部アンケートタブ側では
render_survey() を実行しません。
"""

from pathlib import Path

SOURCE_NAME = "Amakusa_quest_survey_note_save_verified.py"

BASE = Path(__file__).resolve().parent
SOURCE = BASE / SOURCE_NAME

if not SOURCE.exists():
    raise FileNotFoundError(
        f"{SOURCE_NAME} が見つかりません。"
        "このFIXEDファイルを元ファイルと同じGitHubフォルダに置いてください。"
    )

source_code = SOURCE.read_text(encoding="utf-8")

# 元コードで問題になっている箇所だけを実行時に差し替える。
# 元ファイルそのものは保存・上書きしない。
old = (
    'with summary_tab: render_summary()\n'
    'with survey_tab: render_survey()\n\n'
    'st.divider(); st.caption("天草つながりクエスト｜テストマーケティング版")'
)

new = (
    'with summary_tab: render_summary()\n'
    'with survey_tab:\n'
    '    # 上部アンケート表示中は、同じ survey フォームを二重生成しない\n'
    '    if st.session_state.get("open_survey_from_top", False):\n'
    '        st.info("現在、画面上部でアンケートを開いています。")\n'
    '    else:\n'
    '        render_survey()\n\n'
    'st.divider(); st.caption("天草つながりクエスト｜テストマーケティング版")'
)

matches = source_code.count(old)
if matches != 1:
    raise RuntimeError(
        "アンケート修正対象を安全に特定できませんでした。"
        f" 想定1箇所 / 検出{matches}箇所。"
        " 元ファイルが変更されていないか確認してください。"
    )

fixed_code = source_code.replace(old, new, 1)

# __file__ を元コードと同じ場所として扱わせるため、
# compile時のfilenameには元ファイルのパスを指定する。
# これにより画像フォルダ等の相対パス仕様も維持する。
compiled = compile(fixed_code, str(SOURCE), "exec")

# 元アプリを修正版コードとして実行。
exec(compiled, globals(), globals())
