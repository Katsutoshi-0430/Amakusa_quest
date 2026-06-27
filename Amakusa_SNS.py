# -*- coding: utf-8 -*-
"""
天草つながりクエスト / Amakusa Link Quest
Streamlit prototype
"""

from __future__ import annotations

import base64
import html
import inspect
import math
import re
import urllib.parse
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

try:
    import folium
    from streamlit_folium import st_folium
except ModuleNotFoundError:
    folium = None
    st_folium = None

try:
    from streamlit_js_eval import get_geolocation
except ModuleNotFoundError:
    get_geolocation = None


# =====================================================================
# ★ 絶対基準位置：黒い画面をどこで開いても「このファイルがある場所」を見る
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent


# -----------------------------
# Story Quests (ストーリーモード専用クエスト)
# -----------------------------
STORY_QUESTS: List[Dict] = [
    {
        "quest_id": "story_1_shiro",
        "quest_name": "天草四郎との出会い",
        "linked_name": "天草四郎ミュージアム",
        "quest_type": "ストーリー",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "知る",
        "tags": ["歴史・文化", "ストーリー", "ミュージアム"],
        "description": "天草四郎ゆかりの地をめぐる旅が今、始まる。まずはミュージアムで四郎の生い立ちを学ぼう。",
        "condition": "天草四郎ミュージアムを訪れる",
        "official_url": "https://www.t-island.jp/spot/137",
        "status": "確認済み",
        "trivia": "【プチ情報】天草四郎ミュージアムでは、島原・天草一揆の歴史や四郎の真の姿に迫る貴重な資料が展示されています。四郎はわずか16歳で一揆の総大将になったと言い伝えられています！"
    },
    {
        "quest_id": "story_2_senganzan",
        "quest_name": "絶景の山で仲間を集めろ",
        "linked_name": "千巌山",
        "quest_type": "ストーリー",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "知る",
        "tags": ["自然・海", "ストーリー", "絶景"],
        "description": "かつて天草四郎が陣を敷いたとされる山。山頂からの絶景の中で仲間を集めよう。",
        "condition": "千巌山を訪れる",
        "official_url": "https://www.t-island.jp/spot/45",
        "status": "確認済み",
        "trivia": "【プチ情報】千巌山（せんがんざん）は、天草四郎が出陣前に祝宴をあげたと伝わる場所です。山頂からは天草五橋や島々が浮かぶ絶景を大パノラマで見渡すことができます！"
    },
    {
        "quest_id": "story_3_ueno",
        "quest_name": "天草大王コロッケで腹ごしらえ",
        "linked_name": "ファミリーショップうえの",
        "quest_type": "ストーリー",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる",
        "tags": ["食", "ストーリー", "地元の人"],
        "description": "長旅の腹ごしらえに、地元で愛される天草大王コロッケを味わおう。",
        "condition": "ファミリーショップうえのを訪れ、コロッケを味わう",
        "official_url": "https://www.t-island.jp/",
        "status": "確認済み",
        "trivia": "【プチ情報】天草大王は、国内最大級の地鶏！昭和初期に一度絶滅してしまいましたが、奇跡的に復元された幻の地鶏です。そのお肉を使ったコロッケは絶品！"
    },
    {
        "quest_id": "story_4_kirishitan",
        "quest_name": "奇跡の旗を探し出せ",
        "linked_name": "天草キリシタン館",
        "quest_type": "ストーリー",
        "area": "本渡",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "知る",
        "tags": ["歴史・文化", "ストーリー", "ミュージアム"],
        "description": "一揆軍が掲げたという奇跡の陣中旗。その実物やレプリカを探し出そう。",
        "condition": "天草キリシタン館を訪れる",
        "official_url": "https://www.t-island.jp/spot/3",
        "status": "確認済み",
        "trivia": "【プチ情報】天草キリシタン館には、国指定重要文化財である「天草四郎陣中旗」が収蔵されています。血痕や矢の跡が残るこの旗は、激しい戦いの歴史を今に伝えています。"
    },
    {
        "quest_id": "story_5_tomioka",
        "quest_name": "難攻不落の城を調査せよ",
        "linked_name": "富岡城跡",
        "quest_type": "ストーリー",
        "area": "苓北",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "知る",
        "tags": ["歴史・文化", "ストーリー", "絶景"],
        "description": "一揆軍が攻撃しても落とすことができなかった堅固な富岡城の跡地を調査しよう。",
        "condition": "富岡城跡を訪れる",
        "official_url": "https://kankou.reihoku-kumamoto.jp/list00417.html",
        "status": "確認済み",
        "trivia": "【プチ情報】富岡城は、島原・天草一揆の際に一揆軍が半月にわたり猛攻撃を仕掛けましたが、城の守りが非常に堅く、ついに落とすことができなかった難攻不落の城です。"
    },
    {
        "quest_id": "story_6_sakitsu",
        "quest_name": "平和な街へたどり着け",
        "linked_name": "崎津集落",
        "quest_type": "ストーリー",
        "area": "崎津",
        "season": "通年",
        "period": "通年",
        "stay_fit": "宿泊推奨",
        "connection_level": "知る",
        "tags": ["歴史・文化", "ストーリー", "写真"],
        "description": "潜伏キリシタンの歴史と、平和な時代を迎えた美しい漁村の風景を目に焼き付けよう。",
        "condition": "崎津集落を訪れる",
        "official_url": "https://www.t-island.jp/spot/2754",
        "status": "確認済み",
        "trivia": "【プチ情報】崎津（﨑津）集落は、「長崎と天草地方の潜伏キリシタン関連遺産」として世界文化遺産に登録されています。禁教期にも信仰を守り抜き、仏教や神道と共存した平和で美しい漁村です。"
    },
]

# -----------------------------
# Verified quest database
# -----------------------------
QUESTS: List[Dict] = [
    {
        "quest_id": "event_ushibuka_haiya_2026",
        "quest_name": "牛深ハイヤ祭りに参加する",
        "linked_name": "牛深ハイヤ祭り",
        "quest_type": "祭り・イベント",
        "area": "牛深",
        "season": "春",
        "period": "2026年4月17日(金)〜4月19日(日)",
        "stay_fit": "宿泊推奨",
        "connection_level": "参加する",
        "tags": ["祭り・イベント", "歴史・文化", "地元の人", "写真"],
        "description": "江戸時代から引き継がれる牛深ハイヤ節の祭りに参加し、地域の伝統芸能に触れるクエスト。",
        "condition": "会場に行き、印象に残った演舞・場面を記録する。",
        "official_url": "https://www.t-island.jp/event/2400",
        "status": "確認済み",
    },
    {
        "quest_id": "event_hondo_haiya_2025",
        "quest_name": "天草ほんどハイヤ祭りで夜の本渡を体験する",
        "linked_name": "天草ほんどハイヤ祭り",
        "quest_type": "祭り・イベント",
        "area": "本渡",
        "season": "夏",
        "period": "夏の夜に開催",
        "stay_fit": "宿泊推奨",
        "connection_level": "参加する",
        "tags": ["祭り・イベント", "食", "写真", "地元の人"],
        "description": "本渡港一帯で行われるハイヤ祭り・花火・マルシェを通じて、夜の天草に関わるクエスト。",
        "condition": "会場で祭り・マルシェ・花火のいずれかを体験し、記録する。",
        "official_url": "https://www.t-island.jp/event/2349",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_goshoura_museum",
        "quest_name": "御所浦恐竜の島博物館で“恐竜の島”を学ぶ",
        "linked_name": "御所浦恐竜の島博物館",
        "quest_type": "ミュージアム・文化施設",
        "area": "御所浦",
        "season": "通年",
        "period": "通年",
        "stay_fit": "宿泊推奨",
        "connection_level": "知る",
        "tags": ["ミュージアム", "親子で学ぶ", "自然・海"],
        "description": "御所浦の化石・地質・島の成り立ちを学び、自然と地域の関係に触れるクエスト。",
        "condition": "展示を見て、印象に残った化石を記録する。",
        "official_url": "https://goshouramuseum.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_dolphin_center",
        "quest_name": "道の駅 天草市イルカセンターでイルカを知る",
        "linked_name": "道の駅 天草市イルカセンター",
        "quest_type": "自然・海の体験",
        "area": "五和",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "体験する",
        "tags": ["自然・海", "親子で学ぶ", "写真"],
        "description": "イルカウォッチングを通じて、天草の豊かな海に触れるクエスト。",
        "condition": "施設を訪れ、知ったことを記録する。",
        "official_url": "https://www.t-island.jp/spot/2837",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_lisola",
        "quest_name": "リゾラテラス天草で海辺の食を楽しむ",
        "linked_name": "リゾラテラス天草",
        "quest_type": "食・物産",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる・買う",
        "tags": ["食", "自然・海", "写真", "癒し"],
        "description": "海辺のレストランを通じて、天草の食と滞在価値に触れるクエスト。",
        "condition": "食べたもの・印象に残った風景を記録する。",
        "official_url": "https://www.seacruise.jp/lisolaterrace/",
        "status": "確認済み",
    },
    {
        "quest_id": "food_sun_haraippai_amakusa_daio",
        "quest_name": "天草大王バルで幻の地鶏を味わう",
        "linked_name": "天草大王バル サン・はらいっぱい",
        "quest_type": "食・物産",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる",
        "tags": ["食", "地元の人", "写真"],
        "description": "上天草の地鶏ブランドである天草大王を使った料理を味わうクエスト。",
        "condition": "店舗を訪れ、天草大王料理を食べ記録する。",
        "official_url": "https://kami-amakusa.jp/archives/eat",
        "status": "確認済み",
    },
    {
        "quest_id": "food_fukuzumi_kaisendon",
        "quest_name": "いけす料理ふくずみで海鮮丼を攻略する",
        "linked_name": "いけす料理ふくずみ",
        "quest_type": "食・物産",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる",
        "tags": ["食", "自然・海", "写真"],
        "description": "いけす料理の店で新鮮な海鮮丼を食べ、天草の海の恵みを味わうクエスト。",
        "condition": "店舗を訪れ、海鮮丼を食べ感想を記録する。",
        "official_url": "https://kami-amakusa.jp/archives/eat",
        "status": "確認済み",
    },
]

QUESTS.extend(STORY_QUESTS)

OBJECTIVES = [
    "祭り・イベント", "歴史・文化", "ミュージアム", "食", "自然・海",
    "工芸・ものづくり", "地元の人", "親子で学ぶ", "雨でも楽しむ", "写真", "癒し", "ストーリー", "特になし"
]
STAY_OPTIONS = ["日帰り", "宿泊", "まだ決めていない"]
SEASONS = ["今日・今週", "春", "夏", "秋", "冬", "通年", "日程未定"]
AREAS = ["指定なし"] + sorted({q["area"] for q in QUESTS})

QUEST_COORDS: Dict[str, Tuple[float, float]] = {
    "event_ushibuka_haiya_2026": (32.1980, 130.0254),
    "event_hondo_haiya_2025": (32.4587, 130.1919),
    "spot_goshoura_museum": (32.3197, 130.3278),
    "spot_dolphin_center": (32.5582, 130.1696),
    "spot_lisola": (32.5860, 130.4285),
    "food_sun_haraippai_amakusa_daio": (32.5860, 130.4285),
    "food_fukuzumi_kaisendon": (32.5860, 130.4285),
    "story_1_shiro": (32.5896, 130.4322),
    "story_2_senganzan": (32.5181, 130.4285),
    "story_3_ueno": (32.5320, 130.4150),
    "story_4_kirishitan": (32.4569, 130.1926),
    "story_5_tomioka": (32.5227, 130.0367),
    "story_6_sakitsu": (32.3154, 130.0264),
}

PLACE_PHOTO_DIR = BASE_DIR / "quest_place_photos"
PLACE_PHOTO_EXTS = ["jpg", "jpeg", "png", "webp"]
CATEGORY_PLACEHOLDER = {
    "祭り・イベント": {"emoji": "🎆", "label": "地域の祭り・イベント"},
    "ミュージアム・文化施設": {"emoji": "🏛️", "label": "歴史・文化施設"},
    "歴史・文化スポット": {"emoji": "⛪", "label": "天草の歴史文化"},
    "自然・海の体験": {"emoji": "🌊", "label": "海と自然の体験"},
    "観光交流拠点": {"emoji": "🧭", "label": "観光交流拠点"},
    "食・物産": {"emoji": "🍽️", "label": "天草の食・物産"},
    "工芸・ものづくり": {"emoji": "🏺", "label": "工芸・ものづくり"},
    "ストーリー": {"emoji": "📖", "label": "ストーリー進行"},
}


def place_photo_path(quest_id: str) -> Optional[Path]:
    for ext in PLACE_PHOTO_EXTS:
        p = PLACE_PHOTO_DIR / f"{quest_id}.{ext}"
        if p.exists():
            return p
    return None

def save_place_photo(quest_id: str, uploaded_file) -> Path:
    PLACE_PHOTO_DIR.mkdir(exist_ok=True)
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        suffix = ".jpg"
    for ext in PLACE_PHOTO_EXTS:
        old = PLACE_PHOTO_DIR / f"{quest_id}.{ext}"
        if old.exists():
            old.unlink()
    dest = PLACE_PHOTO_DIR / f"{quest_id}{suffix}"
    dest.write_bytes(uploaded_file.getvalue())
    return dest

def render_placeholder_place_card(q: Dict, compact: bool = False) -> None:
    info = CATEGORY_PLACEHOLDER.get(q.get("quest_type", ""), {"emoji": "📍", "label": "天草の地域クエスト"})
    height = 118 if compact else 220
    emoji_size = 38 if compact else 64
    label_size = 16 if compact else 22
    st.markdown(
        f"""
        <div style="
            height:{height}px;
            border-radius:18px;
            background:linear-gradient(135deg,#e8f4ff,#fff7fb);
            border:1px solid #dbeafe;
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            text-align:center;
            margin:8px 0 12px 0;
        ">
            <div style="font-size:{emoji_size}px; line-height:1; margin-bottom:8px;">{info['emoji']}</div>
            <div style="font-size:{label_size}px; font-weight:800; color:#24506b;">{html.escape(info['label'])}</div>
            <div style="font-size:12px; color:#60758a; margin-top:6px;">{html.escape(q['linked_name'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_place_photo(q: Dict, compact: bool = False) -> None:
    image_url = q.get("place_image_url", "")
    if image_url:
        st.image(image_url, caption=f"{q['linked_name']}", use_container_width=True)
        return
    p = place_photo_path(q["quest_id"])
    if p:
        st.image(str(p), caption=f"{q['linked_name']}", use_container_width=True)
    else:
        render_placeholder_place_card(q, compact=compact)


# ---------------------------------------------------------------------
# Character Evolution Database (★ ①②③個別画像連動版 ★)
# ---------------------------------------------------------------------
CHARACTER_IMAGE_DIR = BASE_DIR / "character_images"

CHARACTERS: Dict[str, Dict] = {
    # --- 通常キャラクター ---
    "shirasui": { "rarity": "レア", "series": "元気系", "stages": [{"name": "シラスイくん", "emoji": "🔥", "catch": "情熱的な精霊"}, {"name": "シラスイ将軍", "emoji": "☄️", "catch": "頼もしい将軍"}, {"name": "シラスイ大将軍", "emoji": "🌋", "catch": "炎の最終形態"}] },
    "hoshimi": { "rarity": "レア", "series": "夜・祭り", "stages": [{"name": "ほしみちゃん", "emoji": "✨", "catch": "キラキラの妖精"}, {"name": "ほしみ姫", "emoji": "🌟", "catch": "夜空を照らす姫"}, {"name": "ほしみ女神", "emoji": "💫", "catch": "夜を見守る女神"}] },
    "irukacchi": { "rarity": "ノーマル", "series": "海の仲間", "stages": [{"name": "イルカっち", "emoji": "🐬", "catch": "すばやい仲間"}, {"name": "イルカ王子", "emoji": "👑", "catch": "海の人気者"}, {"name": "イルカ大王", "emoji": "🐋", "catch": "海原を泳ぐ大王"}] },
    "kairun": { "rarity": "ノーマル", "series": "海の仲間", "stages": [{"name": "かいルン", "emoji": "🐚", "catch": "宝物を隠しているよ"}, {"name": "かい姫", "emoji": "🦪", "catch": "綺麗なお姫様"}, {"name": "かい女王", "emoji": "💎", "catch": "宝物を司る女王"}] },
    "amanya": { "rarity": "ノーマル", "series": "島の仲間", "stages": [{"name": "あまにゃん", "emoji": "🐾", "catch": "町歩きが好き"}, {"name": "あまにゃん将軍", "emoji": "😸", "catch": "町のボス"}, {"name": "あまにゃん大王", "emoji": "😼", "catch": "気まぐれ大王"}] },

    # --- ★ ストーリー限定キャラクター（ご指定の①②③ファイル名に完全対応） ★ ---
    "story_char_amakusa_siro": {
        "rarity": "スーパーレア", "series": "ストーリー・歴史",
        "stages": [
            {"name": "天草四郎（志士）", "emoji": "⚔️", "catch": "マントを羽織り、日本刀を携えた若きカリスマ！", "img_id": "story_char_amakusa_siro①"},
            {"name": "天草四郎・覚醒", "emoji": "🕊️", "catch": "天草の人々の祈りを受け、力強く成長した姿！", "img_id": "story_char_amakusa_siro②"},
            {"name": "天草四郎・聖将大天草", "emoji": "🌟", "catch": "天草に永遠の平和をもたらす伝説の聖将！", "img_id": "story_char_amakusa_siro③"}
        ]
    },
    "story_char_senganzan": {
        "rarity": "レア", "series": "ストーリー・自然",
        "stages": [
            {"name": "千巌まる", "emoji": "⛰️", "catch": "千巌山の名水から生まれた、笑顔の山の精！", "img_id": "story_char_senganzan①"},
            {"name": "千巌大権現", "emoji": "🐉", "catch": "富士を望むパワーを吸収して多腕に進化した姿！", "img_id": "story_char_senganzan②"},
            {"name": "千巌・銀河龍神", "emoji": "🌌", "catch": "天草から宇宙へ！銀河を注ぐ伝説の山神！", "img_id": "story_char_senganzan③"}
        ]
    },
    "story_char_amakusa_daio": {
        "rarity": "ウルトラレア", "series": "ストーリー・食",
        "stages": [
            {"name": "天草大王", "emoji": "🐔", "catch": "【大王の威風】味方全体の攻撃力を小アップさせる。", "img_id": "story_char_amakusa_daio①"},
            {"name": "天草大王・烈", "emoji": "🔥", "catch": "【烈火の連撃】敵単体に強力な火属性ダメージを与える。", "img_id": "story_char_amakusa_daio②"},
            {"name": "天草大王・天焔", "emoji": "🌋", "catch": "【天焔の覇王撃】敵全体に超強力な火属性ダメージを与える。", "img_id": "story_char_amakusa_daio③"}
        ]
    },
    "story_char_maria_kannon": {
        "rarity": "スーパーレア", "series": "ストーリー・信仰",
        "stages": [
            {"name": "マリア観音", "emoji": "🙏", "catch": "天草の祈りをそっと包み込む、温かな慈愛の像。", "img_id": "story_char_maria_kannon①"},
            {"name": "聖天使マリア", "emoji": "👼", "catch": "黄金の翼を広げ、祝福をもたらす大天使の姿！", "img_id": "story_char_maria_kannon②"},
            {"name": "聖母マリア・星核創世神", "emoji": "🌌", "catch": "銀河を掌に宿す、宇宙規模の聖母神！", "img_id": "story_char_maria_kannon③"}
        ]
    },
    "story_char_tomiokajo": {
        "rarity": "レア", "series": "ストーリー・城郭",
        "stages": [
            {"name": "とみっち", "emoji": "🏯", "catch": "苓北の海を見守る、元気いっぱいなお城のマスコット！", "img_id": "story_char_tomiokajo①"},
            {"name": "とみまる", "emoji": "🚩", "catch": "「富岡城」の旗を掲げて頼もしくなったお城の精！", "img_id": "story_char_tomiokajo②"},
            {"name": "富岡城・守護大将", "emoji": "🛡️", "catch": "黄金の装飾と錫杖を授かった、難攻不落の守護大将！", "img_id": "story_char_tomiokajo③"}
        ]
    },
    "story_char_sakitsu_syuraku": {
        "rarity": "スーパーレア", "series": "ストーリー・平和",
        "stages": [
            {"name": "ピースピヨ", "emoji": "🕊️", "catch": "オリーブの枝をくわえた、愛らしい平和の小鳩。", "img_id": "story_char_sakitsu_syuraku①"},
            {"name": "オリーブ鳩", "emoji": "🌿", "catch": "胸に綺麗で大きなハートの宝石を宿した聖なる使者！", "img_id": "story_char_sakitsu_syuraku②"},
            {"name": "聖愛の平和神鳩", "emoji": "👑", "catch": "黄金の冠と大きなダイヤをまとった、崎津の守護神鳩！", "img_id": "story_char_sakitsu_syuraku③"}
        ]
    },
}

QUEST_CHARACTER_REWARDS: Dict[str, str] = {
    "event_ushibuka_haiya_2026": "shirasui",
    "event_hondo_haiya_2025": "hoshimi",
    "spot_dolphin_center": "irukacchi",
    "spot_lisola": "kairun",
    # ストーリーキャラ紐づけ
    "story_1_shiro": "story_char_amakusa_siro",
    "story_2_senganzan": "story_char_senganzan",
    "story_3_ueno": "story_char_amakusa_daio",
    "story_4_kirishitan": "story_char_maria_kannon",
    "story_5_tomioka": "story_char_tomiokajo",
    "story_6_sakitsu": "story_char_sakitsu_syuraku",
}


def character_image_path(lookup_id: str) -> Optional[Path]:
    exts = ["png", "jpg", "jpeg", "webp", "jpg.jpg", "PNG", "JPG"]
    
    # 1. ①つきの名前でそのまま探す
    for ext in exts:
        p = CHARACTER_IMAGE_DIR / f"{lookup_id}.{ext}"
        if p.exists():
            return p

    # 2. パソコンの自動変換対策： ①②③ を普通の 1, 2, 3 に変えても探す
    alt_id = lookup_id.replace("①", "1").replace("②", "2").replace("③", "3")
    if alt_id != lookup_id:
        for ext in exts:
            p = CHARACTER_IMAGE_DIR / f"{alt_id}.{ext}"
            if p.exists():
                return p

    # 3. それでも無ければ、ベースID（語尾の数字なし）でも探す
    base_id = re.sub(r"[①②③123]$", "", lookup_id)
    if base_id != lookup_id:
        for ext in exts:
            p = CHARACTER_IMAGE_DIR / f"{base_id}.{ext}"
            if p.exists():
                return p

    return None

def get_character_stage(cid: str) -> dict:
    base_char = CHARACTERS.get(cid)
    
    if not base_char:
        base_char = CHARACTERS["amanya"]
        cid = "amanya"
        
    fed = st.session_state.character_apples.get(cid, 0)
    stages = base_char["stages"]
    
    if fed >= 20: stage_idx = 2
    elif fed >= 10: stage_idx = 1
    else: stage_idx = 0
        
    res = dict(base_char)
    res.update(stages[stage_idx])
    res["stage_idx"] = stage_idx
    res["fed_apples"] = fed
    res["character_id"] = cid
    return res

def get_character_for_quest(q: Dict) -> Dict:
    cid = QUEST_CHARACTER_REWARDS.get(q["quest_id"])
    if not cid or cid not in CHARACTERS:
        tags = set(q.get("tags", []) + [q.get("quest_type", "")])
        cid = "amanya"
        if "自然・海" in tags: cid = "irukacchi"
        elif "食" in tags: cid = "kueta"
        elif "祭り・イベント" in tags: cid = "shirasui"
    
    return get_character_stage(cid)

def award_character_for_quest(q: Dict) -> Dict:
    char = get_character_for_quest(q)
    cid = char["character_id"]
    qid = q["quest_id"]
    st.session_state.quest_character_rewards[qid] = cid
    if cid not in st.session_state.unlocked_character_ids:
        st.session_state.unlocked_character_ids.add(cid)
        st.session_state.unlocked_character_order.append(cid)
    return char

def render_character_card(char: Dict, locked: bool = False, compact: bool = False, show_enhance: bool = False) -> None:
    # ★ 連動の心臓部：段階ごとの img_id を優先して読みに行く
    lookup_id = char.get("img_id", char.get("character_id", ""))
    img = character_image_path(lookup_id)
    name = "？？？" if locked else char.get("name", "")
    rarity = char.get("rarity", "")
    series = char.get("series", "")
    catch = "まだ出会っていない仲間です。対応するクエストをクリアすると解放されます。" if locked else char.get("catch", "")
    emoji = "？" if locked else char.get("emoji", "✨")

    with st.container(border=True):
        if img:
            st.image(str(img), use_container_width=True)
        else:
            height = 110 if compact else 150
            font_size = 46 if compact else 62
            st.markdown(
                f"""
                <div style="height:{height}px; border-radius:18px; background:linear-gradient(135deg,#edf6ff,#fff7fb); border:1px solid #dbeafe; display:flex; align-items:center; justify-content:center; font-size:{font_size}px; filter:{'grayscale(1)' if locked else 'none'};">
                    {emoji}
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        if not locked:
            stage_idx = char.get("stage_idx", 0)
            stage_text = "✨ 最終進化" if stage_idx == 2 else ("⭐ 1段階進化" if stage_idx == 1 else "🌱 初期形態")
            st.caption(f"{stage_text}")
            
        st.markdown(f"**{name}**")
        st.caption(f"{rarity} / {series}")
        st.write(catch)
        
        if show_enhance and not locked:
            fed = char.get("fed_apples", 0)
            st.divider()
            
            if fed >= 20:
                st.progress(1.0)
                st.button("✨ 進化MAX", key=f"feed_{char.get('character_id')}", disabled=True, use_container_width=True)
            else:
                target = 20 if fed >= 10 else 10
                st.caption(f"次の進化まで： {fed} / {target} 個")
                st.progress(fed / 20.0)
                
                apples_owned = st.session_state.apples
                if st.button(f"🍎 リンゴをあげる", key=f"feed_{char.get('character_id')}", disabled=apples_owned <= 0, use_container_width=True):
                    st.session_state.apples -= 1
                    st.session_state.character_apples[char.get("character_id")] = fed + 1
                    if (fed + 1) == 10 or (fed + 1) == 20:
                        st.balloons()
                    st.rerun()


def render_character_collection() -> None:
    st.subheader("🎁 キャラクター図鑑 & 育成")
    st.write("クエストをクリアしてキャラクターを集めよう！手に入れた「🍎リンゴ」を10個あげると1進化、累計20個あげると最終進化します。")
    
    col1, col2 = st.columns(2)
    total = len(CHARACTERS)
    unlocked = len(st.session_state.unlocked_character_ids)
    col1.metric("獲得キャラクター", f"{unlocked} / {total}")
    col2.metric("所持しているリンゴ 🍎", f"{st.session_state.apples} 個")
    st.progress(unlocked / total if total else 0)

    st.markdown("### コレクション＆進化させる")
    character_ids = list(CHARACTERS.keys())

    for i in range(0, len(character_ids), 3):
        cols = st.columns(3)
        for col, cid in zip(cols, character_ids[i:i+3]):
            with col:
                locked = cid not in st.session_state.unlocked_character_ids
                c = get_character_stage(cid)
                render_character_card(c, locked=locked, compact=True, show_enhance=not locked)


# -----------------------------
# State helpers
# -----------------------------
def init_state() -> None:
    defaults = {
        "completed": set(),
        "completed_order": [],
        "favorites": set(),
        "notes": {},
        "photos": {},
        "photo_data": {},
        "photo_mime": {},
        "sns_texts": {},
        "x_post_urls": {},
        "diary": {},
        "unlocked_character_ids": set(),
        "unlocked_character_order": [],
        "quest_character_rewards": {},
        "user_lat": None,
        "user_lon": None,
        "user_accuracy": None,
        "user_location_source": "未取得",
        "gps_required": True,
        "gps_radius_m": 300,
        "manual_location_enabled": False,
        "apples": 0,
        "character_apples": {},
        "last_login_date": None,
        "story_progress": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_quest(quest_id: str) -> Dict:
    return next(q for q in QUESTS if q["quest_id"] == quest_id)

def season_match(q_season: str, selected_season: str) -> bool:
    if selected_season in ["日程未定", "今日・今週"]: return True
    if selected_season == "通年": return q_season == "通年"
    return q_season in [selected_season, "通年"]

OBJECTIVE_SYNONYMS = {
    "食": ["グルメ", "海鮮", "海鮮丼", "うに", "ウニ", "塩パン", "スイーツ", "カフェ", "ランチ", "天草大王", "車エビ", "魚", "寿司", "料理", "ちゃんぽん"],
    "自然・海": ["海", "自然", "絶景", "展望", "夕日", "イルカ", "海岸", "島", "公園", "滝", "橋"],
    "歴史・文化": ["歴史", "文化", "教会", "城", "城跡", "キリシタン", "崎津", "天草四郎", "神社"],
    "ミュージアム": ["博物館", "資料館", "展示", "学ぶ", "ミュージアム"],
    "工芸・ものづくり": ["陶器", "陶磁器", "窯元", "ものづくり", "工芸"],
    "祭り・イベント": ["祭り", "イベント", "花火", "ハイヤ", "フェスタ", "イルミネーション"],
    "癒し": ["温泉", "休む", "のんびり", "カフェ", "景色", "夕日"],
    "写真": ["写真", "映え", "フォト", "景色", "絶景"],
}

def normalize_text_for_match(text: str) -> str:
    return re.sub(r"\s+", "", str(text).lower())

def expand_objective_terms(objectives: List[str]) -> List[str]:
    terms: List[str] = []
    for obj in objectives:
        obj = str(obj).strip()
        if not obj or obj == "特になし": continue
        terms.append(obj)
        for key, values in OBJECTIVE_SYNONYMS.items():
            if obj == key or obj in values:
                terms.append(key)
                terms.extend(values)
    unique_terms: List[str] = []
    seen = set()
    for term in terms:
        norm = normalize_text_for_match(term)
        if norm and norm not in seen:
            seen.add(norm)
            unique_terms.append(term)
    return unique_terms

def parse_objective_text(text: str, existing: Optional[List[str]] = None, max_items: int = 3) -> List[str]:
    items: List[str] = list(existing or [])
    for token in re.split(r"[、,，/／\s]+", str(text)):
        token = token.strip()
        if token and token not in items:
            items.append(token)
        if len(items) >= max_items: break
    return items[:max_items]

def objective_match(q: Dict, objectives: List[str]) -> int:
    if not objectives or "特になし" in objectives: return 1
    tags = [str(t) for t in q.get("tags", [])] + [str(q.get("quest_type", ""))]
    tag_texts = [normalize_text_for_match(t) for t in tags]
    q_text = normalize_text_for_match(" ".join([
        q.get("quest_name", ""), q.get("linked_name", ""), q.get("quest_type", ""),
        q.get("area", ""), q.get("season", ""), q.get("description", ""), " ".join(q.get("tags", [])),
    ]))
    expanded_terms = expand_objective_terms(objectives)
    expanded_norms = [normalize_text_for_match(t) for t in expanded_terms]
    score = 0
    for term in expanded_terms:
        term_norm = normalize_text_for_match(term)
        if not term_norm: continue
        if term_norm in tag_texts: score += 5
        elif any(term_norm in tag or tag in tag_texts): score += 3
        elif term_norm in q_text: score += 2
    return score

def stay_match_score(q: Dict, stay: str) -> int:
    fit = q["stay_fit"]
    if stay == "宿泊": return 2 if fit == "宿泊推奨" else 1
    if stay == "日帰り": return 2 if fit == "日帰り可" else 0
    return 1

def get_current_season() -> str:
    month = date.today().month
    if 3 <= month <= 5: return "春"
    elif 6 <= month <= 8: return "夏"
    elif 9 <= month <= 11: return "秋"
    else: return "冬"

def recommend_quests(objectives: List[str], stay: str, season: str, area: str, keyword: str = "") -> List[Dict]:
    rows = []
    current_season = get_current_season()
    
    for q in QUESTS:
        if q.get("quest_type") == "ストーリー": continue
        if area != "指定なし" and q["area"] != area: continue
        if not season_match(q["season"], season): continue
        if keyword:
            kw = keyword.strip().lower()
            search_target = f"{q.get('quest_name','')} {q.get('linked_name','')} {q.get('description','')} {' '.join(q.get('tags',[]))}".lower()
            if kw not in search_target: continue
        
        obj_score = objective_match(q, objectives)
        stay_score = stay_match_score(q, stay)
        if objectives and "特になし" not in objectives and obj_score == 0: continue
        if stay == "日帰り" and q["stay_fit"] == "宿泊推奨": stay_score = 0
        
        season_bonus = 20 if q.get("season") == current_season else 0
        rows.append((obj_score * 10 + stay_score * 3 + season_bonus + (1 if q["status"] == "確認済み" else 0), q))
    
    rows.sort(key=lambda x: x[0], reverse=True)
    return [q for _, q in rows]

def make_sns_text(q: Dict) -> str:
    return f"天草つながりクエストで『{q['linked_name']}』に参加しました。\n{q['description']}\n#天草つながりクエスト #天草観光 #天草旅"

def x_share_url(text: str, url: str) -> str:
    base = "https://twitter.com/intent/tweet"
    params = urllib.parse.urlencode({"text": text, "url": url})
    return f"{base}?{params}"

def google_maps_search_url(place_name: str, area: str) -> str:
    q = urllib.parse.quote(f"{place_name} {area} 天草")
    return f"https://www.google.com/maps/search/?api=1&query={q}"

def parse_geolocation_payload(payload) -> Optional[Tuple[float, float, Optional[float]]]:
    if not payload or not isinstance(payload, dict): return None
    coords = payload.get("coords", payload)
    if not isinstance(coords, dict): return None
    try: return float(coords.get("latitude")), float(coords.get("longitude")), float(coords.get("accuracy")) if coords.get("accuracy") is not None else None
    except: return None

def set_current_location(lat: float, lon: float, accuracy: Optional[float] = None, source: str = "GPS") -> None:
    st.session_state.user_lat, st.session_state.user_lon, st.session_state.user_accuracy, st.session_state.user_location_source = lat, lon, accuracy, source

def current_location() -> Optional[Tuple[float, float]]:
    if st.session_state.get("user_lat") is None or st.session_state.get("user_lon") is None: return None
    return float(st.session_state.user_lat), float(st.session_state.user_lon)

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_coord(q: Dict) -> Optional[Tuple[float, float]]:
    return QUEST_COORDS.get(q["quest_id"])

def distance_to_quest_m(q: Dict) -> Optional[float]:
    loc, coord = current_location(), get_coord(q)
    return haversine_m(loc[0], loc[1], coord[0], coord[1]) if loc and coord else None

def is_near_quest(q: Dict) -> bool:
    if not st.session_state.get("gps_required", True): return True
    d = distance_to_quest_m(q)
    return d is not None and d <= float(st.session_state.get("gps_radius_m", 300))

def format_distance(d: Optional[float]) -> str:
    if d is None: return "距離不明"
    return f"約{d:.0f}m" if d < 1000 else f"約{d/1000:.1f}km"

def render_gps_panel_for_quest(q: Dict) -> bool:
    if not st.session_state.get("gps_required", True):
        st.info("デモ用にGPS訪問判定をOFFにしています。")
        return True
    coord = get_coord(q)
    if coord is None:
        st.warning("座標未登録のためGPS判定できません。")
        return False
    loc = current_location()
    if loc is None:
        st.warning("現在地が未取得です。サイドバーで設定してください。")
        return False
    d = distance_to_quest_m(q)
    radius = float(st.session_state.get("gps_radius_m", 300))
    if d is not None and d <= radius:
        st.success(f"GPS判定OK：目的地から{format_distance(d)}以内です。")
        return True
    st.error(f"GPS判定NG：目的地から{format_distance(d)}離れています。")
    return False

def image_data_url(qid: str) -> str:
    data = st.session_state.photo_data.get(qid)
    return f"data:{st.session_state.photo_mime.get(qid, 'image/jpeg')};base64,{base64.b64encode(data).decode('utf-8')}" if data else ""

def save_diary_record(q: Dict, note: str, sns_text: str, x_url: str) -> None:
    qid = q["quest_id"]
    char = get_character_for_quest(q)
    st.session_state.diary[qid] = {
        "date": date.today().isoformat(), "quest_name": q["quest_name"], "linked_name": q["linked_name"],
        "area": q["area"], "quest_type": q["quest_type"], "note": note, "sns_text": sns_text,
        "x_post_url": x_url, "photo_name": st.session_state.photos.get(qid, ""),
        "user_lat": st.session_state.get("user_lat"), "user_lon": st.session_state.get("user_lon"),
        "gps_accuracy": st.session_state.get("user_accuracy"), "gps_distance_m": distance_to_quest_m(q),
        "character_id": char["character_id"], "character_name": char["name"],
    }

def diary_popup_html(q: Dict) -> str:
    qid = q["quest_id"]
    record = st.session_state.diary.get(qid, {})
    note = html.escape(record.get("note", "感想はまだ記録されていません。"))
    sns_text = html.escape(record.get("sns_text", make_sns_text(q))).replace("\n", "<br>")
    char = get_character_for_quest(q)
    char_name, char_emoji = html.escape(record.get("character_name", char["name"])), html.escape(char.get("emoji", "✨"))
    char_html = f'<p style="font-size:13px; background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:8px;"><b>仲間になったキャラ</b><br>{char_emoji} {char_name}</p>'
    img_url = image_data_url(qid)
    img_html = f'<img src="{img_url}" style="width:260px; max-height:190px; object-fit:cover; border-radius:10px; margin:8px 0;" />' if img_url else '<p style="color:#777;">写真は未登録です。</p>'
    return f"""
    <div style="font-family: sans-serif; width: 285px;">
      <h4 style="margin-bottom:4px;">👣 {html.escape(q['linked_name'])}</h4>
      <div style="font-size:12px; color:#555; margin-bottom:6px;">{html.escape(record.get('date', date.today().isoformat()))} / {html.escape(q['area'])}</div>
      {img_html}<p style="font-size:13px;"><b>日記</b><br>{note}</p>{char_html}
    </div>
    """

def render_footprint_map() -> None:
    st.subheader("👣 足跡マップ・旅の日記")
    if folium is None or st_folium is None:
        st.error("地図を表示するには folium と streamlit-folium が必要です。")
        return
    done_ids = [qid for qid in st.session_state.completed_order if qid in st.session_state.completed]
    m = folium.Map(location=[32.43, 130.19], zoom_start=9, tiles="OpenStreetMap")
    loc = current_location()
    if loc:
        folium.Marker(location=loc, tooltip="現在地", icon=folium.Icon(color="blue", icon="location-arrow", prefix="fa")).add_to(m)
        folium.Circle(location=loc, radius=st.session_state.get("gps_radius_m", 300), color="blue", fill=False).add_to(m)
    
    if not done_ids:
        st.info("まだ足跡はありません。クエスト詳細で『このクエストに参加して足跡を残す』を押すと、ここに表示されます。")
        st_folium(m, width=900, height=520)
        return

    coords = []
    for idx, qid in enumerate(done_ids, start=1):
        q = get_quest(qid)
        coord = get_coord(q)
        if not coord: continue
        coords.append(coord)
        icon_html = f'<div style="font-size:28px; line-height:28px; filter: drop-shadow(0 1px 2px rgba(0,0,0,.35));">👣</div><div style="font-size:11px; background:white; border:1px solid #ddd; border-radius:10px; padding:0 5px; transform: translate(18px,-8px);">{idx}</div>'
        folium.Marker(location=coord, popup=folium.Popup(diary_popup_html(q), max_width=330), tooltip=f"{idx}. {q['linked_name']}", icon=folium.DivIcon(html=icon_html)).add_to(m)
    if len(coords) >= 2: folium.PolyLine(coords, weight=3, opacity=0.65).add_to(m)
    if coords: m.fit_bounds(coords)
    st_folium(m, width=900, height=560)


def quest_card(q: Dict, show_actions: bool = True, objectives: List[str] | None = None, stay: str = "まだ決めていない", season: str = "日程未定", ui_scope: str = "quest") -> None:
    completed = q["quest_id"] in st.session_state.completed
    favorite = q["quest_id"] in st.session_state.favorites

    with st.container(border=True):
        st.markdown(f"### {'★' if favorite else '☆'} {q['quest_name']}")
        st.caption(f"{'✅ 参加済み' if completed else '未参加'} / {q['quest_type']} / {q['area']} / {q['season']} / {q['connection_level']}")
        render_place_photo(q, compact=not show_actions)
        st.write(q["description"])
        st.markdown(f"**紐づく実在施設・イベント：** {q['linked_name']}")
        if q.get("period"): st.markdown(f"**開催・利用時期：** {q['period']}")
        st.markdown(f"**達成条件：** {q['condition']}")

        reward_char = get_character_for_quest(q)
        reward_owned = reward_char["character_id"] in st.session_state.unlocked_character_ids
        with st.expander("🎁 このクエストで仲間になるキャラクター", expanded=False):
            render_character_card(reward_char, locked=False, compact=True, show_enhance=False)
            if reward_owned: st.success("獲得済みです！（図鑑からリンゴをあげて育成できます）")
            else: st.info("このクエストをクリアすると獲得できます。")

        cols = st.columns(3)
        cols[0].link_button("公式ページ", q["official_url"], use_container_width=True)
        cols[1].link_button("Googleマップ", google_maps_search_url(q["linked_name"], q["area"]), use_container_width=True)
        if cols[2].button("お気に入り" if not favorite else "解除する", key=f"{ui_scope}_fav_{q['quest_id']}", use_container_width=True):
            if favorite: st.session_state.favorites.remove(q["quest_id"])
            else: st.session_state.favorites.add(q["quest_id"])
            st.rerun()

        if show_actions:
            with st.expander("📝 記録して足跡を残す（タップして展開）", expanded=False):
                note_key = f"{ui_scope}_note_{q['quest_id']}"
                st.session_state.notes[q["quest_id"]] = st.text_area("感想・学んだこと", value=st.session_state.notes.get(q["quest_id"], ""), key=note_key, height=80)
                
                uploaded = st.file_uploader("写真を記録する", type=["png", "jpg", "jpeg"], key=f"{ui_scope}_photo_{q['quest_id']}")
                if uploaded:
                    st.session_state.photos[q["quest_id"]] = uploaded.name
                    st.session_state.photo_data[q["quest_id"]] = uploaded.getvalue()
                    st.session_state.photo_mime[q["quest_id"]] = uploaded.type or "image/jpeg"
                    st.image(st.session_state.photo_data[q["quest_id"]], width=320)
                elif q["quest_id"] in st.session_state.photo_data:
                    st.image(st.session_state.photo_data[q["quest_id"]], width=320)

                sns_text = st.text_area("SNS投稿文", value=st.session_state.sns_texts.get(q["quest_id"], make_sns_text(q)), height=110, key=f"{ui_scope}_sns_{q['quest_id']}")
                st.session_state.sns_texts[q["quest_id"]] = sns_text
                
                # ------ SNSリンクボタン ------
                sns_cols = st.columns(3)
                sns_cols[0].link_button("Xで投稿画面を開く", x_share_url(sns_text, q["official_url"]), use_container_width=True)
                sns_cols[1].link_button("Instagramを開く", "https://www.instagram.com/", use_container_width=True)
                sns_cols[2].link_button("TikTokを開く", "https://www.tiktok.com/upload?lang=ja-JP", use_container_width=True)
                st.caption("Xは投稿文を入れた状態で開きます。Instagram・TikTokは投稿画面を開き、写真と文章は手動で投稿する前提です。")
                # ----------------------------------------

                st.session_state.x_post_urls[q["quest_id"]] = st.text_input("X投稿URL", value=st.session_state.x_post_urls.get(q["quest_id"], ""), key=f"{ui_scope}_xurl_{q['quest_id']}")
                
                gps_ok = render_gps_panel_for_quest(q)
                if st.button("足跡日記を更新する" if completed else "このクエストに参加して足跡を残す", key=f"{ui_scope}_complete_{q['quest_id']}", type="primary", use_container_width=True, disabled=not gps_ok):
                    already_completed = q["quest_id"] in st.session_state.completed
                    st.session_state.completed.add(q["quest_id"])
                    if q["quest_id"] not in st.session_state.completed_order: st.session_state.completed_order.append(q["quest_id"])
                    char = award_character_for_quest(q)
                    save_diary_record(q, st.session_state.notes[q["quest_id"]], st.session_state.sns_texts[q["quest_id"]], st.session_state.x_post_urls[q["quest_id"]])
                    
                    st.session_state.apples += 2
                    
                    if already_completed: st.success(f"日記を更新し、リンゴを2個獲得しました！")
                    else: 
                        st.success(f"達成！ {char['emoji']} {char['name']} が仲間になり、育成用の🍎リンゴを2個獲得しました！")
                        st.balloons()
                    st.rerun()

def progress_panel() -> None:
    total = len([q for q in QUESTS if q.get("quest_type") != "ストーリー"])
    done = len([qid for qid in st.session_state.completed if get_quest(qid).get("quest_type") != "ストーリー"])
    st.metric("参加した通常クエスト", f"{done} / {total}")
    st.progress(done / total if total else 0)


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="天草つながりクエスト", page_icon="🌊", layout="wide")
init_state()

st.title("🌊 天草つながりクエスト")
st.caption("実在する天草の施設・祭り・地域イベントだけをクエスト化するプロトタイプ")

with st.sidebar:
    today_str = date.today().isoformat()
    st.subheader("🎁 ログインボーナス")
    if st.session_state.last_login_date != today_str:
        st.info("今日のログインボーナスを受け取れます！")
        if st.button("🍎 リンゴを3個もらう", use_container_width=True):
            st.session_state.apples += 3
            st.session_state.last_login_date = today_str
            st.success("リンゴを3個獲得しました！図鑑タブでキャラクターの進化に使えます。")
            st.rerun()
    else:
        st.success(f"本日受取済み！ 所持リンゴ: {st.session_state.apples}個")
    st.divider()

    st.header("旅の条件")
    st.subheader("GPS設定")
    st.session_state.gps_required = st.checkbox("GPSで訪問判定する", value=st.session_state.get("gps_required", True))
    st.session_state.gps_radius_m = st.slider("達成判定の半径", 50, 1000, int(st.session_state.get("gps_radius_m", 300)), 50)

    if get_geolocation is None: st.warning("GPSライブラリ未インストール。")
    else:
        parsed = parse_geolocation_payload(get_geolocation())
        if parsed: set_current_location(parsed[0], parsed[1], parsed[2], "ブラウザGPS")

    manual = st.checkbox("緯度・経度を手入力して現在地にする", value=st.session_state.get("manual_location_enabled", False))
    if manual:
        mode = st.radio("設定方法", ["直接入力", "クエスト地点を使う"])
        if mode == "直接入力":
            c1, c2 = st.columns(2)
            mlat = c1.number_input("緯度", value=float(st.session_state.user_lat or 32.4569), format="%.6f")
            mlon = c2.number_input("経度", value=float(st.session_state.user_lon or 130.1926), format="%.6f")
            if st.button("この緯度経度にする"): set_current_location(mlat, mlon, 5, "手入力デモ"); st.rerun()
        else:
            demo_q = st.selectbox("OKにしたいクエスト", [q for q in QUESTS if get_coord(q)], format_func=lambda q: q['quest_name'])
            coord = get_coord(demo_q)
            if coord and st.button("この地点にする"): set_current_location(coord[0], coord[1], 5, f"デモ：{demo_q['linked_name']}"); st.rerun()

    loc = current_location()
    if loc: st.success(f"現在地: {loc[0]:.6f}, {loc[1]:.6f}")
    
    st.divider()
    multiselect_kwargs = {"label": "どんな体験をしたいですか？（1〜3つ）", "options": OBJECTIVES, "default": [], "max_selections": 3}
    if "accept_new_options" in inspect.signature(st.multiselect).parameters: multiselect_kwargs["accept_new_options"] = True
    selected_objectives = st.multiselect(**multiselect_kwargs)

    extra_obj = st.text_input("選択肢にない目的を入力") if "accept_new_options" not in inspect.signature(st.multiselect).parameters else ""
    objectives = parse_objective_text(extra_obj, selected_objectives, 3)
    search_keyword = st.text_input("🔍 キーワード検索", placeholder="例：イルカ、カフェ")

    stay = st.radio("滞在スタイル", STAY_OPTIONS, index=2)
    season = st.selectbox("行く時期", SEASONS, index=6)
    area = st.selectbox("エリア", AREAS, index=0)

    progress_panel()

story_tab, main_tab, map_tab, character_tab, gps_tab, list_tab, fav_tab, summary_tab, db_tab = st.tabs([
    "📜 ストーリー", "おすすめクエスト", "足跡マップ・日記", "キャラクター図鑑 & 育成", "GPS確認", "全クエスト一覧", "お気に入り", "旅のまとめ", "データ確認"
])

# -----------------------------
# ストーリーモードの表示処理
# -----------------------------
with story_tab:
    st.header("📖 ストーリーモード")
    st.markdown("### ＃1. 天草四郎ゆかりの地をめぐる～隠された６つの奇跡～")
    st.write("天草四郎の足跡をたどりながら、天草の歴史と自然をめぐる物語。クエストを順番にクリアして、特別なキャラクターを仲間にしよう！")
    
    progress = st.session_state.story_progress
    
    for i, sq in enumerate(STORY_QUESTS):
        is_unlocked = (i <= progress)
        is_cleared = (i < progress)
        
        status_icon = "✅ クリア" if is_cleared else ("🔓 挑戦可能" if is_unlocked else "🔒 未解放")
        
        with st.expander(f"第{i+1}章：{sq['quest_name']} （{status_icon}）", expanded=is_unlocked and not is_cleared):
            if not is_unlocked:
                st.warning("前のクエストをクリアすると解放され、詳細を見ることができます。")
                continue
            
            st.markdown(f"**目的地：** {sq['linked_name']} （{sq['area']}）")
            render_place_photo(sq, compact=True)
            st.write(sq['description'])
            st.markdown(f"**達成条件：** {sq['condition']}")
            
            if is_cleared:
                st.success("🎉 このクエストはクリア済みです！")
                st.markdown("#### 💡 クリア特典・プチ情報")
                st.info(sq['trivia'])
                
                st.markdown("**獲得したキャラクター：**")
                reward_char = get_character_stage(QUEST_CHARACTER_REWARDS[sq['quest_id']])
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    render_character_card(reward_char, locked=False, compact=True, show_enhance=False)
            else:
                st.markdown("#### クエストに挑戦する")
                gps_ok = render_gps_panel_for_quest(sq)
                if st.button("このクエストをクリアして次へ進む", key=f"story_btn_{sq['quest_id']}", type="primary", use_container_width=True, disabled=not gps_ok):
                    st.session_state.completed.add(sq["quest_id"])
                    st.session_state.story_progress += 1
                    char = award_character_for_quest(sq)
                    st.session_state.apples += 3
                    save_diary_record(sq, "ストーリーモードでクリアしました！", make_sns_text(sq), "")
                    st.success(f"クエストクリア！ {char['emoji']} {char['name']} が仲間になり、次のクエストが解放されました！")
                    st.balloons()
                    st.rerun()

with main_tab:
    st.subheader("あなたにおすすめの地域つながりクエスト")
    recommended = recommend_quests(objectives, stay, season, area, search_keyword)
    if not recommended: 
        st.warning("条件に合うクエストがありません。")
    else:
        st.write("おすすめのクエスト候補です。（クリア済みの通常クエストも継続して表示されます）")
        cols = st.columns(3)
        for i, q in enumerate(recommended[:12]):
            with cols[i % 3]:
                quest_card(q, show_actions=True, objectives=objectives, stay=stay, season=season, ui_scope=f"main_{i}_{q['quest_id']}")

with map_tab: render_footprint_map()

with character_tab: render_character_collection()

with gps_tab:
    st.subheader("📍 GPS確認・近くのクエスト")
    loc = current_location()
    if not loc: st.warning("現在地が未取得です。")
    else:
        st.success(f"現在地：{loc[0]:.6f}, {loc[1]:.6f}")
        radius = float(st.session_state.get("gps_radius_m", 300))
        st.dataframe(pd.DataFrame([{
            "クエスト": q["quest_name"], "距離": format_distance(distance_to_quest_m(q)),
            "半径内": "OK" if distance_to_quest_m(q) is not None and distance_to_quest_m(q) <= radius else "NG"
        } for q in QUESTS]), use_container_width=True)

with list_tab:
    st.subheader("全クエスト一覧")
    df = pd.DataFrame(QUESTS)
    df["tags_text"] = df["tags"].apply(lambda t: " / ".join(t))
    f_cols = st.columns(3)
    sel_tag = f_cols[0].selectbox("タグ", ["すべて"] + [x for x in OBJECTIVES if x != "特になし"])
    sel_area = f_cols[1].selectbox("エリア", ["すべて"] + sorted(df["area"].dropna().unique()))
    kw = f_cols[2].text_input("キーワード", key="list_kw")
    
    f_df = df.copy()
    if sel_tag != "すべて": f_df = f_df[f_df["tags"].apply(lambda t: sel_tag in t) | (f_df["quest_type"] == sel_tag)]
    if sel_area != "すべて": f_df = f_df[f_df["area"] == sel_area]
    if kw.strip():
        mask = False
        for c in ["quest_name", "linked_name", "description", "tags_text"]: mask |= f_df[c].astype(str).str.contains(kw.strip(), case=False)
        f_df = f_df[mask]
    
    if f_df.empty: st.warning("該当なし")
    else:
        st.dataframe(f_df[["quest_name", "linked_name", "area", "quest_type"]], use_container_width=True)
        sel_name = st.selectbox("詳細を見る", f_df["quest_name"].tolist())
        quest_card(next(q for q in QUESTS if q["quest_name"] == sel_name), show_actions=True, ui_scope="list")

with fav_tab:
    st.subheader("お気に入り")
    favs = [get_quest(q) for q in st.session_state.favorites]
    if not favs: st.info("お気に入りはありません。")
    else: 
        cols = st.columns(3)
        for i, q in enumerate(favs): 
            with cols[i % 3]:
                quest_card(q, ui_scope=f"fav_{i}")

with summary_tab:
    st.subheader("旅のまとめ")
    done = [get_quest(q) for q in st.session_state.completed]
    if not done: st.info("まだ参加記録がありません。")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("参加クエスト", len(done))
        c2.metric("仲間キャラ", len(st.session_state.unlocked_character_ids))
        c3.metric("所持リンゴ", st.session_state.apples)

with db_tab:
    st.subheader("データ確認・表紙写真の登録")
    st.write("各クエストの表紙写真（マスターイメージ）をここで簡単に登録・変更できます。")
    q_name = st.selectbox("写真を登録するクエストを選択", [q["quest_name"] for q in QUESTS])
    target_q = next(q for q in QUESTS if q["quest_name"] == q_name)
    existing_photo = place_photo_path(target_q["quest_id"])
    if existing_photo:
        st.image(str(existing_photo), caption="現在登録されている表紙写真", width=300)
    else:
        st.info("現在、写真は未登録（仮イラスト）です。")

    up_file = st.file_uploader(f"「{q_name}」の新しい写真をアップロード", type=["jpg", "jpeg", "png", "webp"])
    if up_file:
        save_place_photo(target_q["quest_id"], up_file)
        st.success("表紙写真を登録しました！おすすめ画面などに反映されます。")
        st.rerun()

    st.divider()
    st.download_button("クエストDBのCSVダウンロード", pd.DataFrame(QUESTS).to_csv(index=False).encode("utf-8-sig"), "db.csv", "text/csv")