def app_focus_url(qid: str) -> str:
    """地図のポップアップから該当クエストを表示するURLを作る"""
    params = {}

    nickname = st.session_state.get("participant_id", "")
    if nickname:
        params["pid"] = nickname

    params["focus_qid"] = qid

    # Foliumはiframe内なので、アプリ本体のルートへ戻す
    return "/?" + urllib.parse.urlencode(params)


def quest_map_popup_html(q: Dict, include_distance: bool = True) -> str:
    qid = q.get("quest_id", "")
    display_q = display_quest_for_list(q)

    dist = (
        format_distance(distance_to_quest_m(q))
        if include_distance
        else "距離不明"
    )

    tags = " / ".join(
        [str(t) for t in display_q.get("tags", [])]
    )

    official_url = html.escape(
        display_q.get("official_url", ""),
        quote=True,
    )

    maps_url = html.escape(
        google_maps_search_url(
            display_q.get("linked_name", ""),
            display_q.get("area", ""),
        ),
        quote=True,
    )

    quest_url = html.escape(
        app_focus_url(qid),
        quote=True,
    )

    description = html.escape(
        display_q.get("description", "")
    )

    condition = html.escape(
        display_q.get("condition", "")
    )

    official_html = ""

    if official_url:
        official_html = f"""
        <a
            href="{official_url}"
            target="_blank"
            style="
                font-size:12px;
                color:#2563eb;
                font-weight:600;
                text-decoration:none;
            "
        >
            公式ページ
        </a>
        """

    maps_html = ""

    if display_q.get("linked_name") != "シークレット":
        maps_html = f"""
        <a
            href="{maps_url}"
            target="_blank"
            style="
                font-size:12px;
                color:#2563eb;
                font-weight:600;
                text-decoration:none;
            "
        >
            Googleマップ
        </a>
        """

    return f"""
    <div
        style="
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                'Segoe UI',
                sans-serif;

            width:300px;
            line-height:1.5;
        "
    >

        <h4
            style="
                margin:0 0 6px 0;
                color:#174ea6;
            "
        >
            📍 {html.escape(display_q.get('quest_name', ''))}
        </h4>

        <div
            style="
                font-size:12px;
                color:#64748b;
                margin-bottom:6px;
            "
        >
            {html.escape(display_q.get('linked_name', ''))}
            <br>

            {html.escape(display_q.get('area', ''))}
            /
            {html.escape(display_q.get('quest_type', ''))}
            /
            {html.escape(display_q.get('season', ''))}
        </div>

        {schedule_status_badge_html(q)}

        <p
            style="
                font-size:13px;
                margin:8px 0;
            "
        >
            <b>クエスト内容</b>
            <br>
            {description}
        </p>

        <p
            style="
                font-size:13px;
                margin:8px 0;
            "
        >
            <b>クリア条件</b>
            <br>
            GPS判定・写真
        </p>

        <p
            style="
                font-size:12px;
                color:#2563eb;
                margin:8px 0;
            "
        >
            <b>現在地からの距離</b>
            ：
            {html.escape(dist)}
        </p>

        <div
            style="
                margin-top:12px;
            "
        >

            <a
                href="{quest_url}"
                target="_top"
                style="
                    display:block;
                    width:100%;
                    box-sizing:border-box;
                    text-align:center;
                    font-size:14px;
                    font-weight:700;
                    color:white;
                    background:#2563eb;
                    padding:10px 12px;
                    border-radius:12px;
                    text-decoration:none;
                    margin-bottom:10px;
                "
            >
                このクエストを見る
            </a>

            <div
                style="
                    display:flex;
                    gap:12px;
                    flex-wrap:wrap;
                "
            >
                {official_html}
                {maps_html}
            </div>

        </div>

    </div>
    """


def render_quest_map(
    quests_to_show: Optional[List[Dict]] = None,
    map_title: str = "🗺️ クエストマップ",
) -> Optional[str]:

    if map_title:
        st.subheader(map_title)

    st.caption(
        "気になる場所のピンをタップして、クエストを選んでください。"
    )

    if folium is None or st_folium is None:

        st.error(
            "地図を表示するには folium と "
            "streamlit-folium が必要です。"
        )

        return None

    # -------------------------
    # 表示するクエスト
    # -------------------------

    if quests_to_show is not None:
        all_quests = list(quests_to_show)

    else:
        all_quests = list(QUESTS) + list(STORY_QUESTS)

    quests_with_coords = [
        q
        for q in all_quests
        if get_coord(q)
    ]

    quests_without_coords = [
        q
        for q in all_quests
        if not get_coord(q)
    ]

    # -------------------------
    # 現在地
    # -------------------------

    loc = current_location()

    if loc:

        st.success(
            f"📍 現在地取得済み"
        )

    # -------------------------
    # 地図
    # -------------------------

    m = folium.Map(
        location=[32.45, 130.20],
        zoom_start=9,
        min_zoom=7,
        tiles="OpenStreetMap",
    )

    # 天草全体が見やすい範囲
    try:

        m.fit_bounds(
            [
                [32.05, 129.85],
                [32.68, 130.55],
            ]
        )

    except Exception:
        pass

    # -------------------------
    # 現在地マーカー
    # -------------------------

    if loc:

        folium.Marker(
            location=loc,
            tooltip="現在地",
            popup=folium.Popup(
                "現在地",
                max_width=180,
            ),
            icon=folium.Icon(
                color="blue",
                icon="location-arrow",
                prefix="fa",
            ),
        ).add_to(m)

        folium.Circle(
            location=loc,
            radius=st.session_state.get(
                "gps_radius_m",
                300,
            ),
            color="blue",
            fill=False,
        ).add_to(m)

    # -------------------------
    # クエスト種類ごとの色
    # -------------------------

    type_color = {

        "祭り、イベント":
            "red",

        "歴史、文化、ミュージアム":
            "cadetblue",

        "食":
            "orange",

        "自然、海":
            "green",

        "体験、工芸、ものづくり":
            "darkblue",
    }

    bounds = []

    # -------------------------
    # クエストピン
    # -------------------------

    for q in quests_with_coords:

        coord = get_coord(q)

        if not coord:
            continue

        bounds.append(coord)

        display_q = display_quest_for_list(q)

        qtype = display_q.get(
            "quest_type",
            "",
        )

        qid = q.get(
            "quest_id",
            "",
        )

        completed = (
            qid
            in st.session_state.completed
        )

        if completed:

            icon_color = "gray"

        else:

            icon_color = type_color.get(
                qtype,
                "blue",
            )

        quest_name = display_q.get(
            "quest_name",
            "",
        )

        tooltip = (
            f"✅ {quest_name}"
            if completed
            else quest_name
        )

        folium.Marker(
            location=coord,

            tooltip=tooltip,

            popup=folium.Popup(
                quest_map_popup_html(q),
                max_width=360,
            ),

            icon=folium.Icon(
                color=icon_color,
                icon=(
                    "flag"
                    if completed
                    else "map-marker"
                ),
                prefix="fa",
            ),

        ).add_to(m)

    # -------------------------
    # クエスト全体を表示
    # -------------------------

    if bounds and len(bounds) > 1:

        try:

            m.fit_bounds(bounds)

        except Exception:
            pass

    # -------------------------
    # Streamlitへ地図表示
    # -------------------------

    map_state = st_folium(
        m,
        width=None,
        height=480,
        use_container_width=True,

        returned_objects=[
            "last_object_clicked"
        ],

        key=(
            "quest_map_"
            + str(
                abs(
                    hash(
                        tuple(
                            q.get(
                                "quest_id",
                                "",
                            )
                            for q
                            in all_quests
                        )
                    )
                )
            )
        ),
    )

    # -------------------------
    # 選択中クエスト
    # -------------------------

    selected_qid = (
        st.session_state.get(
            "map_selected_qid",
            "",
        )
    )

    clicked = (
        (map_state or {})
        .get(
            "last_object_clicked"
        )
        or {}
    )

    # -------------------------
    # ピンのクリック判定
    # -------------------------

    if (
        clicked
        and clicked.get("lat")
        is not None
        and clicked.get("lng")
        is not None
    ):

        click_lat = float(
            clicked["lat"]
        )

        click_lng = float(
            clicked["lng"]
        )

        closest_qid = ""

        closest_d = float("inf")

        for candidate in quests_with_coords:

            candidate_coord = (
                get_coord(candidate)
            )

            if not candidate_coord:
                continue

            d = haversine_m(
                click_lat,
                click_lng,
                candidate_coord[0],
                candidate_coord[1],
            )

            if d < closest_d:

                closest_d = d

                closest_qid = (
                    candidate.get(
                        "quest_id",
                        "",
                    )
                )

        # 約30m以内
        if (
            closest_qid
            and closest_d <= 30
        ):

            selected_qid = closest_qid

            st.session_state[
                "map_selected_qid"
            ] = closest_qid

    # -------------------------
    # 地図下のクエスト選択UI
    # -------------------------

    if selected_qid:

        selected_q = next(
            (
                q
                for q in all_quests
                if q.get(
                    "quest_id"
                )
                == selected_qid
            ),
            None,
        )

        if selected_q:

            selected_display = (
                display_quest_for_list(
                    selected_q
                )
            )

            st.markdown(
                f"""
                <div
                    style="
                        background:
                            linear-gradient(
                                135deg,
                                #eff6ff,
                                #dbeafe
                            );
                        border:
                            1px solid #bfdbfe;
                        border-radius:16px;
                        padding:14px 16px;
                        margin-top:8px;
                        margin-bottom:10px;
                    "
                >

                    <div
                        style="
                            color:#64748b;
                            font-size:12px;
                            font-weight:700;
                        "
                    >
                        選択中のクエスト
                    </div>

                    <div
                        style="
                            color:#174ea6;
                            font-size:18px;
                            font-weight:800;
                            margin-top:3px;
                        "
                    >
                        📍
                        {
                            selected_display.get(
                                'quest_name',
                                '',
                            )
                        }
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "このクエストを見る",
                key=(
                    f"open_map_quest_"
                    f"{selected_qid}"
                ),
                type="primary",
                use_container_width=True,
            ):

                # -------------------------
                # URLへクエストIDを保存
                # -------------------------

                try:

                    nickname = (
                        st.session_state.get(
                            "participant_id",
                            "",
                        )
                    )

                    if nickname:

                        st.query_params[
                            "pid"
                        ] = nickname

                    st.query_params[
                        "focus_qid"
                    ] = selected_qid

                except Exception:
                    pass

                # -------------------------
                # セッションにも保存
                # -------------------------

                st.session_state[
                    "map_selected_qid"
                ] = selected_qid

                # 再描画
                st.rerun()

    # -------------------------
    # 座標未登録
    # -------------------------

    if quests_without_coords:

        with st.expander(
            "座標未登録のクエスト",
            expanded=False,
        ):

            st.warning(
                "以下のクエストは"
                "地図に表示できません。"
            )

            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "quest_id":
                                q.get(
                                    "quest_id",
                                    "",
                                ),

                            "クエスト名":
                                display_quest_for_list(
                                    q
                                ).get(
                                    "quest_name",
                                    "",
                                ),

                            "施設・イベント":
                                display_quest_for_list(
                                    q
                                ).get(
                                    "linked_name",
                                    "",
                                ),

                            "エリア":
                                classified_area(q),
                        }

                        for q
                        in quests_without_coords
                    ]
                ),

                use_container_width=True,
            )

    return selected_qid
