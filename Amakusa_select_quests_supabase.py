# -*- coding: utf-8 -*-
"""
天草つながりクエスト / Amakusa Link Quest
Streamlit prototype
"""

from __future__ import annotations

import base64
import html
import json
import math
import re
import urllib.parse
from datetime import date, datetime, timezone
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

try:
    from supabase import create_client, Client
except ModuleNotFoundError:
    create_client = None
    Client = None


# =====================================================================
# ★ 絶対基準位置：黒い画面をどこで開いても「このファイルがある場所」を見る
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent

# セーブデータの保存先
SAVE_FILE = BASE_DIR / "save_data.json"


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
# リニューアル版 クエストデータベース (全16件)
# -----------------------------
QUESTS: List[Dict] = [
    {
        "quest_id": "spot_fukuzumi",
        "quest_name": "いけす料理ふくずみで海鮮を味わう",
        "linked_name": "いけす料理 ふくずみ",
        "quest_type": "食",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる",
        "tags": ["食", "自然・海"],
        "description": "いけす料理で新鮮な海鮮丼や海の幸を味わおう。",
        "condition": "店舗を訪れ、海鮮料理を食べ感想を記録する",
        "official_url": "https://kami-amakusa.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_hamankura",
        "quest_name": "浜崎鮮魚 浜んくらで豪快な魚料理を食べる",
        "linked_name": "浜崎鮮魚 浜んくら",
        "quest_type": "食",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる",
        "tags": ["食", "自然・海"],
        "description": "鮮魚店直営の食事処で、天草の新鮮な魚介をふんだんに使った料理を楽しもう。",
        "condition": "店舗を訪れ、料理の感想を記録する",
        "official_url": "https://kami-amakusa.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_ikoi",
        "quest_name": "いこい食堂で天草ちゃんぽんをすする",
        "linked_name": "いこい食堂",
        "quest_type": "食",
        "area": "苓北",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる",
        "tags": ["食", "地元の人"],
        "description": "地元で愛される「いこい食堂」で、具だく的外天草ちゃんぽんを味わおう。",
        "condition": "ちゃんぽんを食べ、味の感想を記録する",
        "official_url": "https://kankou.reihoku-kumamoto.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_lisola",
        "quest_name": "リゾラテラス天草で塩パンと絶景を楽しむ",
        "linked_name": "リゾラテラス天草",
        "quest_type": "食",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる・買う",
        "tags": ["食", "自然・海", "絶景", "癒し"],
        "description": "海辺のリゾート施設で、大人気の天草塩パンを買い、海を眺めながら過ごそう。",
        "condition": "塩パンを買い、景色の感想を記録する",
        "official_url": "https://www.seacruise.jp/lisolaterrace/",
        "status": "確認済み",
    },
    {
        "quest_id": "play_seadonut",
        "quest_name": "海中水族館シードーナツで海の生き物と遊ぶ",
        "linked_name": "海中水族館シードーナツ",
        "quest_type": "親子で遊ぶ",
        "area": "上天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "体験する",
        "tags": ["親子で遊ぶ", "自然・海", "ミュージアム"],
        "description": "海に浮かぶドーナツ型の水族館で、イルカや魚たちと間近でふれあおう。",
        "condition": "一番面白かった生き物を記録する",
        "official_url": "https://kami-amakusa.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "nat_oppai",
        "quest_name": "おっぱい岩の不思議な形を見る",
        "linked_name": "おっぱい岩",
        "quest_type": "自然・海",
        "area": "苓北",
        "season": "通年",
        "period": "干潮時",
        "stay_fit": "日帰り可",
        "connection_level": "知る",
        "tags": ["自然・海", "写真", "絶景"],
        "description": "干潮時にだけ姿を現すユニークな形の奇岩「おっぱい岩」を見に行こう。",
        "condition": "岩の形を確認し、写真を記録する",
        "official_url": "https://kankou.reihoku-kumamoto.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "photo_kuradake",
        "quest_name": "倉岳神社の天空の鳥居から絶景を撮る",
        "linked_name": "倉岳神社",
        "quest_type": "写真",
        "area": "天草",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "知る",
        "tags": ["写真", "絶景", "自然・海"],
        "description": "天草最高峰の山頂にある鳥居越しに、海に浮かぶパノラマ絶景を撮影しよう。",
        "condition": "山頂からの景色を記録する",
        "official_url": "https://www.t-island.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "photo_nishihira",
        "quest_name": "西平椿公園でラピュタの木に驚く",
        "linked_name": "西平椿公園（ラピュタの木）",
        "quest_type": "写真",
        "area": "天草西海岸・大江",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "知る",
        "tags": ["写真", "自然・海", "絶景"],
        "description": "岩を包み込むように根を張る巨大なアコウの木（通称ラピュタの木）の生命力を感じよう。",
        "condition": "木の迫力について感想を記録する",
        "official_url": "https://www.t-island.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "food_aosa",
        "quest_name": "大漁食堂あおさで新鮮な海鮮を堪能する",
        "linked_name": "大漁食堂 あおさ",
        "quest_type": "食",
        "area": "牛深",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる",
        "tags": ["食", "自然・海"],
        "description": "牛深港の「うしぶか海彩館」内にある食堂で、市場直送の海鮮料理を堪能しよう。",
        "condition": "海鮮料理を食べ、感想を記録する",
        "official_url": "https://kaisaikan.com/restaurant/",
        "status": "確認済み",
    },
    {
        "quest_id": "food_kura",
        "quest_name": "天草海鮮蔵で名物うにコロッケを食べる",
        "linked_name": "天草海鮮 蔵",
        "quest_type": "食",
        "area": "五和",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "食べる",
        "tags": ["食", "自然・海", "地元の人"],
        "description": "五和町にある海鮮蔵で、名物のうにコロッケや新鮮な海鮮バーベキューを楽しもう。",
        "condition": "料理を食べ、味の感想を記録する",
        "official_url": "https://kaisenkura.com/",
        "status": "確認済み",
    },
    {
        "quest_id": "event_ushibuka",
        "quest_name": "牛深ハイヤ祭りの熱気を感じる",
        "linked_name": "牛深ハイヤ祭り",
        "quest_type": "祭り・イベント",
        "area": "牛深",
        "season": "春",
        "period": "春",
        "stay_fit": "宿泊推奨",
        "connection_level": "参加する",
        "tags": ["祭り・イベント", "歴史・文化", "地元の人"],
        "description": "江戸時代から続く牛深ハイヤ祭りに参加し、軽快なハイヤ節と踊りの熱気を感じよう。",
        "condition": "祭りの様子や踊りの感想を記録する",
        "official_url": "https://www.t-island.jp/event/2400",
        "status": "確認済み",
    },
    {
        "quest_id": "event_hanashobu",
        "quest_name": "天草花しょうぶ祭りで満開の花を愛でる",
        "linked_name": "天草花しょうぶ祭り（西の久保公園）",
        "quest_type": "祭り・イベント",
        "area": "本渡",
        "season": "春",
        "period": "春〜初夏",
        "stay_fit": "日帰り可",
        "connection_level": "参加する",
        "tags": ["祭り・イベント", "自然・海", "写真"],
        "description": "西の久保公園で25万本の花菖蒲が咲き誇る絶景と、様々な催しを楽しもう。",
        "condition": "花の風景やイベントの感想を記録する",
        "official_url": "https://www.t-island.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "event_hondo",
        "quest_name": "天草ほんどハイヤ祭りで夜の熱気を体験する",
        "linked_name": "天草ほんどハイヤ祭り",
        "quest_type": "祭り・イベント",
        "area": "本渡",
        "season": "夏",
        "period": "夏",
        "stay_fit": "宿泊推奨",
        "connection_level": "参加する",
        "tags": ["祭り・イベント", "食", "地元の人"],
        "description": "本渡の夏の夜を彩るお祭りで、ハイヤ踊りや花火、マルシェを満喫しよう。",
        "condition": "お祭りの体験を記録する",
        "official_url": "https://www.t-island.jp/event/2349",
        "status": "確認済み",
    },
    {
        "quest_id": "play_oninoshiro",
        "quest_name": "鬼の城公園で展望塔から絶景を見る",
        "linked_name": "鬼の城公園",
        "quest_type": "親子で遊ぶ",
        "area": "五和",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "知る",
        "tags": ["親子で遊ぶ", "自然・海", "絶景"],
        "description": "鬼にまつわる伝説が残る公園で、高さ13mの展望塔に登り海峡を見渡そう。",
        "condition": "展望塔からの景色や公園の感想を記録する",
        "official_url": "https://www.t-island.jp/spot/58",
        "status": "確認済み",
    },
    {
        "quest_id": "craft_unshu",
        "quest_name": "雲舟窯で温かみのある天草陶磁器に出会う",
        "linked_name": "雲舟窯",
        "quest_type": "工芸・ものづくり",
        "area": "苓北",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "知る・買う",
        "tags": ["工芸・ものづくり", "写真"],
        "description": "苓北町の窯元「雲舟窯」を訪れ、使いやすさと温もりを感じる陶器の器を探そう。",
        "condition": "気になった器や窯元の雰囲気を記録する",
        "official_url": "https://amakusatoujiki.com/kamamoto/unsyuugama",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_dolphin",
        "quest_name": "イルカセンターで野生のイルカを知る",
        "linked_name": "道の駅 天草市イルカセンター",
        "quest_type": "自然・海",
        "area": "五和",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "体験する",
        "tags": ["自然・海", "親子で遊ぶ", "写真"],
        "description": "道の駅からイルカウォッチングに出発し、早崎海峡に住む野生のイルカと出会おう。",
        "condition": "イルカの姿や海風の感想を記録する",
        "official_url": "https://www.t-island.jp/spot/2837",
        "status": "確認済み",
    }
]

OBJECTIVES = [
    "祭り・イベント", "歴史・文化", "ミュージアム", "食", "自然・海",
    "工芸・ものづくり", "地元の人", "親子で遊ぶ", "写真", "癒し", "特になし"
]
STAY_OPTIONS = ["日帰り", "宿泊", "まだ決めていない"]
SEASONS = ["今日・今週", "春", "夏", "秋", "冬", "通年", "日程未定"]
AREAS = ["指定なし"] + sorted(list(set(q["area"] for q in QUESTS if q.get("quest_type") != "ストーリー")))

QUEST_COORDS: Dict[str, Tuple[float, float]] = {
    "spot_fukuzumi": (32.518682, 130.422624),
    "spot_hamankura": (32.522600, 130.425900),
    "spot_ikoi": (32.527600, 130.032100),
    "spot_lisola": (32.527691, 130.426280),
    "play_seadonut": (32.528347, 130.426949),
    "nat_oppai": (32.502000, 130.054300),
    "photo_kuradake": (32.407000, 130.336000),
    "photo_nishihira": (32.347558, 129.979153),
    "food_aosa": (32.193200, 130.024700),
    "food_kura": (32.554000, 130.158100),
    "event_ushibuka": (32.198000, 130.025400),
    "event_hanashobu": (32.469000, 130.187000),
    "event_hondo": (32.458700, 130.191900),
    "play_oninoshiro": (32.535000, 130.151100),
    "craft_unshu": (32.528500, 130.030500),
    "spot_dolphin": (32.558200, 130.169600),

    # ストーリーモード
    "story_1_shiro": (32.576031, 130.421133),
    "story_2_senganzan": (32.518100, 130.428500),
    "story_3_ueno": (32.532000, 130.415000),
    "story_4_kirishitan": (32.459954, 130.184100),
    "story_5_tomioka": (32.522700, 130.036700),
    "story_6_sakitsu": (32.315400, 130.026400),
}

PLACE_PHOTO_DIR = BASE_DIR / "quest_place_photos"
PLACE_PHOTO_EXTS = ["jpg", "jpeg", "png", "webp"]
CATEGORY_PLACEHOLDER = {
    "祭り・イベント": {"emoji": "🎆", "label": "地域の祭り・イベント"},
    "歴史・文化": {"emoji": "⛩️", "label": "天草の歴史文化"},
    "ミュージアム": {"emoji": "🏛️", "label": "歴史・文化施設"},
    "自然・海": {"emoji": "🌊", "label": "海と自然の体験"},
    "食": {"emoji": "🍽️", "label": "天草の食・物産"},
    "工芸・ものづくり": {"emoji": "🏺", "label": "工芸・ものづくり"},
    "地元の人": {"emoji": "🤝", "label": "地元の人との交流"},
    "親子で遊ぶ": {"emoji": "👨‍👩‍👧", "label": "親子で楽しむ体験"},
    "写真": {"emoji": "📷", "label": "絶景・写真スポット"},
    "癒し": {"emoji": "♨️", "label": "癒しのひととき"},
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
            <div style="font-size:12px; color:#60758a; margin-top:6px;">{html.escape(q.get('linked_name',''))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_place_photo(q: Dict, compact: bool = False) -> None:
    image_url = q.get("place_image_url", "")
    if image_url:
        st.image(image_url, caption=f"{q.get('linked_name','')}", use_container_width=True)
        return
    p = place_photo_path(q["quest_id"])
    if p:
        st.image(str(p), caption=f"{q.get('linked_name','')}", use_container_width=True)
    else:
        render_placeholder_place_card(q, compact=compact)


# ---------------------------------------------------------------------
# Character Evolution Database
# ---------------------------------------------------------------------
CHARACTER_IMAGE_DIR = BASE_DIR / "character_images"

CHARACTERS: Dict[str, Dict] = {
    # --- 通常キャラクター ---
    "shirasui": { "rarity": "レア", "series": "元気系", "stages": [{"name": "シラスイくん", "emoji": "🔥", "catch": "情熱的な精霊"}, {"name": "シラスイ将軍", "emoji": "☄️", "catch": "頼もしい将軍"}, {"name": "シラスイ大将軍", "emoji": "🌋", "catch": "炎の最終形態"}] },
    "hoshimi": { "rarity": "レア", "series": "夜・祭り", "stages": [{"name": "ほしみちゃん", "emoji": "✨", "catch": "キラキラの妖精"}, {"name": "ほしみ姫", "emoji": "🌟", "catch": "夜空を照らす姫"}, {"name": "ほしみ女神", "emoji": "💫", "catch": "夜を見守る女神"}] },
    "irukacchi": { "rarity": "ノーマル", "series": "海の仲間", "stages": [{"name": "イルカっち", "emoji": "🐬", "catch": "すばやい仲間"}, {"name": "イルカ王子", "emoji": "👑", "catch": "海の人気者"}, {"name": "イルカ大王", "emoji": "🐋", "catch": "海原を泳ぐ大王"}] },
    "kairun": { "rarity": "ノーマル", "series": "海の仲間", "stages": [{"name": "かいルン", "emoji": "🐚", "catch": "宝物を隠しているよ"}, {"name": "かい姫", "emoji": "🦪", "catch": "綺麗なお姫様"}, {"name": "かい女王", "emoji": "💎", "catch": "宝物を司る女王"}] },
    "amanya": { "rarity": "ノーマル", "series": "島の仲間", "stages": [{"name": "あまにゃん", "emoji": "🐾", "catch": "町歩きが好き"}, {"name": "あまにゃん将軍", "emoji": "😸", "catch": "町のボス"}, {"name": "あまにゃん大王", "emoji": "😼", "catch": "気まぐれ大王"}] },

    # --- ★ ストーリー限定キャラクター ★ ---
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
    "spot_fukuzumi": "kairun",
    "spot_hamankura": "kairun",
    "spot_ikoi": "amanya",
    "spot_lisola": "hoshimi",
    "play_seadonut": "irukacchi",
    "nat_oppai": "amanya",
    "photo_kuradake": "hoshimi",
    "photo_nishihira": "irukacchi",
    "food_aosa": "kairun",
    "food_kura": "kairun",
    "event_ushibuka": "shirasui",
    "event_hanashobu": "shirasui",
    "event_hondo": "shirasui",
    "play_oninoshiro": "amanya",
    "craft_unshu": "amanya",
    "spot_dolphin": "irukacchi",

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
    for ext in exts:
        p = CHARACTER_IMAGE_DIR / f"{lookup_id}.{ext}"
        if p.exists():
            return p

    alt_id = lookup_id.replace("①", "1").replace("②", "2").replace("③", "3")
    if alt_id != lookup_id:
        for ext in exts:
            p = CHARACTER_IMAGE_DIR / f"{alt_id}.{ext}"
            if p.exists():
                return p

    base_id = re.sub(r"[①②③123]$", "", lookup_id)
    if base_id != lookup_id:
        for ext in exts:
            p = CHARACTER_IMAGE_DIR / f"{base_id}.{ext}"
            if p.exists():
                return p

    return None

def get_character_stage(cid: str) -> dict:
    base_char = CHARACTERS.get(cid, CHARACTERS["amanya"])
    if base_char == CHARACTERS["amanya"]: cid = "amanya"
        
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
    cid = QUEST_CHARACTER_REWARDS.get(q.get("quest_id", ""))
    if not cid or cid not in CHARACTERS:
        tags = set(q.get("tags", []) + [q.get("quest_type", "")])
        cid = "amanya"
        if "自然・海" in tags: cid = "irukacchi"
        elif "食" in tags: cid = "kairun"
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
    save_user_data()
    return char


# -----------------------------
# データ永続化 (Save/Load) 機能
# -----------------------------
APP_STATE_QUEST_ID = "__app_state__"


def _safe_secret(name: str, default: str = "") -> str:
    """Streamlit Secretsの値を安全に取り出す。未設定でもアプリを落とさない。"""
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def supabase_is_configured() -> bool:
    """Supabase接続に必要な情報がそろっているか確認する。"""
    return (
        create_client is not None
        and bool(_safe_secret("SUPABASE_URL"))
        and bool(_safe_secret("SUPABASE_SERVICE_ROLE_KEY") or _safe_secret("SUPABASE_SECRET_KEY"))
    )


@st.cache_resource
def get_supabase_client() -> Optional["Client"]:
    """Supabaseクライアントを作成する。Secrets未設定時はNoneを返す。"""
    if create_client is None:
        return None
    url = _safe_secret("SUPABASE_URL")
    key = _safe_secret("SUPABASE_SERVICE_ROLE_KEY") or _safe_secret("SUPABASE_SECRET_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def _get_query_param(name: str) -> str:
    """URLの ?pid=... から参加者IDを取得する。"""
    try:
        value = st.query_params.get(name, "")
        if isinstance(value, list):
            return str(value[0]).strip() if value else ""
        return str(value).strip()
    except Exception:
        return ""


def render_participant_setup() -> None:
    """
    実証実験用の参加者IDをセットする。
    URL例：https://xxxx.streamlit.app/?pid=AMK-7F3Q
    """
    query_pid = _get_query_param("pid")
    if query_pid and not st.session_state.get("participant_id"):
        st.session_state.participant_id = query_pid

    with st.expander("🧪 実証実験の参加者ID", expanded=not bool(st.session_state.get("participant_id"))):
        st.caption("配布された参加者IDを入力してください。同じIDで開くと、タブを閉じた後もSupabaseから進捗を復元できます。")
        pid = st.text_input(
            "参加者ID",
            value=st.session_state.get("participant_id", ""),
            placeholder="例：AMK-7F3Q",
            key="participant_id_input",
        ).strip()

        if st.button("この参加者IDで開始する", use_container_width=True):
            if not pid:
                st.warning("参加者IDを入力してください。")
            else:
                old_pid = st.session_state.get("participant_id")
                st.session_state.participant_id = pid
                if old_pid != pid:
                    st.session_state.data_loaded = False
                    st.session_state.loaded_participant_id = None
                st.rerun()

        if st.session_state.get("participant_id"):
            st.success(f"現在の参加者ID：{st.session_state.participant_id}")
            if supabase_is_configured():
                st.caption("保存先：Supabase")
            else:
                st.warning("Supabase Secretsが未設定です。今はローカル保存になります。実証実験前に必ず設定してください。")
        else:
            st.info("参加者IDが未設定です。実証実験では必ず参加者IDを入力してから始めてください。")

    if not st.session_state.get("participant_id"):
        st.stop()

    ensure_participant(st.session_state.participant_id)

    # 参加者IDが変わった場合は、その人のデータを再ロードする。
    if st.session_state.get("loaded_participant_id") != st.session_state.participant_id:
        st.session_state.data_loaded = False


def ensure_participant(pid: str) -> None:
    """participantsテーブルに参加者IDを作成・更新する。Supabase未設定時は何もしない。"""
    if not supabase_is_configured():
        return
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return
        supabase.table("participants").upsert({
            "participant_id": pid,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        st.warning(f"Supabaseの参加者登録に失敗しました。ローカル保存に切り替えます: {e}")


def _local_state_dict(include_photo_binary: bool = True) -> Dict:
    """現在の状態を辞書化する。ローカル保存・Supabase保存の共通材料。"""
    data = {
        "completed": list(st.session_state.completed),
        "completed_order": st.session_state.completed_order,
        "completed_at": st.session_state.get("completed_at", {}),
        "favorites": list(st.session_state.favorites),
        "notes": st.session_state.notes,
        "sns_texts": st.session_state.sns_texts,
        "x_post_urls": st.session_state.x_post_urls,
        "diary": st.session_state.diary,
        "unlocked_character_ids": list(st.session_state.unlocked_character_ids),
        "unlocked_character_order": st.session_state.unlocked_character_order,
        "quest_character_rewards": st.session_state.quest_character_rewards,
        "apples": st.session_state.apples,
        "character_apples": st.session_state.character_apples,
        "last_login_date": st.session_state.last_login_date,
        "story_progress": st.session_state.story_progress,
        "photos": st.session_state.photos,
        "photo_mime": st.session_state.photo_mime,
    }
    # Supabaseにはプライバシーと容量の観点から画像本体は保存しない。
    # ローカル検証時だけ画像バイナリをJSONに含める。
    if include_photo_binary:
        data["photo_data"] = {
            k: base64.b64encode(v).decode("utf-8")
            for k, v in st.session_state.photo_data.items()
        }
    return data


def _apply_state_dict(data: Dict, include_photo_binary: bool = True) -> None:
    """辞書データをsession_stateに反映する。"""
    st.session_state.completed = set(data.get("completed", []))
    st.session_state.completed_order = data.get("completed_order", [])
    st.session_state.completed_at = data.get("completed_at", {})
    st.session_state.favorites = set(data.get("favorites", []))
    st.session_state.notes = data.get("notes", {})
    st.session_state.sns_texts = data.get("sns_texts", {})
    st.session_state.x_post_urls = data.get("x_post_urls", {})
    st.session_state.diary = data.get("diary", {})
    st.session_state.unlocked_character_ids = set(data.get("unlocked_character_ids", []))
    st.session_state.unlocked_character_order = data.get("unlocked_character_order", [])
    st.session_state.quest_character_rewards = data.get("quest_character_rewards", {})
    st.session_state.apples = data.get("apples", 0)
    st.session_state.character_apples = data.get("character_apples", {})
    st.session_state.last_login_date = data.get("last_login_date", None)
    st.session_state.story_progress = data.get("story_progress", 0)
    st.session_state.photos = data.get("photos", {})
    st.session_state.photo_mime = data.get("photo_mime", {})

    if include_photo_binary:
        photo_data = {}
        for k, v in data.get("photo_data", {}).items():
            try:
                photo_data[k] = base64.b64decode(v)
            except Exception:
                pass
        st.session_state.photo_data = photo_data


def save_user_data():
    """
    データ保存の入口。
    Supabase設定がある場合はSupabaseへ保存し、未設定・失敗時は従来のsave_data.jsonへ保存する。
    """
    if supabase_is_configured() and st.session_state.get("participant_id"):
        try:
            save_user_data_supabase()
            return
        except Exception as e:
            st.warning(f"Supabase保存に失敗しました。ローカル保存に切り替えます: {e}")

    save_user_data_local()


def save_user_data_local():
    """セッションステートの内容をローカルのJSONファイルに保存する。"""
    data = _local_state_dict(include_photo_binary=True)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_user_data_supabase():
    """
    参加者ごとのデータをSupabaseに保存する。
    画像そのものは保存せず、photo_uploaded=True/Falseだけ保存する。
    """
    pid = st.session_state.get("participant_id", "").strip()
    if not pid:
        return

    supabase = get_supabase_client()
    if supabase is None:
        save_user_data_local()
        return

    ensure_participant(pid)

    # アプリ全体の状態は、quest_progressの特別行にJSON文字列として保存する。
    app_state = _local_state_dict(include_photo_binary=False)
    supabase.table("quest_progress").upsert({
        "participant_id": pid,
        "quest_id": APP_STATE_QUEST_ID,
        "completed": False,
        "favorite": False,
        "note": json.dumps(app_state, ensure_ascii=False),
        "photo_uploaded": False,
        "apples": int(st.session_state.get("apples", 0)),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="participant_id,quest_id").execute()

    all_quests = list(QUESTS) + list(STORY_QUESTS)
    rows = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for q in all_quests:
        qid = q.get("quest_id")
        if not qid:
            continue
        completed = qid in st.session_state.completed
        if completed and not st.session_state.completed_at.get(qid):
            st.session_state.completed_at[qid] = now_iso

        rows.append({
            "participant_id": pid,
            "quest_id": qid,
            "completed": completed,
            "completed_at": st.session_state.completed_at.get(qid) if completed else None,
            "favorite": qid in st.session_state.favorites,
            "note": st.session_state.notes.get(qid, ""),
            "sns_text": st.session_state.sns_texts.get(qid, ""),
            "x_post_url": st.session_state.x_post_urls.get(qid, ""),
            "photo_uploaded": bool(st.session_state.photo_data.get(qid) or st.session_state.photos.get(qid)),
            "photo_url": "",
            "user_lat": st.session_state.get("user_lat"),
            "user_lon": st.session_state.get("user_lon"),
            "gps_accuracy": st.session_state.get("user_accuracy"),
            "gps_distance_m": distance_to_quest_m(q),
            "character_id": st.session_state.quest_character_rewards.get(qid, ""),
            "apples": int(st.session_state.get("apples", 0)),
            "updated_at": now_iso,
        })

    if rows:
        supabase.table("quest_progress").upsert(
            rows,
            on_conflict="participant_id,quest_id"
        ).execute()


def load_user_data():
    """
    データ読み込みの入口。
    Supabase設定がある場合は参加者IDごとに読み込み、未設定時は従来のsave_data.jsonを読む。
    """
    if supabase_is_configured() and st.session_state.get("participant_id"):
        try:
            load_user_data_supabase(st.session_state.participant_id)
            return
        except Exception as e:
            st.warning(f"Supabase読み込みに失敗しました。ローカル保存を確認します: {e}")

    load_user_data_local()


def load_user_data_local():
    """JSONファイルからセーブデータを読み込む。"""
    if not SAVE_FILE.exists():
        return
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _apply_state_dict(data, include_photo_binary=True)
    except Exception as e:
        st.error(f"セーブデータの読み込みに失敗しました: {e}")


def load_user_data_supabase(pid: str):
    """Supabaseから参加者IDごとの進捗を読み込む。"""
    supabase = get_supabase_client()
    if supabase is None:
        return

    response = (
        supabase
        .table("quest_progress")
        .select("*")
        .eq("participant_id", pid)
        .execute()
    )
    rows = response.data or []

    # まず特別行のアプリ状態を読み込む。
    app_state_row = next((r for r in rows if r.get("quest_id") == APP_STATE_QUEST_ID), None)
    if app_state_row and app_state_row.get("note"):
        try:
            app_state = json.loads(app_state_row.get("note") or "{}")
            _apply_state_dict(app_state, include_photo_binary=False)
        except Exception:
            pass

    # クエストごとの状態を上書き・補完する。
    for row in rows:
        qid = row.get("quest_id")
        if not qid or qid == APP_STATE_QUEST_ID:
            continue

        if row.get("completed"):
            st.session_state.completed.add(qid)
            if qid not in st.session_state.completed_order:
                st.session_state.completed_order.append(qid)
            if row.get("completed_at"):
                st.session_state.completed_at[qid] = row.get("completed_at")

        if row.get("favorite"):
            st.session_state.favorites.add(qid)

        if row.get("note") is not None:
            st.session_state.notes[qid] = row.get("note") or ""
        if row.get("sns_text") is not None:
            st.session_state.sns_texts[qid] = row.get("sns_text") or ""
        if row.get("x_post_url") is not None:
            st.session_state.x_post_urls[qid] = row.get("x_post_url") or ""
        if row.get("character_id"):
            st.session_state.quest_character_rewards[qid] = row.get("character_id")
        if row.get("photo_uploaded"):
            # 画像本体は保存しないが、写真添付済みの事実は復元する。
            st.session_state.photos[qid] = st.session_state.photos.get(qid) or "写真添付済み"

    st.session_state.loaded_participant_id = pid


def init_state() -> None:
    defaults = {
        "completed": set(),
        "completed_order": [],
        "completed_at": {},
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
        "photo_capture_open": set(),
        "participant_id": "",
        "data_loaded": False,
        "loaded_participant_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    valid_qids = {q.get("quest_id") for q in QUESTS if q.get("quest_id")}
    # ストーリークエストのIDも検証に追加
    valid_story_qids = {q.get("quest_id") for q in STORY_QUESTS if q.get("quest_id")}
    all_valid_qids = valid_qids.union(valid_story_qids)

    st.session_state.completed = {qid for qid in st.session_state.completed if qid in all_valid_qids}
    st.session_state.completed_order = [qid for qid in st.session_state.completed_order if qid in all_valid_qids]
    st.session_state.favorites = {qid for qid in st.session_state.favorites if qid in all_valid_qids}


def render_character_card(char: Dict, locked: bool = False, compact: bool = False, show_enhance: bool = False) -> None:
    lookup_id = char.get("img_id", char.get("character_id", ""))
    img = character_image_path(lookup_id)
    name = "？？？" if locked else char.get("name", "")
    rarity = char.get("rarity", "")
    series = char.get("series", "")
    catch = "まだ出会っていない仲間です。対応するクエストをクリアすると解放されます。" if locked else char.get("catch", "")
    emoji = "❓" if locked else char.get("emoji", "✨")

    with st.container(border=True):
        if img and not locked:
            st.image(str(img), use_container_width=True)
        else:
            height = 110 if compact else 150
            font_size = 46 if compact else 62
            st.markdown(
                f"""
                <div style="height:{height}px; border-radius:18px; background:linear-gradient(135deg,#edf6ff,#fff7fb); border:1px solid #dbeafe; display:flex; align-items:center; justify-content:center; font-size:{font_size}px; filter:{'grayscale(1) opacity(0.5)' if locked else 'none'}; margin-bottom:1rem;">
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
                    save_user_data() # ★ 自動保存
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


def get_quest(quest_id: str) -> Dict:
    all_quests = QUESTS + STORY_QUESTS
    return next((q for q in all_quests if q.get("quest_id") == quest_id), {})


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
    "親子で遊ぶ": ["遊ぶ", "子供", "家族", "体験", "水族館", "アクティビティ"],
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

def objective_match(q: Dict, objectives: List[str]) -> int:
    if not objectives or "特になし" in objectives:
        return 1

    tags = [str(t) for t in q.get("tags", [])] + [str(q.get("quest_type", ""))]
    tag_texts = [normalize_text_for_match(t) for t in tags if str(t).strip()]
    q_text = normalize_text_for_match(" ".join([
        q.get("quest_name", ""), q.get("linked_name", ""), q.get("quest_type", ""),
        q.get("area", ""), q.get("season", ""), q.get("description", ""), " ".join(q.get("tags", [])),
    ]))

    expanded_terms = expand_objective_terms(objectives)
    score = 0
    for term in expanded_terms:
        term_norm = normalize_text_for_match(term)
        if not term_norm:
            continue

        if term_norm in tag_texts:
            score += 5
        elif any(term_norm in tag_text or tag_text in term_norm for tag_text in tag_texts):
            score += 3
        elif term_norm in q_text:
            score += 2

    return score

def stay_match_score(q: Dict, stay: str) -> int:
    fit = q.get("stay_fit", "")
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
        if area != "指定なし" and q.get("area") != area: continue
        if not season_match(q.get("season", ""), season): continue
        if keyword:
            kw = keyword.strip().lower()
            search_target = f"{q.get('quest_name','')} {q.get('linked_name','')} {q.get('description','')} {' '.join(q.get('tags',[]))}".lower()
            if kw not in search_target: continue
        
        obj_score = objective_match(q, objectives)
        stay_score = stay_match_score(q, stay)
        if objectives and "特になし" not in objectives and obj_score == 0: continue
        if stay == "日帰り" and q.get("stay_fit") == "宿泊推奨": stay_score = 0
        
        season_bonus = 20 if q.get("season") == current_season else 0
        rows.append((obj_score * 10 + stay_score * 3 + season_bonus + (1 if q.get("status") == "確認済み" else 0), q))
    
    rows.sort(key=lambda x: x[0], reverse=True)
    return [q for _, q in rows]

def make_sns_text(q: Dict) -> str:
    return f"天草つながりクエストで『{q.get('linked_name','')}』に参加しました。\n{q.get('description','')}\n#天草つながりクエスト #天草観光 #天草旅"

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
    return QUEST_COORDS.get(q.get("quest_id", ""))

def distance_to_quest_m(q: Dict) -> Optional[float]:
    loc, coord = current_location(), get_coord(q)
    return haversine_m(loc[0], loc[1], coord[0], coord[1]) if loc and coord else None

def format_distance(d: Optional[float]) -> str:
    if d is None: return "距離不明"
    return f"約{d:.0f}m" if d < 1000 else f"約{d/1000:.1f}km"

def render_gps_panel_for_quest(q: Dict) -> bool:
    if not st.session_state.get("gps_required", True):
        st.info("デモ用にGPS判定をOFFにしています。")
        return True
    coord = get_coord(q)
    if coord is None:
        st.warning("座標未登録のためGPS判定できません。")
        return False
    loc = current_location()
    if loc is None:
        st.warning("現在地が未取得です。画面上部の『⚙️ GPS・現在地設定』から設定してください。")
        return False
    d = distance_to_quest_m(q)
    radius = float(st.session_state.get("gps_radius_m", 300))
    if d is not None and d <= radius:
        st.success(f"GPS判定OK：目的地から{format_distance(d)}以内です。")
        return True
    st.error(f"GPS判定NG：目的地から{format_distance(d)}離れています。")
    return False

def store_quest_photo(qid: str, uploaded_file) -> None:
    if not qid or uploaded_file is None:
        return
    st.session_state.photos[qid] = getattr(uploaded_file, "name", "camera_photo.jpg") or "camera_photo.jpg"
    st.session_state.photo_data[qid] = uploaded_file.getvalue()
    st.session_state.photo_mime[qid] = getattr(uploaded_file, "type", None) or "image/jpeg"
    save_user_data() # ★ 写真を登録したら保存


def has_clear_photo(q: Dict) -> bool:
    qid = q.get("quest_id", "")
    return bool(qid and (st.session_state.photo_data.get(qid) or st.session_state.photos.get(qid)))


def render_photo_clear_panel(q: Dict, ui_scope: str = "quest") -> bool:
    qid = q.get("quest_id", "")
    if not qid:
        return False

    st.markdown("#### 📸 写真によるクリア確認")
    st.caption("クリア条件：GPS判定OKに加えて、現地で撮った写真、または写真フォルダから選んだ写真の添付が必要です。")

    if has_clear_photo(q):
        st.success("写真確認OK：クリア用写真が添付されています。")
        if st.session_state.photo_data.get(qid):
            st.image(st.session_state.photo_data[qid], caption="クリア用写真", width=320)
        else:
            st.info("前回の写真添付記録を復元しました。プライバシー保護のため、画像本体はSupabaseには保存していません。")
        if st.button("写真を撮り直す・選び直す", key=f"{ui_scope}_reset_clear_photo_{qid}", use_container_width=True):
            st.session_state.photos.pop(qid, None)
            st.session_state.photo_data.pop(qid, None)
            st.session_state.photo_mime.pop(qid, None)
            st.session_state.photo_capture_open.add(qid)
            save_user_data()
            st.rerun()
        return True

    st.warning("写真確認がまだです。写真を添付すると、クリアボタンを押せるようになります。")

    if st.button("📸 クリア用写真を登録する", key=f"{ui_scope}_open_clear_photo_{qid}", use_container_width=True):
        st.session_state.photo_capture_open.add(qid)
        st.rerun()

    if qid in st.session_state.photo_capture_open:
        method = st.radio(
            "写真の登録方法を選んでください",
            ["カメラで撮影する", "写真フォルダからアップロードする"],
            key=f"{ui_scope}_photo_method_{qid}",
            horizontal=True,
        )

        if method == "カメラで撮影する":
            captured = st.camera_input("カメラを起動して撮影する", key=f"{ui_scope}_camera_{qid}")
            if captured:
                store_quest_photo(qid, captured)
                st.session_state.photo_capture_open.discard(qid)
                st.success("写真を登録しました。クリアボタンを押せるようになりました。")
                st.rerun()
        else:
            uploaded = st.file_uploader(
                "写真フォルダから選択する",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"{ui_scope}_clear_photo_upload_{qid}",
            )
            if uploaded:
                store_quest_photo(qid, uploaded)
                st.session_state.photo_capture_open.discard(qid)
                st.success("写真を登録しました。クリアボタンを押せるようになりました。")
                st.rerun()

    st.info("GPS判定と写真添付の両方がそろうと、クリアボタンが有効になります。")
    return False


def image_data_url(qid: str) -> str:
    data = st.session_state.photo_data.get(qid)
    return f"data:{st.session_state.photo_mime.get(qid, 'image/jpeg')};base64,{base64.b64encode(data).decode('utf-8')}" if data else ""

def save_diary_record(q: Dict, note: str, sns_text: str, x_url: str) -> None:
    qid = q.get("quest_id")
    if not qid: return
    char = get_character_for_quest(q)
    st.session_state.diary[qid] = {
        "date": date.today().isoformat(), "quest_name": q.get("quest_name", ""), "linked_name": q.get("linked_name", ""),
        "area": q.get("area", ""), "quest_type": q.get("quest_type", ""), "note": note, "sns_text": sns_text,
        "x_post_url": x_url, "photo_name": st.session_state.photos.get(qid, ""),
        "user_lat": st.session_state.get("user_lat"), "user_lon": st.session_state.get("user_lon"),
        "gps_accuracy": st.session_state.get("user_accuracy"), "gps_distance_m": distance_to_quest_m(q),
        "character_id": char.get("character_id", ""), "character_name": char.get("name", ""),
    }

def diary_popup_html(q: Dict) -> str:
    qid = q.get("quest_id")
    if not qid: return ""
    record = st.session_state.diary.get(qid, {})
    note = html.escape(record.get("note", "感想はまだ記録されていません。"))
    sns_text = html.escape(record.get("sns_text", make_sns_text(q))).replace("\n", "<br>")
    char = get_character_for_quest(q)
    char_name, char_emoji = html.escape(record.get("character_name", char.get("name", ""))), html.escape(char.get("emoji", "✨"))
    char_html = f'<p style="font-size:13px; background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:8px;"><b>仲間になったキャラ</b><br>{char_emoji} {char_name}</p>'
    img_url = image_data_url(qid)
    img_html = f'<img src="{img_url}" style="width:260px; max-height:190px; object-fit:cover; border-radius:10px; margin:8px 0;" />' if img_url else '<p style="color:#777;">写真は未登録です。</p>'
    return f"""
    <div style="font-family: sans-serif; width: 285px;">
      <h4 style="margin-bottom:4px;">👣 {html.escape(q.get('linked_name',''))}</h4>
      <div style="font-size:12px; color:#555; margin-bottom:6px;">{html.escape(record.get('date', date.today().isoformat()))} / {html.escape(q.get('area',''))}</div>
      {img_html}<p style="font-size:13px;"><b>日記</b><br>{note}</p>{char_html}
    </div>
    """

def render_footprint_map() -> None:
    st.subheader("👣 足跡マップ・旅の日記")
    if folium is None or st_folium is None:
        st.error("地図を表示するには folium と streamlit-folium が必要です。")
        return
    done_ids = [qid for qid in st.session_state.completed_order if qid in st.session_state.completed and get_quest(qid).get("quest_id")]
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
        if not q.get("quest_id"): continue
        coord = get_coord(q)
        if not coord: continue
        coords.append(coord)
        icon_html = f'<div style="font-size:28px; line-height:28px; filter: drop-shadow(0 1px 2px rgba(0,0,0,.35));">👣</div><div style="font-size:11px; background:white; border:1px solid #ddd; border-radius:10px; padding:0 5px; transform: translate(18px,-8px);">{idx}</div>'
        folium.Marker(location=coord, popup=folium.Popup(diary_popup_html(q), max_width=330), tooltip=f"{idx}. {q.get('linked_name','')}", icon=folium.DivIcon(html=icon_html)).add_to(m)
    if len(coords) >= 2: folium.PolyLine(coords, weight=3, opacity=0.65).add_to(m)
    if coords: m.fit_bounds(coords)
    st_folium(m, width=900, height=560)


def quest_map_popup_html(q: Dict, include_distance: bool = True) -> str:
    qid = q.get("quest_id", "")
    dist = format_distance(distance_to_quest_m(q)) if include_distance else "距離不明"
    tags = " / ".join([str(t) for t in q.get("tags", [])])
    official_url = html.escape(q.get("official_url", ""), quote=True)
    maps_url = html.escape(google_maps_search_url(q.get("linked_name", ""), q.get("area", "")), quote=True)
    description = html.escape(q.get("description", ""))
    condition = html.escape(q.get("condition", ""))
    return f"""
    <div style="font-family:sans-serif; width:300px; line-height:1.45;">
      <h4 style="margin:0 0 6px 0;">📍 {html.escape(q.get('quest_name',''))}</h4>
      <div style="font-size:12px; color:#555; margin-bottom:6px;">
        {html.escape(q.get('linked_name',''))}<br>
        {html.escape(q.get('area',''))} / {html.escape(q.get('quest_type',''))} / {html.escape(q.get('season',''))}
      </div>
      <p style="font-size:13px; margin:6px 0;"><b>内容</b><br>{description}</p>
      <p style="font-size:13px; margin:6px 0;"><b>達成条件</b><br>{condition}</p>
      <p style="font-size:12px; color:#555; margin:6px 0;"><b>タグ</b><br>{html.escape(tags)}</p>
      <p style="font-size:12px; color:#2563eb; margin:6px 0;"><b>現在地からの距離</b>：{html.escape(dist)}</p>
      <div style="margin-top:8px; display:flex; gap:8px;">
        <a href="{official_url}" target="_blank" style="font-size:12px;">公式ページ</a>
        <a href="{maps_url}" target="_blank" style="font-size:12px;">Googleマップ</a>
      </div>
    </div>
    """

def render_quest_map() -> None:
    st.subheader("🗺️ クエストマップ")
    st.write("天草のマップ上に、各クエストのピンを表示します。ピンを押すとクエスト内容・達成条件・距離を確認できます。")

    if folium is None or st_folium is None:
        st.error("地図を表示するには folium と streamlit-folium が必要です。requirements.txt に追加してください。")
        return

    all_quests = list(QUESTS) + list(STORY_QUESTS)
    quests_with_coords = [q for q in all_quests if get_coord(q)]
    quests_without_coords = [q for q in all_quests if not get_coord(q)]

    loc = current_location()
    if loc:
        st.success(f"現在地：{loc[0]:.6f}, {loc[1]:.6f}")
    else:
        st.info("現在地は未取得です。上部の『⚙️ GPS・デモ用現在地設定』から取得・手入力できます。現在地なしでもクエストピンは表示されます。")

    c1, c2, c3 = st.columns(3)
    c1.metric("表示中のクエスト", len(quests_with_coords))
    c2.metric("座標未登録", len(quests_without_coords))
    c3.metric("参加済み", len([q for q in QUESTS if q.get("quest_id") in st.session_state.completed]))

    m = folium.Map(location=[32.43, 130.20], zoom_start=9, tiles="OpenStreetMap")

    if loc:
        folium.Marker(
            location=loc,
            tooltip="現在地",
            popup=folium.Popup("現在地", max_width=180),
            icon=folium.Icon(color="blue", icon="location-arrow", prefix="fa"),
        ).add_to(m)
        folium.Circle(
            location=loc,
            radius=st.session_state.get("gps_radius_m", 300),
            color="blue",
            fill=False,
        ).add_to(m)

    type_color = {
        "ストーリー": "purple",
        "祭り・イベント": "red",
        "歴史・文化": "darkred",
        "ミュージアム": "cadetblue",
        "食": "orange",
        "自然・海": "green",
        "工芸・ものづくり": "darkblue",
        "地元の人": "lightred",
        "親子で遊ぶ": "lightgreen",
        "写真": "pink",
        "癒し": "lightblue",
    }

    bounds = []
    for q in quests_with_coords:
        coord = get_coord(q)
        if not coord:
            continue
        bounds.append(coord)
        qtype = q.get("quest_type", "")
        qid = q.get("quest_id", "")
        completed = qid in st.session_state.completed
        icon_color = "gray" if completed else type_color.get(qtype, "darkgreen")
        tooltip = f"{'✅ ' if completed else ''}{q.get('quest_name','')}"
        folium.Marker(
            location=coord,
            tooltip=tooltip,
            popup=folium.Popup(quest_map_popup_html(q), max_width=340),
            icon=folium.Icon(color=icon_color, icon="flag" if completed else "map-marker", prefix="fa"),
        ).add_to(m)

    if bounds:
        try:
            m.fit_bounds(bounds)
        except Exception:
            pass

    st_folium(m, width=1000, height=620)

    if quests_without_coords:
        with st.expander("座標未登録のクエストを確認する", expanded=False):
            st.warning("以下のクエストは座標が未登録のため、地図に表示できません。")
            st.dataframe(pd.DataFrame([{
                "quest_id": q.get("quest_id", ""),
                "クエスト名": q.get("quest_name", ""),
                "施設・イベント": q.get("linked_name", ""),
                "エリア": q.get("area", ""),
            } for q in quests_without_coords]), use_container_width=True)


def quest_card(q: Dict, show_actions: bool = True, ui_scope: str = "quest") -> None:
    if not q.get("quest_id"): return
    completed = q["quest_id"] in st.session_state.completed
    favorite = q["quest_id"] in st.session_state.favorites

    with st.container(border=True):
        st.markdown(f"### {'★' if favorite else '☆'} {q.get('quest_name','')}")
        st.caption(f"{'✅ 参加済み' if completed else '未参加'} / {q.get('quest_type','')} / {q.get('area','')} / {q.get('season','')} / {q.get('connection_level','')}")
        render_place_photo(q, compact=not show_actions)
        st.write(q.get("description",""))
        st.markdown(f"**紐づく実在施設・イベント：** {q.get('linked_name','')}")
        if q.get("period"): st.markdown(f"**開催・利用時期：** {q['period']}")
        st.markdown(f"**達成条件：** {q.get('condition','')}")

        if show_actions:
            gps_ok = render_gps_panel_for_quest(q)
            photo_ok = render_photo_clear_panel(q, ui_scope=ui_scope)
            btn_label = "足跡日記を更新する" if completed else "このクエストに参加して足跡を残す"
            can_clear = gps_ok and photo_ok
            if not can_clear:
                st.caption("クリアボタンは、GPS判定OK ＋ 写真添付OK の両方がそろうと押せます。")
            if st.button(btn_label, key=f"{ui_scope}_complete_{q['quest_id']}", type="primary", use_container_width=True, disabled=not can_clear):
                already_completed = q["quest_id"] in st.session_state.completed
                st.session_state.completed.add(q["quest_id"])
                if q["quest_id"] not in st.session_state.completed_at:
                    st.session_state.completed_at[q["quest_id"]] = datetime.now(timezone.utc).isoformat()
                if q["quest_id"] not in st.session_state.completed_order: st.session_state.completed_order.append(q["quest_id"])
                
                char = award_character_for_quest(q)
                save_diary_record(q, st.session_state.notes.get(q["quest_id"], ""), st.session_state.sns_texts.get(q["quest_id"], make_sns_text(q)), st.session_state.x_post_urls.get(q["quest_id"], ""))
                
                st.session_state.apples += 2
                save_user_data() # ★ 自動保存
                
                if already_completed: 
                    st.success(f"日記を更新し、リンゴを2個獲得しました！")
                    st.snow()
                else: 
                    st.success(f"達成！ {char.get('emoji','')} {char.get('name','')} が仲間になり、育成用の🍎リンゴを2個獲得しました！")
                    st.balloons()
                st.rerun()

        reward_char = get_character_for_quest(q)
        reward_owned = reward_char.get("character_id") in st.session_state.unlocked_character_ids
        with st.expander("🎁 このクエストで仲間になるキャラクター", expanded=False):
            render_character_card(reward_char, locked=not reward_owned, compact=True, show_enhance=False)
            if reward_owned: st.success("獲得済みです！（図鑑からリンゴをあげて育成できます）")
            else: st.info("このクエストをクリアすると獲得できます。")

        cols = st.columns(3)
        cols[0].link_button("公式ページ", q.get("official_url",""), use_container_width=True)
        cols[1].link_button("Googleマップ", google_maps_search_url(q.get("linked_name",""), q.get("area","")), use_container_width=True)
        if cols[2].button("お気に入り" if not favorite else "解除する", key=f"{ui_scope}_fav_{q['quest_id']}", use_container_width=True):
            if favorite: st.session_state.favorites.remove(q["quest_id"])
            else: st.session_state.favorites.add(q["quest_id"])
            save_user_data() # ★ 自動保存
            st.rerun()

        if show_actions:
            with st.expander("📝 記録を書いておく（タップして展開）", expanded=False):
                note_key = f"{ui_scope}_note_{q['quest_id']}"
                st.session_state.notes[q["quest_id"]] = st.text_area("感想・学んだこと", value=st.session_state.notes.get(q["quest_id"], ""), key=note_key, height=80)
                
                uploaded = st.file_uploader("写真を差し替える・追加する", type=["png", "jpg", "jpeg", "webp"], key=f"{ui_scope}_photo_{q['quest_id']}")
                if uploaded:
                    store_quest_photo(q["quest_id"], uploaded)
                    st.image(st.session_state.photo_data[q["quest_id"]], width=320)
                elif q["quest_id"] in st.session_state.photo_data:
                    st.image(st.session_state.photo_data[q["quest_id"]], width=320)

                sns_text = st.text_area("SNS投稿文", value=st.session_state.sns_texts.get(q["quest_id"], make_sns_text(q)), height=110, key=f"{ui_scope}_sns_{q['quest_id']}")
                st.session_state.sns_texts[q["quest_id"]] = sns_text
                
                sns_cols = st.columns(3)
                sns_cols[0].link_button("Xで投稿画面を開く", x_share_url(sns_text, q.get("official_url","")), use_container_width=True)
                sns_cols[1].link_button("Instagramを開く", "https://www.instagram.com/", use_container_width=True)
                sns_cols[2].link_button("TikTokを開く", "https://www.tiktok.com/upload?lang=ja-JP", use_container_width=True)
                st.caption("Xは投稿文を入れた状態で開きます。Instagram・TikTokは投稿画面を開き、写真と文章は手動で投稿する前提です。")

                st.session_state.x_post_urls[q["quest_id"]] = st.text_input("X投稿URL", value=st.session_state.x_post_urls.get(q["quest_id"], ""), key=f"{ui_scope}_xurl_{q['quest_id']}")

                if st.button("💾 このメモ・SNS文を保存する", key=f"{ui_scope}_save_memo_{q['quest_id']}"):
                    save_user_data() # ★ 自動保存
                    st.toast("📝 メモとSNS投稿文を保存しました！")


# =====================================================================
# ★ UI構築
# =====================================================================
st.set_page_config(page_title="天草つながりクエスト", page_icon="🌊", layout="wide")
init_state()

st.title("🌊 天草つながりクエスト")
st.caption("実在する天草の施設・祭り・地域イベントだけをクエスト化するプロトタイプ")

render_participant_setup()
if not st.session_state.get("data_loaded", False):
    load_user_data()
    st.session_state.data_loaded = True
    st.session_state.loaded_participant_id = st.session_state.get("participant_id")

col_log, col_prog = st.columns([1, 1])
with col_log:
    today_str = date.today().isoformat()
    if st.session_state.last_login_date != today_str:
        if st.button("🎁 今日のログインボーナス：🍎 リンゴを3個もらう", use_container_width=True):
            st.session_state.apples += 3
            st.session_state.last_login_date = today_str
            save_user_data() # ★ 自動保存
            st.rerun()
    else:
        st.success(f"🎁 本日受取済み！ 所持リンゴ: {st.session_state.apples}個")

with col_prog:
    total_q = len([q for q in QUESTS if q.get("quest_type") != "ストーリー"])
    valid_completed = [qid for qid in st.session_state.completed if get_quest(qid).get("quest_id")]
    done_q = len([qid for qid in valid_completed if get_quest(qid).get("quest_type") != "ストーリー"])
    st.progress(done_q / total_q if total_q else 0, text=f"参加した通常クエスト： {done_q} / {total_q}")

with st.expander("⚙️ GPS・デモ用現在地設定（タップして展開）"):
    st.session_state.gps_required = st.checkbox("GPSで訪問判定する", value=st.session_state.get("gps_required", True))
    st.session_state.gps_radius_m = st.slider("達成判定の半径", 50, 1000, int(st.session_state.get("gps_radius_m", 300)), 50)

    if get_geolocation is None: 
        st.warning("GPSライブラリ未インストール。")
    else:
        parsed = parse_geolocation_payload(get_geolocation())
        if parsed: set_current_location(parsed[0], parsed[1], parsed[2], "ブラウザGPS")

    manual = st.checkbox("緯度・経度を手入力して現在地にする", value=st.session_state.get("manual_location_enabled", False))
    if manual:
        mode = st.radio("設定方法", ["直接入力", "クエスト地点を使う"], horizontal=True)
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

st.write("") 

main_tab, list_tab, story_tab, map_tab, character_tab, gps_tab, fav_tab, summary_tab, db_tab = st.tabs([
    "🌟 おすすめクエスト", "🔍 全クエスト一覧", "📜 ストーリー", "👣 足跡マップ・日記", "🎁 キャラクター図鑑 & 育成", "🗺️ クエストマップ", "⭐ お気に入り", "🎒 旅のまとめ", "⚙️ データ確認"
])

with main_tab:
    st.subheader("あなたにおすすめの地域つながりクエスト")
    st.write("今の季節にぴったりなクエストを中心にピックアップしています！")
    recommended = recommend_quests([], "まだ決めていない", "日程未定", "指定なし", "")
    
    cols = st.columns(3)
    for i, q in enumerate(recommended[:12]):
        with cols[i % 3]:
            quest_card(q, show_actions=True, ui_scope=f"main_{i}_{q['quest_id']}")

with list_tab:
    st.subheader("🔍 全クエスト一覧")
    st.write("目的やエリアで絞り込んで、好きなクエストを探せます。")
    
    f_cols = st.columns(4)
    sel_tag = f_cols[0].selectbox("目的・タグ", ["すべて"] + [x for x in OBJECTIVES if x != "特になし"])
    sel_area = f_cols[1].selectbox("エリア", ["すべて"] + sorted(list(set(q["area"] for q in QUESTS if q.get("quest_type") != "ストーリー"))))
    sel_season = f_cols[2].selectbox("行く時期", SEASONS, index=6)
    kw = f_cols[3].text_input("キーワード検索", key="list_kw", placeholder="例：イルカ、海鮮")
    
    obj_filter = [sel_tag] if sel_tag != "すべて" else []
    area_filter = sel_area if sel_area != "すべて" else "指定なし"
    
    f_quests = recommend_quests(obj_filter, "まだ決めていない", sel_season, area_filter, kw)
    
    st.write(f"**該当クエスト： {len(f_quests)} 件**")
    
    for q in f_quests:
        with st.expander(f"📍 {q.get('quest_name','')} （{q.get('area','')} / {q.get('quest_type','')}）"):
            quest_card(q, show_actions=True, ui_scope=f"list_{q['quest_id']}")

with story_tab:
    st.header("📖 ストーリーモード")
    st.markdown("### ＃1. 天草四郎ゆかりの地をめぐる～隠された６つの奇跡～")
    st.write("天草四郎の足跡をたどりながら、天草の歴史と自然をめぐる物語。クエストを順番にクリアして、特別なキャラクターを仲間にしよう！")
    
    progress = st.session_state.story_progress
    
    for i, sq in enumerate(STORY_QUESTS):
        is_unlocked = (i <= progress)
        is_cleared = (i < progress)
        
        status_icon = "✅ クリア" if is_cleared else ("🔓 挑戦可能" if is_unlocked else "🔒 未解放")
        
        with st.expander(f"第{i+1}章：{sq.get('quest_name','')} （{status_icon}）", expanded=is_unlocked and not is_cleared):
            if not is_unlocked:
                st.warning("前のクエストをクリアすると解放され、詳細を見ることができます。")
                continue
            
            st.markdown(f"**目的地：** {sq.get('linked_name','')} （{sq.get('area','')}）")
            render_place_photo(sq, compact=True)
            st.write(sq.get('description',''))
            st.markdown(f"**達成条件：** {sq.get('condition','')}")
            
            if is_cleared:
                st.success("🎉 このクエストはクリア済みです！")
                st.markdown("#### 💡 クリア特典・プチ情報")
                st.info(sq.get('trivia',''))
                
                st.markdown("**獲得したキャラクター：**")
                reward_char = get_character_stage(QUEST_CHARACTER_REWARDS.get(sq['quest_id'], ""))
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    render_character_card(reward_char, locked=False, compact=True, show_enhance=False)
            else:
                st.markdown("#### クエストに挑戦する")
                gps_ok = render_gps_panel_for_quest(sq)
                photo_ok = render_photo_clear_panel(sq, ui_scope=f"story_{sq['quest_id']}")
                can_clear = gps_ok and photo_ok
                if not can_clear:
                    st.caption("クリアボタンは、GPS判定OK ＋ 写真添付OK の両方がそろうと押せます。")
                if st.button("このクエストをクリアして次へ進む", key=f"story_btn_{sq['quest_id']}", type="primary", use_container_width=True, disabled=not can_clear):
                    st.session_state.completed.add(sq["quest_id"])
                    if sq["quest_id"] not in st.session_state.completed_at:
                        st.session_state.completed_at[sq["quest_id"]] = datetime.now(timezone.utc).isoformat()
                    st.session_state.story_progress += 1
                    char = award_character_for_quest(sq)
                    st.session_state.apples += 3
                    save_diary_record(sq, "ストーリーモードでクリアしました！", make_sns_text(sq), "")
                    save_user_data() # ★ 自動保存
                    st.success(f"クエストクリア！ {char.get('emoji','')} {char.get('name','')} が仲間になり、次のクエストが解放されました！")
                    st.balloons()
                    st.rerun()

with map_tab: render_footprint_map()

with character_tab: render_character_collection()

with gps_tab: render_quest_map()

with fav_tab:
    st.subheader("⭐ お気に入り")
    favs = [get_quest(q) for q in st.session_state.favorites if get_quest(q).get("quest_id")]
    if not favs: st.info("お気に入りはありません。")
    else: 
        cols = st.columns(3)
        for i, q in enumerate(favs): 
            with cols[i % 3]:
                quest_card(q, ui_scope=f"fav_{i}")

with summary_tab:
    st.subheader("🎒 旅のまとめ")
    done = [get_quest(q) for q in st.session_state.completed if get_quest(q).get("quest_id")]
    if not done: st.info("まだ参加記録がありません。")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("参加クエスト", len(done))
        c2.metric("仲間キャラ", len(st.session_state.unlocked_character_ids))
        c3.metric("所持リンゴ", st.session_state.apples)

with db_tab:
    st.subheader("⚙️ データ確認・表紙写真の登録")
    st.write("各クエストの表紙写真（マスターイメージ）をここで簡単に登録・変更できます。")
    q_name = st.selectbox("写真を登録するクエストを選択", [q.get("quest_name","") for q in QUESTS])
    target_q = next((q for q in QUESTS if q.get("quest_name","") == q_name), None)
    if target_q:
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