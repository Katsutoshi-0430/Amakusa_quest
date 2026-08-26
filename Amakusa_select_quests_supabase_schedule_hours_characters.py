# -*- coding: utf-8 -*-
"""
天草つながりクエスト
アンケート「旅行消費・掲載店送客効果」追加用アップデーター

使い方:
1. このファイルを、現在のアプリ本体
   Amakusa_select_quests_supabase_schedule_hours_characters_story_admin_photos.py
   と同じフォルダに置く
2. Anaconda Prompt / PowerShell でそのフォルダへ移動
3. python add_spending_survey_to_amakusa.py
4. 同じフォルダに
   Amakusa_select_quests_supabase_schedule_hours_characters_story_admin_photos_spending_survey.py
   が生成される
"""

from pathlib import Path
import re
import sys

SOURCE_NAME = "Amakusa_select_quests_supabase_schedule_hours_characters_story_admin_photos.py"
OUTPUT_NAME = "Amakusa_select_quests_supabase_schedule_hours_characters_story_admin_photos_spending_survey.py"

NEW_RENDER_SURVEY = r"""def render_survey() -> None:
    st.subheader("📝 テストマーケティング アンケート")
    st.write(
        "ご協力ありがとうございます。回答はアプリ改善、天草への再訪効果、"
        "クエスト掲載店・施設への送客効果の検証に使用します。"
    )
    if st.session_state.get("survey_submitted"):
        st.success("✅ アンケートは回答済みです。内容を変更して再送信することもできます。")

    ans = dict(st.session_state.get("survey_answers", {}) or {})
    age_value = st.session_state.get("profile_age") or ans.get("age", "")

    gender_options = ["選択してください", "男性", "女性", "回答しない・その他"]
    region_options = [
        "選択してください",
        "天草",
        "熊本県内（天草外）",
        "九州地方（熊本県外）",
        "関東地方",
        "関西地方",
        "その他",
    ]
    companion_options = [
        "一人旅",
        "家族（配偶者・パートナー）",
        "家族（子ども連れ）",
        "家族（親・その他親族）",
        "友人・知人",
        "恋人",
        "旅行ではない（天草在住・日常利用）",
        "その他",
    ]
    game_options = ["選択してください", "よくする", "たまにする", "あまりしない", "全くしない"]
    visit_options = [
        "選択してください",
        "初めて",
        "2回目",
        "3〜5回目",
        "6回目以上（リピーター）",
        "天草在住",
    ]
    change_options = [
        "選択してください",
        "1：大きく下がった",
        "2：やや下がった",
        "3：変わらない",
        "4：やや高まった",
        "5：大きく高まった",
        "該当しない（天草在住）",
    ]
    intent_options = [
        "選択してください",
        "1：全くそう思わない",
        "2：あまりそう思わない",
        "3：どちらともいえない",
        "4：そう思う",
        "5：とてもそう思う",
        "該当しない（天草在住）",
    ]
    satisfaction_options = [
        "選択してください",
        "1：とても不満",
        "2：やや不満",
        "3：どちらともいえない",
        "4：満足",
        "5：とても満足",
    ]

    spend_optional_options = [
        "回答しない",
        "0円",
        "1〜999円",
        "1,000〜2,999円",
        "3,000〜4,999円",
        "5,000〜9,999円",
        "10,000〜19,999円",
        "20,000〜29,999円",
        "30,000〜49,999円",
        "50,000円以上",
        "わからない",
    ]
    quest_spend_options = [
        "選択してください",
        "0円",
        "1〜999円",
        "1,000〜2,999円",
        "3,000〜4,999円",
        "5,000〜9,999円",
        "10,000〜19,999円",
        "20,000〜29,999円",
        "30,000円以上",
        "わからない",
    ]
    app_trigger_options = [
        "選択してください",
        "はい",
        "いいえ",
        "わからない・覚えていない",
        "該当しない（天草在住・日常利用など）",
    ]
    counterfactual_options = [
        "選択してください",
        "利用していたと思う",
        "おそらく利用していた",
        "おそらく利用していなかった",
        "利用していなかったと思う",
        "わからない",
    ]

    place_options = []
    for _q in list(QUESTS) + list(STORY_QUESTS):
        _name = str(_q.get("linked_name", "")).strip()
        if _name and _name not in place_options:
            place_options.append(_name)

    with st.form("test_marketing_survey"):
        st.markdown("### ■ あなた自身について（基本属性）")
        age = st.selectbox(
            "Q1. 年代を教えてください。",
            AGE_OPTIONS[1:],
            index=max(0, _option_index(AGE_OPTIONS[1:], age_value, 0)),
        )
        gender = st.selectbox(
            "Q2. 性別を教えてください。（任意）",
            gender_options,
            index=_option_index(gender_options, ans.get("gender", "")),
        )
        region = st.selectbox(
            "Q3. お住まいの地域を教えてください。（必須）",
            region_options,
            index=_option_index(region_options, ans.get("region", "")),
        )
        region_other = st.text_input(
            "Q3-2. 「その他」の場合、地域を入力してください。",
            value=ans.get("region_other", ""),
        )
        companions = st.multiselect(
            "Q4. 今回の旅の同行者を教えてください。（任意・複数選択可）",
            companion_options,
            default=ans.get("companions", []),
        )
        companion_other = st.text_input(
            "Q4-2. 「その他」の場合、同行者を入力してください。",
            value=ans.get("companion_other", ""),
        )
        gaming = st.selectbox(
            "Q5. 普段、ゲーム（スマホアプリ、据え置き機など）はしますか？（任意）",
            game_options,
            index=_option_index(game_options, ans.get("gaming", "")),
        )
        visits = st.selectbox(
            "Q6. 天草への訪問は今回で何回目ですか？（必須）",
            visit_options,
            index=_option_index(visit_options, ans.get("visits", "")),
        )

        st.markdown("### ■ 今回の旅での消費・クエスト掲載店の利用について")
        st.caption(
            "掲載店・施設への送客効果と、今後の掲載料金を検討するために使用します。"
            "金額はおおよその『1人あたり』で構いません。"
        )

        st.markdown("**Q7. 今回の天草での消費額を教えてください。（任意）**")
        st.caption("覚えている範囲で構いません。回答しにくい項目は「回答しない」を選べます。")

        spend_col1, spend_col2 = st.columns(2)
        with spend_col1:
            trip_spend_lodging = st.selectbox(
                "Q7-1. 宿泊費（1人あたり）",
                spend_optional_options,
                index=_option_index(
                    spend_optional_options,
                    ans.get("trip_spend_lodging", "回答しない"),
                ),
            )
            trip_spend_food = st.selectbox(
                "Q7-2. 飲食費（1人あたり）",
                spend_optional_options,
                index=_option_index(
                    spend_optional_options,
                    ans.get("trip_spend_food", "回答しない"),
                ),
            )
        with spend_col2:
            trip_spend_souvenir = st.selectbox(
                "Q7-3. お土産・買い物代（1人あたり）",
                spend_optional_options,
                index=_option_index(
                    spend_optional_options,
                    ans.get("trip_spend_souvenir", "回答しない"),
                ),
            )
            trip_spend_experience = st.selectbox(
                "Q7-4. 体験・施設入場料（1人あたり）",
                spend_optional_options,
                index=_option_index(
                    spend_optional_options,
                    ans.get("trip_spend_experience", "回答しない"),
                ),
            )

        quest_listing_spend = st.selectbox(
            "Q8. 今回、クエスト掲載店・有料施設で使った金額の合計を教えてください。（必須・1人あたり）",
            quest_spend_options,
            index=_option_index(
                quest_spend_options,
                ans.get("quest_listing_spend", ""),
            ),
            help="飲食、買い物、入場料、体験料など、クエスト掲載先で支払った金額の合計です。",
        )

        app_triggered_visit = st.selectbox(
            "Q9. このアプリ・クエストを見たことがきっかけで、実際に行ったスポットはありましたか？（必須）",
            app_trigger_options,
            index=_option_index(
                app_trigger_options,
                ans.get("app_triggered_visit", ""),
            ),
        )

        saved_triggered_places = ans.get("app_triggered_places", []) or []
        app_triggered_places = st.multiselect(
            "Q9-2. 「はい」の場合、アプリがきっかけで訪れたスポットを選んでください。（必須・複数選択可）",
            place_options,
            default=[p for p in saved_triggered_places if p in place_options],
        )

        counterfactual_visit = st.selectbox(
            "Q10. Q9で「はい」と答えた方へ：アプリがなかった場合、そのスポットを訪問・利用していたと思いますか？（必須）",
            counterfactual_options,
            index=_option_index(
                counterfactual_options,
                ans.get("counterfactual_visit", ""),
            ),
        )
        st.caption(
            "※ Q8〜Q10は、アプリによって新しく生まれた可能性のある消費を推定するための重要項目です。"
        )

        st.markdown("### ■ アプリの機能について")
        st.caption(
            "各機能について、実際に使ったうえでの満足度を教えてください。"
            "使っていない機能は「使っていない」を選択してください。"
        )
        feature_answers = {}
        saved_features = ans.get("feature_ratings", {}) or {}
        feature_start_q = 11
        for i, feature in enumerate(FEATURE_SURVEY_ITEMS, start=feature_start_q):
            feature_answers[feature] = st.radio(
                f"Q{i}. {feature}",
                FEATURE_RATING_OPTIONS,
                index=_option_index(
                    FEATURE_RATING_OPTIONS,
                    saved_features.get(feature, "使っていない"),
                ),
                horizontal=True,
                key=f"survey_feature_{feature}",
            )

        qn = feature_start_q + len(FEATURE_SURVEY_ITEMS)

        st.markdown("### ■ アプリを通しての再訪意欲")
        revisit_change = st.selectbox(
            f"Q{qn}. このアプリを使ったことで、天草に『また来たい』という気持ちは高まりましたか？",
            change_options,
            index=_option_index(change_options, ans.get("revisit_change", "")),
        )
        revisit_intent = st.selectbox(
            f"Q{qn+1}. 今後1年以内に、天草を再び訪れたいと思いますか？",
            intent_options,
            index=_option_index(intent_options, ans.get("revisit_intent", "")),
        )
        reuse_intent = st.selectbox(
            f"Q{qn+2}. 次回天草を訪れる際にも、このアプリを使いたいと思いますか？",
            intent_options,
            index=_option_index(intent_options, ans.get("reuse_intent", "")),
        )

        st.markdown("### ■ アプリ全体について")
        satisfaction = st.selectbox(
            f"Q{qn+3}. アプリ全体の満足度を教えてください。",
            satisfaction_options,
            index=_option_index(
                satisfaction_options,
                ans.get("overall_satisfaction", ""),
            ),
        )

        good_points = st.text_area(
            f"Q{qn+4}. 良かった点を教えてください。（任意）",
            value=ans.get("good_points", ""),
            height=100,
        )
        improvement_points = st.text_area(
            f"Q{qn+5}. 改善してほしい点を教えてください。（任意）",
            value=ans.get("improvement_points", ""),
            height=100,
        )
        requested_features = st.text_area(
            f"Q{qn+6}. 追加してほしい機能があれば教えてください。（任意）",
            value=ans.get("requested_features", ""),
            height=100,
        )

        submitted = st.form_submit_button(
            "📨 アンケートを送信する",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        required_missing = []

        if region == "選択してください":
            required_missing.append("居住地域")
        if "一人旅" in companions and len(companions) > 1:
            required_missing.append("同行者（一人旅と他の選択肢は同時に選べません）")
        if visits == "選択してください":
            required_missing.append("天草訪問回数")

        if quest_listing_spend == "選択してください":
            required_missing.append("クエスト掲載店・施設での消費額")
        if app_triggered_visit == "選択してください":
            required_missing.append("アプリをきっかけにした来店・来訪の有無")

        if app_triggered_visit == "はい":
            if not app_triggered_places:
                required_missing.append("アプリがきっかけで訪れた店・施設")
            if counterfactual_visit == "選択してください":
                required_missing.append("アプリがなかった場合の利用意向")

        if revisit_change == "選択してください":
            required_missing.append("再訪意欲の変化")
        if revisit_intent == "選択してください":
            required_missing.append("1年以内の再訪意向")
        if reuse_intent == "選択してください":
            required_missing.append("アプリ再利用意向")
        if satisfaction == "選択してください":
            required_missing.append("全体満足度")

        if region == "その他" and not region_other.strip():
            required_missing.append("その他の居住地域")

        if required_missing:
            st.error("未回答の必須項目があります：" + "、".join(required_missing))
        else:
            payload = {
                "age": age,
                "gender": gender,
                "region": region,
                "region_other": region_other.strip(),
                "companions": companions,
                "companion_other": companion_other.strip(),
                "gaming": gaming,
                "visits": visits,

                "trip_spend_lodging": trip_spend_lodging,
                "trip_spend_food": trip_spend_food,
                "trip_spend_souvenir": trip_spend_souvenir,
                "trip_spend_experience": trip_spend_experience,
                "quest_listing_spend": quest_listing_spend,
                "app_triggered_visit": app_triggered_visit,
                "app_triggered_places": app_triggered_places,
                "counterfactual_visit": (
                    counterfactual_visit
                    if app_triggered_visit == "はい"
                    else "該当なし"
                ),

                "feature_ratings": feature_answers,
                "revisit_change": revisit_change,
                "revisit_intent": revisit_intent,
                "reuse_intent": reuse_intent,
                "overall_satisfaction": satisfaction,
                "good_points": good_points.strip(),
                "improvement_points": improvement_points.strip(),
                "requested_features": requested_features.strip(),
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            }

            st.session_state.profile_age = age
            st.session_state.survey_answers = payload
            st.session_state.survey_submitted = True
            st.session_state.survey_submitted_at = payload["submitted_at"]

            survey_saved = False
            survey_error = None

            if supabase_is_configured():
                try:
                    survey_saved = save_survey_to_quest_progress(payload)
                except Exception as e:
                    survey_error = e

            try:
                save_user_data()
            except Exception as e:
                if survey_error is None:
                    survey_error = e

            if survey_saved:
                st.success(
                    "ご回答ありがとうございました！"
                    "アンケートを quest_progress に保存しました。"
                )
                st.caption(
                    "Supabaseでは quest_id が「__survey__」の行に回答内容が保存されています。"
                )
            elif supabase_is_configured() and survey_error is not None:
                st.error(
                    "アンケートをSupabaseに保存できませんでした。"
                    f"エラー: {survey_error}"
                )
            else:
                st.warning(
                    "アンケートはこの端末に保存しましたが、"
                    "Supabaseへの接続を確認できませんでした。"
                )
"""

def main():
    here = Path(__file__).resolve().parent
    src = here / SOURCE_NAME
    out = here / OUTPUT_NAME

    if not src.exists():
        print(f"エラー: {SOURCE_NAME} が同じフォルダに見つかりません。")
        print("このアップデーターを現在のアプリ本体と同じフォルダに置いてから実行してください。")
        sys.exit(1)

    text = src.read_text(encoding="utf-8")

    pattern = re.compile(
        r"(?ms)^def render_survey\(\) -> None:\n.*?(?=^# =====================================================================\n# ★ UI構築)"
    )

    match = pattern.search(text)
    if not match:
        print("エラー: render_survey() の範囲を特定できませんでした。")
        print("アプリ本体のバージョンが想定と異なる可能性があります。")
        sys.exit(1)

    updated = text[:match.start()] + NEW_RENDER_SURVEY.rstrip() + "\n\n\n" + text[match.end():]
    out.write_text(updated, encoding="utf-8")

    print("更新完了")
    print(f"元ファイル: {src.name}")
    print(f"新ファイル: {out.name}")
    print("")
    print("追加された主なアンケート項目:")
    print("- 宿泊費（任意）")
    print("- 飲食費（任意）")
    print("- お土産・買い物代（任意）")
    print("- 体験・施設入場料（任意）")
    print("- クエスト掲載店・有料施設での消費額（必須）")
    print("- アプリがきっかけの来店・来訪有無（必須）")
    print("- アプリがきっかけで訪れたスポット（「はい」の場合必須）")
    print("- アプリがなくても訪問・利用したか（「はい」の場合必須）")
    print("")
    print("Supabaseは既存の quest_progress.note にJSON保存するため、DBの列追加は不要です。")

if __name__ == "__main__":
    main()
