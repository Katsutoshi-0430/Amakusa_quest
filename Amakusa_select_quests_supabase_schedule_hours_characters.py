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
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
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
    "祭り、イベント",
    "歴史、文化、ミュージアム",
    "食",
    "自然、海",
    "体験、工芸、ものづくり",
]
STAY_OPTIONS = ["日帰り", "宿泊", "まだ決めていない"]
SEASONS = ["今日・今週", "春", "夏", "秋", "冬", "通年", "日程未定"]
AREAS = ["指定なし", "上天草", "天草", "苓北"]

# 実証実験用に、目的とエリアの分類を固定する。
# ここに含めない分類は、全クエスト一覧の検索項目には表示しない。
PURPOSE_GROUP_QUEST_IDS: Dict[str, List[str]] = {
    "祭り、イベント": [
        "event_hondo", "event_ushibuka", "event_hanashobu",
    ],
    "歴史、文化、ミュージアム": [
        "story_1_shiro", "story_4_kirishitan", "story_5_tomioka",
    ],
    "食": [
        "spot_fukuzumi", "spot_hamankura", "spot_ikoi", "spot_lisola",
        "food_kura", "food_aosa", "story_3_ueno",
    ],
    "自然、海": [
        "play_seadonut", "nat_oppai", "photo_kuradake", "photo_nishihira",
        "play_oninoshiro", "story_2_senganzan", "story_6_sakitsu",
    ],
    "体験、工芸、ものづくり": [
        "craft_unshu", "spot_dolphin",
    ],
}

AREA_GROUP_QUEST_IDS: Dict[str, List[str]] = {
    "上天草": [
        "spot_fukuzumi", "spot_hamankura", "spot_lisola", "play_seadonut",
        "story_1_shiro", "story_2_senganzan", "story_3_ueno",
    ],
    "天草": [
        "event_hondo", "photo_kuradake", "photo_nishihira", "food_aosa",
        "food_kura", "event_ushibuka", "event_hanashobu", "play_oninoshiro",
        "spot_dolphin", "story_4_kirishitan", "story_6_sakitsu",
    ],
    "苓北": [
        "spot_ikoi", "nat_oppai", "craft_unshu", "story_5_tomioka",
    ],
}

QUEST_ID_TO_PURPOSE = {
    qid: purpose
    for purpose, qids in PURPOSE_GROUP_QUEST_IDS.items()
    for qid in qids
}
QUEST_ID_TO_AREA = {
    qid: area
    for area, qids in AREA_GROUP_QUEST_IDS.items()
    for qid in qids
}
STORY_QUEST_ORDER = {q.get("quest_id", ""): i + 1 for i, q in enumerate(STORY_QUESTS)}


def classified_purpose(q: Dict) -> str:
    """全クエスト一覧で表示・検索する目的分類を返す。"""
    return QUEST_ID_TO_PURPOSE.get(q.get("quest_id", ""), q.get("quest_type", ""))


def classified_area(q: Dict) -> str:
    """全クエスト一覧で表示・検索するエリア分類を返す。"""
    return QUEST_ID_TO_AREA.get(q.get("quest_id", ""), q.get("area", ""))


def is_story_quest(q: Dict) -> bool:
    return q.get("quest_id", "") in STORY_QUEST_ORDER


def story_chapter_number(q: Dict) -> Optional[int]:
    return STORY_QUEST_ORDER.get(q.get("quest_id", ""))


def story_is_unlocked(q: Dict) -> bool:
    chapter = story_chapter_number(q)
    if chapter is None:
        return True
    return (chapter - 1) <= int(st.session_state.get("story_progress", 0))


def story_is_cleared(q: Dict) -> bool:
    chapter = story_chapter_number(q)
    if chapter is None:
        return False
    return (chapter - 1) < int(st.session_state.get("story_progress", 0))


def display_quest_for_list(q: Dict) -> Dict:
    """一覧・マップ用の表示データ。未解放ストーリーは場所名をシークレットにする。"""
    display_q = dict(q)
    display_q["quest_type"] = classified_purpose(q)
    display_q["area"] = classified_area(q)

    if is_story_quest(q):
        chapter = story_chapter_number(q) or 0
        if story_is_unlocked(q):
            display_q["quest_name"] = f"ストーリーモード第{chapter}章：{q.get('quest_name', '')}"
        else:
            display_q["quest_name"] = f"ストーリーモード第{chapter}章（シークレット）"
            display_q["linked_name"] = "シークレット"
            display_q["description"] = "ストーリーモードを進めると、この章の目的地とクエスト内容が解放されます。"
            display_q["condition"] = "前のストーリークエストをクリアすると解放されます。"
            display_q["official_url"] = ""
            display_q["tags"] = [classified_purpose(q), classified_area(q), "ストーリー"]
    return display_q


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


# ---------------------------------------------------------------------
# Spreadsheet-derived quest details / coordinates / schedule metadata
# ---------------------------------------------------------------------
# 添付スプレッドシート「天草クエスト一覧.xlsx」の内容を反映した上書きデータ。
# 既存のクエストIDを維持したまま、クエスト名・座標・時期/営業時間・定休日を更新する。
SPREADSHEET_QUEST_PATCHES: Dict[str, Dict] = {'event_hondo': {'quest_name': '天草ほんどハイヤ祭りで夜の熱気を体験する', 'time_info': '7/25、7/26、8/1（2026年度）', 'business_hours': '7/25、7/26、8/1（2026年度）', 'closed_days': 'ー', 'source_row_place': '天草ほんどハイヤ祭りアマクサマツ', 'period': '7/25、7/26、8/1（2026年度）'}, 'spot_fukuzumi': {'quest_name': 'いけす料理ふくずみで海鮮を味わう', 'time_info': '11:00-14:30、 17:00-19:30', 'business_hours': '11:00-14:30、 17:00-19:30', 'closed_days': '毎週水曜日', 'source_row_place': 'いけす料理ふくずみリョウリ'}, 'spot_hamankura': {'quest_name': '浜崎鮮魚 浜んくらで豪快な魚料理を食べる', 'time_info': '11:00-23:00', 'business_hours': '11:00-23:00', 'closed_days': '不定休', 'source_row_place': '浜崎鮮魚浜んくらハマサキセンギョハマ'}, 'spot_ikoi': {'quest_name': 'いこい食堂で天草ちゃんぽんをすする', 'time_info': '11:00-13:30', 'business_hours': '11:00-13:30', 'closed_days': '土・日曜日', 'source_row_place': 'いこい食堂ショクドウ'}, 'spot_lisola': {'quest_name': 'リゾラテラス天草で塩パンと絶景を楽しむ', 'time_info': '平日9:00-17:30、土日祝9:00-18:00', 'business_hours': '平日9:00-17:30、土日祝9:00-18:00', 'closed_days': 'なし', 'source_row_place': 'リゾラテラス'}, 'play_seadonut': {'quest_name': '海中水族館シードーナツで海の生き物と遊ぶ', 'time_info': '3/20~10/19 9:00-18:00、 10/20~3/19 9:00-17:00', 'business_hours': '3/20~10/19 9:00-18:00、 10/20~3/19 9:00-17:00', 'closed_days': 'なし', 'source_row_place': '海中水族館シードーナツカイチュウスイゾクカン'}, 'nat_oppai': {'quest_name': 'おっぱい岩の不思議な形を見る', 'time_info': 'ー', 'business_hours': 'ー', 'closed_days': 'ー', 'source_row_place': 'おっぱい岩イワ'}, 'photo_kuradake': {'quest_name': '倉岳神社の天空の鳥居から絶景を撮る', 'time_info': 'ー', 'business_hours': 'ー', 'closed_days': 'ー', 'source_row_place': '倉岳神社クラタケジンジャ'}, 'photo_nishihira': {'quest_name': '西平椿公園でラピュタの木に驚く', 'time_info': 'ー', 'business_hours': 'ー', 'closed_days': 'ー', 'source_row_place': '西平椿公園ニシヒラツバキコウエン'}, 'food_aosa': {'quest_name': '大漁食堂あおさで新鮮な海鮮を堪能する', 'time_info': '11:00-15:00、 17:00-21:00', 'business_hours': '11:00-15:00、 17:00-21:00', 'closed_days': 'なし', 'source_row_place': '大漁食堂あおさダイギョショクドウ'}, 'food_kura': {'quest_name': '天草海鮮蔵でてんこ盛り丼を食らう', 'time_info': '11:00-16:00', 'business_hours': '11:00-16:00', 'closed_days': '不定休', 'source_row_place': '天草海鮮蔵アマクサカイセンクラ'}, 'event_ushibuka': {'quest_name': '牛深ハイヤ祭りの熱気を感じる', 'time_info': '4/17、4/18、4/19（2026年度）', 'business_hours': '4/17、4/18、4/19（2026年度）', 'closed_days': 'ー', 'source_row_place': '牛深ハイヤ祭りウシブカマツ', 'period': '4/17、4/18、4/19（2026年度）'}, 'event_hanashobu': {'quest_name': '天草花しょうぶ祭りで満開の花を愛でる', 'time_info': '6/6、6/7（2026年度）', 'business_hours': '6/6、6/7（2026年度）', 'closed_days': 'ー', 'source_row_place': '天草花しょうぶ祭りアマクサハナマツ', 'period': '6/6、6/7（2026年度）'}, 'play_oninoshiro': {'quest_name': '鬼の城公園で展望塔から絶景を見る', 'time_info': 'ー', 'business_hours': 'ー', 'closed_days': 'ー', 'source_row_place': '鬼の城公園オニシロコウエン'}, 'craft_unshu': {'quest_name': '雲舟窯で温かみのある天草陶磁器に出会う', 'time_info': '10:00-17:00', 'business_hours': '10:00-17:00', 'closed_days': '不定休', 'source_row_place': '雲舟窯ウンシュウカマ'}, 'spot_dolphin': {'quest_name': 'イルカセンターで野生のイルカを知る', 'time_info': '3~10月 9:00-18:00、 11~2月 9:00-17:00', 'business_hours': '3~10月 9:00-18:00、 11~2月 9:00-17:00', 'closed_days': '毎月第2・4水曜日、年末年始', 'source_row_place': 'イルカセンター'}, 'story_1_shiro': {'quest_name': '天草四郎との出会い', 'time_info': '9:00-17:00', 'business_hours': '9:00-17:00', 'closed_days': '12/29~1/1、1・6月の第2水曜日', 'source_row_place': '天草四郎ミュージアムアマクサシロウ'}, 'story_2_senganzan': {'quest_name': '絶景の山で仲間を集めろ', 'time_info': 'ー', 'business_hours': 'ー', 'closed_days': 'ー', 'source_row_place': '千巌山センガンザン'}, 'story_3_ueno': {'quest_name': '天草大王コロッケで腹ごしらえ', 'time_info': '9:00-18:00', 'business_hours': '9:00-18:00', 'closed_days': '日曜日', 'source_row_place': 'ファミリーショップうえの'}, 'story_4_kirishitan': {'quest_name': '奇跡の旗を探し出せ', 'time_info': '9:00-17:00', 'business_hours': '9:00-17:00', 'closed_days': '火曜日', 'source_row_place': '天草キリシタン館アマクサカン'}, 'story_5_tomioka': {'quest_name': '難攻不落の城を調査せよ', 'time_info': 'ー', 'business_hours': 'ー', 'closed_days': 'ー', 'source_row_place': '富岡城跡トミオカジョウセキ'}, 'story_6_sakitsu': {'quest_name': '平和な街へたどり着け', 'time_info': 'ー', 'business_hours': 'ー', 'closed_days': 'ー', 'source_row_place': '崎津集落サキツシュウラク'}}

SPREADSHEET_COORD_UPDATES: Dict[str, Tuple[float, float]] = {'event_hondo': (32.4556566, 130.199987), 'spot_fukuzumi': (32.5188852015741, 130.422679537183), 'spot_hamankura': (32.5481646571749, 130.421738907566), 'spot_ikoi': (32.524330828054, 130.033959225541), 'spot_lisola': (32.5276741360745, 130.42622494288), 'play_seadonut': (32.5298923684305, 130.42834666602), 'nat_oppai': (32.5404691864404, 130.11210456602), 'photo_kuradake': (32.4278836342759, 130.327333059979), 'photo_nishihira': (32.3475201478057, 129.978735082671), 'food_aosa': (32.1940616800265, 130.027649879495), 'food_kura': (32.5496148153241, 130.167306337185), 'event_ushibuka': (32.1967404084772, 130.026386830685), 'event_hanashobu': (32.4675531230178, 130.171460442328), 'play_oninoshiro': (32.5046979770165, 130.16423590639), 'craft_unshu': (32.5193809395413, 130.035016163127), 'spot_dolphin': (32.5457113115041, 130.130597437849), 'story_1_shiro': (32.575919182804, 130.421189844898), 'story_2_senganzan': (32.5131997358584, 130.419315860399), 'story_3_ueno': (32.5181662627699, 130.453448537183), 'story_4_kirishitan': (32.4601451315796, 130.184069279509), 'story_5_tomioka': (32.5294112782553, 130.031524608348), 'story_6_sakitsu': (32.3120676064363, 130.025899539258)}


def apply_spreadsheet_quest_updates() -> None:
    # スプレッドシート由来のクエスト内容・営業情報・座標を反映する。
    for _q in QUESTS + STORY_QUESTS:
        _qid = _q.get("quest_id", "")
        if _qid in SPREADSHEET_QUEST_PATCHES:
            _q.update(SPREADSHEET_QUEST_PATCHES[_qid])
    QUEST_COORDS.update(SPREADSHEET_COORD_UPDATES)


apply_spreadsheet_quest_updates()

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
    "祭り、イベント": {"emoji": "🎆", "label": "地域の祭り・イベント"},
    "歴史、文化、ミュージアム": {"emoji": "🏛️", "label": "天草の歴史・文化"},
    "自然、海": {"emoji": "🌊", "label": "海と自然の体験"},
    "体験、工芸、ものづくり": {"emoji": "🏺", "label": "体験・工芸・ものづくり"},
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

    # --- 通常クエスト専用キャラクター（各施設・イベントごと） ---
    "basic_char_hukuzumi": {
        "rarity": "ノーマル", "series": "食・海鮮",
        "stages": [
            {"name": "ふくずみの海鮮っ子", "emoji": "🐟", "catch": "いけすの海の幸から生まれた、元気な海鮮キャラクター！", "img_id": "basic_char_hukuzumi①"},
            {"name": "ふくずみ海鮮大将", "emoji": "🐟", "catch": "新鮮な海の力をまとって進化した、頼れる海鮮大将！", "img_id": "basic_char_hukuzumi②"},
        ],
    },
    "basic_char_hamankura": {
        "rarity": "ノーマル", "series": "食・鮮魚",
        "stages": [
            {"name": "浜んくらの魚っ子", "emoji": "🐠", "catch": "鮮魚店直営の活気をまとった、魚料理の案内役！", "img_id": "basic_char_hamankura①"},
            {"name": "浜んくら豪快魚将", "emoji": "🐠", "catch": "豪快な魚料理の力で進化した、浜の元気印！", "img_id": "basic_char_hamankura②"},
        ],
    },
    "basic_char_ikoi_shokudou": {
        "rarity": "ノーマル", "series": "食・地元食堂",
        "stages": [
            {"name": "いこいちゃんぽん", "emoji": "🍜", "catch": "地元で愛されるちゃんぽんの湯気から生まれた、あったかキャラ！", "img_id": "basic_char_ikoi_shokudou①"},
            {"name": "いこい満腹大将", "emoji": "🍜", "catch": "具だくさんの元気をまとって進化した、満腹の守り手！", "img_id": "basic_char_ikoi_shokudou②"},
        ],
    },
    "basic_char_rizoraterasu": {
        "rarity": "レア", "series": "食・リゾート",
        "stages": [
            {"name": "リゾラしおパン", "emoji": "🥐", "catch": "海辺の塩パンと潮風が大好きな、リゾートキャラクター！", "img_id": "basic_char_rizoraterasu①"},
            {"name": "リゾラテラスの光パン", "emoji": "🥐", "catch": "絶景と塩パンの力で輝く、海辺の人気者！", "img_id": "basic_char_rizoraterasu②"},
        ],
    },
    "basic_char_si-do-natsu": {
        "rarity": "レア", "series": "自然・水族館",
        "stages": [
            {"name": "シードナッツ", "emoji": "🐬", "catch": "海に浮かぶ水族館からやってきた、好奇心いっぱいの海の仲間！", "img_id": "basic_char_si-do-natsu①"},
            {"name": "シードーナツ海王", "emoji": "🐬", "catch": "海の生き物たちと仲良くなって進化した、海上水族館の守り手！", "img_id": "basic_char_si-do-natsu②"},
        ],
    },
    "basic_char_oppaiiwa": {
        "rarity": "ノーマル", "series": "自然・奇岩",
        "stages": [
            {"name": "おっぱい岩ころん", "emoji": "🪨", "catch": "干潮のときに姿を見せる、不思議な岩のマスコット！", "img_id": "basic_char_oppaiiwa①"},
            {"name": "おっぱい岩まもりん", "emoji": "🪨", "catch": "潮の満ち引きを見守る、やさしい奇岩の精！", "img_id": "basic_char_oppaiiwa②"},
        ],
    },
    "basic_char_kuratake_jinja": {
        "rarity": "レア", "series": "自然・神社",
        "stages": [
            {"name": "倉岳とりい丸", "emoji": "⛩️", "catch": "天空の鳥居から天草の海を見守る、小さな神社キャラ！", "img_id": "basic_char_kuratake_jinja①"},
            {"name": "倉岳天空守", "emoji": "⛩️", "catch": "山頂の風と祈りを受けて進化した、天空の守り手！", "img_id": "basic_char_kuratake_jinja②"},
        ],
    },
    "basic_nishihiratsubaki": {
        "rarity": "レア", "series": "自然・公園",
        "stages": [
            {"name": "椿のラピュタっ子", "emoji": "🌳", "catch": "アコウの根と椿の森から生まれた、生命力あふれるキャラクター！", "img_id": "basic_nishihiratsubaki①"},
            {"name": "西平椿の森守", "emoji": "🌳", "catch": "大地に根を張る力で進化した、椿公園の守り神！", "img_id": "basic_nishihiratsubaki②"},
        ],
    },
    "basic_char_aosa": {
        "rarity": "ノーマル", "series": "食・海鮮食堂",
        "stages": [
            {"name": "あおさ丸", "emoji": "🍚", "catch": "牛深の海鮮とあおさの香りが大好きな食堂キャラ！", "img_id": "basic_char_aosa①"},
            {"name": "大漁あおさ大将", "emoji": "🍚", "catch": "大漁の海の幸をまとって進化した、牛深のごちそう番長！", "img_id": "basic_char_aosa②"},
        ],
    },
    "basic_char_kaisen_kura": {
        "rarity": "レア", "series": "食・海鮮",
        "stages": [
            {"name": "海鮮蔵うにころ", "emoji": "🦐", "catch": "海鮮蔵の名物と海の幸から生まれた、食いしん坊キャラ！", "img_id": "basic_char_kaisen_kura①"},
            {"name": "海鮮蔵てんこ盛り王", "emoji": "🦐", "catch": "てんこ盛りの海鮮パワーで進化した、五和の海鮮王！", "img_id": "basic_char_kaisen_kura②"},
        ],
    },
    "basic_char_usibuka_haiyamatsuri": {
        "rarity": "レア", "series": "祭り・ハイヤ",
        "stages": [
            {"name": "牛深ハイヤっ子", "emoji": "🎆", "catch": "ハイヤ節のリズムにのって踊る、牛深祭りの小さな主役！", "img_id": "basic_char_usibuka_haiyamatsuri①"},
            {"name": "牛深ハイヤ舞将", "emoji": "🎆", "catch": "祭りの熱気で進化した、踊りと音頭の盛り上げ役！", "img_id": "basic_char_usibuka_haiyamatsuri②"},
        ],
    },
    "basic_char_hanasyobumatsuri": {
        "rarity": "ノーマル", "series": "祭り・花",
        "stages": [
            {"name": "花しょうぶのしずく", "emoji": "🌸", "catch": "花しょうぶの色どりから生まれた、やさしい花の精！", "img_id": "basic_char_hanasyobumatsuri①"},
            {"name": "花しょうぶ姫", "emoji": "🌸", "catch": "満開の花に包まれて進化した、初夏の華やかなキャラクター！", "img_id": "basic_char_hanasyobumatsuri②"},
        ],
    },
    "basic_char_hondo_haiyamatsuri": {
        "rarity": "レア", "series": "祭り・ハイヤ",
        "stages": [
            {"name": "ほんどハイヤっ子", "emoji": "🎇", "catch": "本渡の夏の夜に生まれた、明るい祭りキャラクター！", "img_id": "basic_char_hondo_haiyamatsuri①"},
            {"name": "ほんどハイヤ大踊り", "emoji": "🎇", "catch": "夜の熱気とハイヤ踊りで進化した、夏祭りのスター！", "img_id": "basic_char_hondo_haiyamatsuri②"},
        ],
    },
    "basic_char_unsyukkama": {
        "rarity": "ノーマル", "series": "工芸・陶磁器",
        "stages": [
            {"name": "雲舟こだぬき", "emoji": "🏺", "catch": "土のぬくもりと器のやさしさから生まれた、窯元キャラ！", "img_id": "basic_char_unsyukkama①"},
            {"name": "雲舟陶芸守", "emoji": "🏺", "catch": "炎と土の力で進化した、ものづくりの守り手！", "img_id": "basic_char_unsyukkama②"},
        ],
    },
    "basic_char_iruka_senta": {
        "rarity": "レア", "series": "体験・イルカ",
        "stages": [
            {"name": "イルカセンターっち", "emoji": "🐬", "catch": "早崎海峡のイルカに会いたくてやってきた、海の案内役！", "img_id": "basic_char_iruka_senta①"},
            {"name": "イルカセンター海翔", "emoji": "🐬", "catch": "野生のイルカと潮風の力で進化した、海を翔ける仲間！", "img_id": "basic_char_iruka_senta②"},
        ],
    },
    "basic_char_oninoshiro_koen": {
        "rarity": "ノーマル", "series": "自然・公園",
        "stages": [
            {"name": "鬼の城こおに", "emoji": "👹", "catch": "鬼の伝説が残る公園から生まれた、ちょっと強がりな小鬼キャラ！", "img_id": "basic_char_oninoshiro_koen①"},
            {"name": "鬼の城展望鬼", "emoji": "👹", "catch": "展望塔から海峡を見渡す力で進化した、公園の守り鬼！", "img_id": "basic_char_oninoshiro_koen②"},
        ],
    },

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
    # 通常クエスト：各施設・イベント専用キャラクター
    "spot_fukuzumi": "basic_char_hukuzumi",
    "spot_hamankura": "basic_char_hamankura",
    "spot_ikoi": "basic_char_ikoi_shokudou",
    "spot_lisola": "basic_char_rizoraterasu",
    "play_seadonut": "basic_char_si-do-natsu",
    "nat_oppai": "basic_char_oppaiiwa",
    "photo_kuradake": "basic_char_kuratake_jinja",
    "photo_nishihira": "basic_nishihiratsubaki",
    "food_aosa": "basic_char_aosa",
    "food_kura": "basic_char_kaisen_kura",
    "event_ushibuka": "basic_char_usibuka_haiyamatsuri",
    "event_hanashobu": "basic_char_hanasyobumatsuri",
    "event_hondo": "basic_char_hondo_haiyamatsuri",
    "play_oninoshiro": "basic_char_oninoshiro_koen",
    "craft_unshu": "basic_char_unsyukkama",
    "spot_dolphin": "basic_char_iruka_senta",

    # ストーリーキャラ紐づけ
    "story_1_shiro": "story_char_amakusa_siro",
    "story_2_senganzan": "story_char_senganzan",
    "story_3_ueno": "story_char_amakusa_daio",
    "story_4_kirishitan": "story_char_maria_kannon",
    "story_5_tomioka": "story_char_tomiokajo",
    "story_6_sakitsu": "story_char_sakitsu_syuraku",
}


def rewardable_character_ids() -> List[str]:
    """図鑑に表示する、実際にクエストから獲得できるキャラクターID一覧。"""
    ids: List[str] = []
    for q in list(QUESTS) + list(STORY_QUESTS):
        cid = QUEST_CHARACTER_REWARDS.get(q.get("quest_id", ""))
        if cid and cid in CHARACTERS and cid not in ids:
            ids.append(cid)
    return ids

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

def character_storage_public_url(lookup_id: str) -> str:
    """
    Supabase StorageのPublic bucketからキャラクター画像URLを作る。
    GitHubのcharacter_imagesに画像がない場合の補助機能。

    Streamlit Secretsで必要に応じて変更可能：
    SUPABASE_CHARACTER_IMAGE_BUCKET = "character-images"
    SUPABASE_CHARACTER_IMAGE_EXT = "png"  # webp / png / jpg など
    """
    try:
        base_url = str(st.secrets.get("SUPABASE_URL", "")).strip().rstrip("/")
        bucket = str(st.secrets.get("SUPABASE_CHARACTER_IMAGE_BUCKET", "character-images")).strip() or "character-images"
        ext = str(st.secrets.get("SUPABASE_CHARACTER_IMAGE_EXT", "png")).strip().lstrip(".") or "png"
    except Exception:
        return ""
    if not base_url or not lookup_id:
        return ""
    filename = urllib.parse.quote(f"{lookup_id}.{ext}")
    bucket_q = urllib.parse.quote(bucket)
    return f"{base_url}/storage/v1/object/public/{bucket_q}/{filename}"


def character_image_display_src(lookup_id: str) -> str:
    """キャラクター画像の表示元。ローカル画像を優先し、なければSupabase Storage URLを返す。"""
    local_path = character_image_path(lookup_id)
    if local_path:
        return str(local_path)
    return character_storage_public_url(lookup_id)

def get_character_stage(cid: str) -> dict:
    if cid not in CHARACTERS:
        cid = "amanya"
    base_char = CHARACTERS[cid]

    fed = int(st.session_state.character_apples.get(cid, 0))
    stages = base_char.get("stages", []) or [{"name": cid, "emoji": "✨", "catch": "天草の仲間"}]
    stage_count = len(stages)

    # 通常キャラは「初期→進化」の2段階、ストーリーキャラは3段階に対応。
    if stage_count >= 3:
        if fed >= 20:
            stage_idx = 2
        elif fed >= 10:
            stage_idx = 1
        else:
            stage_idx = 0
    elif stage_count == 2:
        stage_idx = 1 if fed >= 10 else 0
    else:
        stage_idx = 0
    stage_idx = min(stage_idx, stage_count - 1)

    res = dict(base_char)
    res.update(stages[stage_idx])
    res["stage_idx"] = stage_idx
    res["fed_apples"] = fed
    res["character_id"] = cid
    res["stage_count"] = stage_count
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
APP_SURVEY_QUEST_ID = "__survey__"

AGE_OPTIONS = ["選択してください", "10代", "20代", "30代", "40代", "50代", "60代以上"]
FEATURE_SURVEY_ITEMS = [
    "全クエストモード",
    "ストーリーモード",
    "キャラクターコレクション",
    "クエストマップ",
    "旅のまとめ",
    "足跡マップ・旅日記",
    "ログインボーナス",
]
FEATURE_RATING_OPTIONS = [
    "使っていない",
    "1：とても不満",
    "2：やや不満",
    "3：どちらともいえない",
    "4：満足",
    "5：とても満足",
]

# 公式サイト・観光協会等で確認できた連絡先。電話ボタン表示用。
QUEST_PHONE_NUMBERS: Dict[str, str] = {
    "spot_fukuzumi": "0969-56-0299",
    "spot_hamankura": "0964-59-0777",
    "spot_ikoi": "0969-35-1014",
    "spot_lisola": "0969-56-3450",
    "play_seadonut": "0969-56-1155",
    "food_aosa": "0969-73-3758",
    "food_kura": "0969-52-7707",
    "craft_unshu": "080-5254-7915",
    "spot_dolphin": "0969-33-1600",
    "story_1_shiro": "0964-56-5311",
    "story_3_ueno": "0969-56-1255",
    "story_4_kirishitan": "0969-22-3845",
}

def quest_phone(q: Dict) -> str:
    return QUEST_PHONE_NUMBERS.get(q.get("quest_id", ""), "")

def tel_url(phone: str) -> str:
    digits = re.sub(r"[^0-9+]", "", phone or "")
    return f"tel:{digits}" if digits else ""


def _safe_secret(name: str, default: str = "") -> str:
    """Streamlit Secretsの値を安全に取得する。"""
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def _supabase_connection_values() -> Tuple[str, str]:
    """
    SupabaseのURLとキーを取得する。

    新形式:
      SUPABASE_URL
      SUPABASE_SERVICE_ROLE_KEY
      SUPABASE_SECRET_KEY

    旧形式:
      [supabase]
      url
      service_role_key

    の両方に対応する。
    """
    url = _safe_secret("SUPABASE_URL")
    key = (
        _safe_secret("SUPABASE_SERVICE_ROLE_KEY")
        or _safe_secret("SUPABASE_SECRET_KEY")
    )

    if not url or not key:
        try:
            supabase_secrets = st.secrets.get("supabase", {})

            if not url:
                url = str(
                    supabase_secrets.get("url", "")
                ).strip()

            if not key:
                key = str(
                    supabase_secrets.get("service_role_key", "")
                    or supabase_secrets.get("secret_key", "")
                    or supabase_secrets.get("key", "")
                ).strip()
        except Exception:
            pass

    return url, key


def supabase_is_configured() -> bool:
    """Supabase接続に必要な設定がそろっているか確認する。"""
    url, key = _supabase_connection_values()

    return (
        create_client is not None
        and bool(url)
        and bool(key)
    )


@st.cache_resource
def get_supabase_client() -> Optional["Client"]:
    """Supabaseクライアントを作成する。"""
    if create_client is None:
        return None

    url, key = _supabase_connection_values()

    if not url or not key:
        return None

    return create_client(url, key)


def _get_query_param(name: str) -> str:
    """URLのクエリパラメータを取得する。"""
    try:
        value = st.query_params.get(name, "")
        if isinstance(value, list):
            return str(value[0]).strip() if value else ""
        return str(value).strip()
    except Exception:
        return ""


def render_participant_setup() -> None:
    """
    利用者が覚えやすいニックネームを入力する。
    DB互換のため、内部保存キーは従来どおり participant_id を使用する。
    """
    query_pid = _get_query_param("pid")
    if query_pid and not st.session_state.get("participant_id"):
        st.session_state.participant_id = query_pid

    with st.expander("👤 ニックネーム", expanded=not bool(st.session_state.get("participant_id"))):
        st.caption("進捗を保存するため、ほかの参加者と重ならないニックネームを入力してください。同じニックネームで開くと続きから遊べます。")
        pid = st.text_input(
            "ニックネーム",
            value=st.session_state.get("participant_id", ""),
            placeholder="例：mei0720",
            key="participant_id_input",
            max_chars=30,
        ).strip()

        if st.button("このニックネームで始める", type="primary", use_container_width=True):
            if not pid:
                st.warning("ニックネームを入力してください。")
            else:
                old_pid = st.session_state.get("participant_id")
                st.session_state.participant_id = pid
                if old_pid != pid:
                    st.session_state.data_loaded = False
                    st.session_state.loaded_participant_id = None
                st.rerun()

        if st.session_state.get("participant_id"):
            st.success(f"👋 {st.session_state.participant_id} さん")
            if supabase_is_configured():
                st.caption("進捗は自動保存されます")
            else:
                st.warning("Supabase Secretsが未設定です。今はローカル保存になります。実証実験前に必ず設定してください。")
        else:
            st.info("ニックネームを入力するとアプリを始められます。")

    if not st.session_state.get("participant_id"):
        st.stop()

    ensure_participant(st.session_state.participant_id)

    # ニックネームが変わった場合は、その利用者のデータを再ロードする。
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
        "profile_age": st.session_state.get("profile_age", ""),
        "guide_seen": bool(st.session_state.get("guide_seen", False)),
        "survey_answers": st.session_state.get("survey_answers", {}),
        "survey_submitted": bool(st.session_state.get("survey_submitted", False)),
        "survey_submitted_at": st.session_state.get("survey_submitted_at"),
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
    st.session_state.profile_age = data.get("profile_age", "")
    st.session_state.guide_seen = bool(data.get("guide_seen", False))
    st.session_state.survey_answers = data.get("survey_answers", {}) or {}
    st.session_state.survey_submitted = bool(data.get("survey_submitted", False))
    st.session_state.survey_submitted_at = data.get("survey_submitted_at")

    if include_photo_binary:
        photo_data = {}
        for k, v in data.get("photo_data", {}).items():
            try:
                photo_data[k] = base64.b64decode(v)
            except Exception:
                pass
        st.session_state.photo_data = photo_data



def save_survey_to_quest_progress(payload: Dict) -> bool:
    """
    アンケート回答を quest_progress の quest_id='__survey__' に確実に保存する。
    同じニックネームの回答がすでに存在する場合は、その行を更新する。
    """
    pid = st.session_state.get("participant_id", "").strip()

    if not pid or not supabase_is_configured():
        return False

    supabase = get_supabase_client()
    if supabase is None:
        return False

    ensure_participant(pid)

    now_iso = datetime.now(timezone.utc).isoformat()
    submitted_at = (
        payload.get("submitted_at")
        or st.session_state.get("survey_submitted_at")
        or now_iso
    )

    row = {
        "participant_id": pid,
        "quest_id": APP_SURVEY_QUEST_ID,
        "completed": True,
        "completed_at": submitted_at,
        "favorite": False,
        "note": json.dumps(payload, ensure_ascii=False),
        "photo_uploaded": False,
        "apples": int(st.session_state.get("apples", 0)),
        "updated_at": now_iso,
    }

    # 既存行の有無を確認。
    # composite unique 制約が無いDBでも動くよう、upsertだけに依存しない。
    existing = (
        supabase
        .table("quest_progress")
        .select("id")
        .eq("participant_id", pid)
        .eq("quest_id", APP_SURVEY_QUEST_ID)
        .limit(1)
        .execute()
    )

    if existing.data:
        row_id = existing.data[0].get("id")

        if row_id is not None:
            (
                supabase
                .table("quest_progress")
                .update(row)
                .eq("id", row_id)
                .execute()
            )
        else:
            (
                supabase
                .table("quest_progress")
                .update(row)
                .eq("participant_id", pid)
                .eq("quest_id", APP_SURVEY_QUEST_ID)
                .execute()
            )
    else:
        (
            supabase
            .table("quest_progress")
            .insert(row)
            .execute()
        )

    return True


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

    # アンケートは専用行にJSON保存。SupabaseのCSV出力時に参加者ごとに抽出しやすくする。
    survey_payload = dict(st.session_state.get("survey_answers", {}) or {})
    if st.session_state.get("profile_age"):
        survey_payload["age"] = st.session_state.get("profile_age")
    supabase.table("quest_progress").upsert({
        "participant_id": pid,
        "quest_id": APP_SURVEY_QUEST_ID,
        "completed": bool(st.session_state.get("survey_submitted", False)),
        "completed_at": st.session_state.get("survey_submitted_at"),
        "favorite": False,
        "note": json.dumps(survey_payload, ensure_ascii=False),
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

    # アンケート専用行があれば復元する。
    survey_row = next((r for r in rows if r.get("quest_id") == APP_SURVEY_QUEST_ID), None)
    if survey_row:
        try:
            st.session_state.survey_answers = json.loads(survey_row.get("note") or "{}")
        except Exception:
            st.session_state.survey_answers = {}
        st.session_state.survey_submitted = bool(survey_row.get("completed"))
        st.session_state.survey_submitted_at = survey_row.get("completed_at")
        if not st.session_state.get("profile_age"):
            st.session_state.profile_age = st.session_state.survey_answers.get("age", "")

    # クエストごとの状態を上書き・補完する。
    for row in rows:
        qid = row.get("quest_id")
        if not qid or qid in {APP_STATE_QUEST_ID, APP_SURVEY_QUEST_ID}:
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
        "clear_effect": None,
        "clear_effect_counter": 0,
        "clear_effect_shown_id": None,
        "profile_age": "",
        "guide_seen": False,
        "survey_answers": {},
        "survey_submitted": False,
        "survey_submitted_at": None,
        "map_selected_qid": "",
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
    img = character_image_display_src(lookup_id)
    name = "？？？" if locked else char.get("name", "")
    rarity = char.get("rarity", "")
    series = char.get("series", "")
    catch = "まだ出会っていない仲間です。対応するクエストをクリアすると解放されます。" if locked else char.get("catch", "")
    emoji = "❓" if locked else char.get("emoji", "✨")

    with st.container(border=True):
        if img and not locked:
            st.image(img, use_container_width=True)
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
            fed = int(char.get("fed_apples", 0))
            stage_count = int(char.get("stage_count", len(char.get("stages", [])) or 1))
            max_apples = 20 if stage_count >= 3 else 10
            st.divider()
            
            if fed >= max_apples:
                st.progress(1.0)
                st.button("✨ 進化MAX", key=f"feed_{char.get('character_id')}", disabled=True, use_container_width=True)
            else:
                target = 20 if stage_count >= 3 and fed >= 10 else 10
                st.caption(f"次の進化まで： {fed} / {target} 個")
                st.progress(min(fed / max_apples, 1.0))
                
                apples_owned = int(st.session_state.apples)
                cid = char.get("character_id")
                next_need = max(0, target - fed)
                feed_cols = st.columns(2)

                if feed_cols[0].button("🍎 1個あげる", key=f"feed_one_{cid}", disabled=apples_owned <= 0, use_container_width=True):
                    give = min(1, apples_owned, max_apples - fed)
                    old_fed = fed
                    new_fed = fed + give
                    st.session_state.apples -= give
                    st.session_state.character_apples[cid] = new_fed
                    if (old_fed < 10 <= new_fed) or (old_fed < 20 <= new_fed):
                        st.balloons()
                    save_user_data()
                    st.rerun()

                bulk_label = f"🍎 進化まで一気に（{next_need}個）"
                if feed_cols[1].button(bulk_label, key=f"feed_bulk_{cid}", disabled=apples_owned < next_need or next_need <= 0, use_container_width=True):
                    old_fed = fed
                    new_fed = min(max_apples, fed + next_need)
                    st.session_state.apples -= (new_fed - old_fed)
                    st.session_state.character_apples[cid] = new_fed
                    if (old_fed < 10 <= new_fed) or (old_fed < 20 <= new_fed):
                        st.balloons()
                    save_user_data()
                    st.rerun()

                if apples_owned < next_need:
                    st.caption(f"進化まであと{next_need}個必要です（所持：{apples_owned}個）")


def render_character_collection() -> None:
    st.subheader("🎁 キャラクター図鑑 & 育成")
    st.write("クエストをクリアしてキャラクターを集めよう！通常クエストのキャラは🍎リンゴ10個で進化、ストーリーキャラは10個で1進化・累計20個で最終進化します。")
    
    col1, col2 = st.columns(2)
    character_ids = rewardable_character_ids()
    total = len(character_ids)
    unlocked = len([cid for cid in st.session_state.unlocked_character_ids if cid in character_ids])
    col1.metric("獲得キャラクター", f"{unlocked} / {total}")
    col2.metric("所持しているリンゴ 🍎", f"{st.session_state.apples} 個")
    st.progress(unlocked / total if total else 0)

    st.markdown("### コレクション＆進化させる")

    for i in range(0, len(character_ids), 3):
        cols = st.columns(3)
        for col, cid in zip(cols, character_ids[i:i+3]):
            with col:
                locked = cid not in st.session_state.unlocked_character_ids
                c = get_character_stage(cid)
                render_character_card(c, locked=locked, compact=True, show_enhance=not locked)


def image_file_to_data_url(path: Optional[Path]) -> str:
    """キャラクター画像をHTML内で表示するためにBase64化する。"""
    if not path or not path.exists():
        return ""
    suffix = path.suffix.lower().lstrip(".") or "png"
    mime = "image/png"
    if suffix in ["jpg", "jpeg"]:
        mime = "image/jpeg"
    elif suffix == "webp":
        mime = "image/webp"
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""

def character_image_html_src(lookup_id: str) -> str:
    """CLEAR演出HTML内で使う画像src。ローカルはBase64、StorageはPublic URLで表示する。"""
    local_path = character_image_path(lookup_id)
    if local_path:
        return image_file_to_data_url(local_path)
    return character_storage_public_url(lookup_id)


def trigger_clear_effect(q: Dict, char: Dict, apples_awarded: int, new_character: bool, already_completed: bool = False) -> None:
    """クエストクリア直後に表示する演出データをsession_stateへ保存する。"""
    st.session_state.clear_effect_counter = int(st.session_state.get("clear_effect_counter", 0)) + 1
    st.session_state.clear_effect = {
        "effect_id": st.session_state.clear_effect_counter,
        "quest_id": q.get("quest_id", ""),
        "quest_name": q.get("quest_name", ""),
        "linked_name": q.get("linked_name", ""),
        "quest_type": q.get("quest_type", ""),
        "area": q.get("area", ""),
        "character_id": char.get("character_id", ""),
        "character_name": char.get("name", ""),
        "character_emoji": char.get("emoji", "✨"),
        "rarity": char.get("rarity", ""),
        "series": char.get("series", ""),
        "catch": char.get("catch", ""),
        "img_id": char.get("img_id", char.get("character_id", "")),
        "apples_awarded": int(apples_awarded),
        "new_character": bool(new_character),
        "already_completed": bool(already_completed),
    }


def render_clear_reward_effect() -> None:
    """CLEAR演出・キャラクターGET演出を上部に表示する。"""
    event = st.session_state.get("clear_effect")
    if not event:
        return

    effect_id = event.get("effect_id")
    if st.session_state.get("clear_effect_shown_id") != effect_id:
        st.balloons()
        st.session_state.clear_effect_shown_id = effect_id

    img_id = event.get("img_id") or event.get("character_id", "")
    char_img = character_image_html_src(img_id)
    char_name = html.escape(event.get("character_name", "仲間キャラクター"))
    char_emoji = html.escape(event.get("character_emoji", "✨"))
    quest_name = html.escape(event.get("quest_name", "クエスト"))
    linked_name = html.escape(event.get("linked_name", ""))
    rarity = html.escape(event.get("rarity", ""))
    series = html.escape(event.get("series", ""))
    catch = html.escape(event.get("catch", ""))
    apples = int(event.get("apples_awarded", 0))
    already_completed = bool(event.get("already_completed"))
    new_character = bool(event.get("new_character"))

    if char_img:
        char_visual = f'<img class="reward-character-img" src="{char_img}" alt="{char_name}">'
    else:
        char_visual = f'<div class="reward-character-emoji">{char_emoji}</div>'

    get_label = "キャラクターGET!!" if new_character else "キャラクター確認!!"
    clear_label = "CLEAR!!" if not already_completed else "UPDATE!!"
    sub_label = "新しい仲間が加わりました" if new_character else "獲得済みキャラクターの記録を更新しました"

    st.markdown(
        f"""
        <style>
        @keyframes clearPop {{
          0% {{ transform: scale(.78) rotate(-2deg); opacity: 0; }}
          60% {{ transform: scale(1.05) rotate(1deg); opacity: 1; }}
          100% {{ transform: scale(1) rotate(0deg); opacity: 1; }}
        }}
        @keyframes shineSweep {{
          0% {{ transform: translateX(-130%) rotate(18deg); }}
          100% {{ transform: translateX(130%) rotate(18deg); }}
        }}
        @keyframes characterFloat {{
          0%, 100% {{ transform: translateY(0px) scale(1); }}
          50% {{ transform: translateY(-10px) scale(1.04); }}
        }}
        @keyframes sparklePulse {{
          0%, 100% {{ opacity: .55; transform: scale(.96); }}
          50% {{ opacity: 1; transform: scale(1.08); }}
        }}
        .clear-reward-card {{
          position: relative;
          overflow: hidden;
          border-radius: 28px;
          padding: 24px 22px 22px 22px;
          margin: 18px 0 22px 0;
          color: #ffffff;
          background:
            radial-gradient(circle at 50% 36%, rgba(255,236,122,.95) 0%, rgba(255,184,47,.45) 22%, transparent 42%),
            linear-gradient(135deg, #06376f 0%, #07508f 45%, #062b5f 100%);
          border: 4px solid rgba(255, 222, 89, .95);
          box-shadow: 0 18px 48px rgba(6, 43, 95, .36), inset 0 0 28px rgba(255,255,255,.12);
          animation: clearPop .65s cubic-bezier(.2,1.2,.25,1) both;
        }}
        .clear-reward-card:before {{
          content: "";
          position: absolute;
          inset: -80px;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,.42), transparent);
          width: 46%;
          animation: shineSweep 1.9s ease-in-out infinite;
        }}
        .reward-sparkles {{
          position: absolute;
          inset: 14px;
          pointer-events: none;
          font-size: 24px;
          letter-spacing: 12px;
          opacity: .92;
          animation: sparklePulse 1.2s ease-in-out infinite;
        }}
        .clear-reward-inner {{
          position: relative;
          display: grid;
          grid-template-columns: minmax(170px, 240px) 1fr;
          gap: 22px;
          align-items: center;
          z-index: 1;
        }}
        .reward-visual-wrap {{
          min-height: 210px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 26px;
          background: radial-gradient(circle, rgba(255,255,255,.9) 0%, rgba(255,229,111,.82) 36%, rgba(36,128,194,.18) 72%);
          box-shadow: inset 0 0 30px rgba(255,255,255,.72), 0 12px 26px rgba(0,0,0,.18);
        }}
        .reward-character-img {{
          max-width: 180px;
          max-height: 180px;
          object-fit: contain;
          filter: drop-shadow(0 12px 18px rgba(0,0,0,.28));
          animation: characterFloat 1.6s ease-in-out infinite;
        }}
        .reward-character-emoji {{
          font-size: 100px;
          filter: drop-shadow(0 12px 18px rgba(0,0,0,.28));
          animation: characterFloat 1.6s ease-in-out infinite;
        }}
        .reward-clear-title {{
          display: inline-block;
          padding: 4px 18px 8px 18px;
          color: #fff56f;
          font-size: clamp(44px, 8vw, 84px);
          font-weight: 1000;
          line-height: .95;
          letter-spacing: 1px;
          text-shadow: 0 5px 0 #00549c, 0 9px 16px rgba(0,0,0,.38);
          transform: rotate(-3deg);
        }}
        .reward-get {{
          display: inline-block;
          margin-top: 8px;
          padding: 10px 16px;
          border-radius: 16px;
          background: linear-gradient(180deg, #fff2a8, #ffbe32);
          color: #173763;
          font-size: 24px;
          font-weight: 900;
          box-shadow: 0 8px 0 rgba(120,72,0,.38);
        }}
        .reward-character-name {{
          margin-top: 12px;
          font-size: 28px;
          font-weight: 900;
        }}
        .reward-meta {{
          margin-top: 8px;
          color: #d6ecff;
          font-size: 14px;
        }}
        .reward-quest {{
          margin-top: 14px;
          padding: 12px 14px;
          border-radius: 14px;
          background: rgba(255,255,255,.12);
          border: 1px solid rgba(255,255,255,.26);
          font-weight: 800;
        }}
        .reward-catch {{
          margin-top: 10px;
          color: #f4fbff;
          font-size: 14px;
        }}
        .reward-apples {{
          margin-top: 14px;
          display: inline-block;
          padding: 8px 14px;
          border-radius: 999px;
          background: rgba(255,255,255,.18);
          border: 1px solid rgba(255,255,255,.25);
          font-weight: 800;
        }}
        @media (max-width: 760px) {{
          .clear-reward-inner {{ grid-template-columns: 1fr; text-align: center; }}
          .reward-visual-wrap {{ min-height: 170px; }}
          .reward-character-img {{ max-width: 145px; max-height: 145px; }}
          .reward-character-emoji {{ font-size: 82px; }}
        }}
        </style>
        <div class="clear-reward-card">
          <div class="reward-sparkles">✨ 🎉 ⭐ 💫 ✨ 🎊 ⭐</div>
          <div class="clear-reward-inner">
            <div class="reward-visual-wrap">{char_visual}</div>
            <div>
              <div class="reward-clear-title">{clear_label}</div><br>
              <div class="reward-get">{get_label}</div>
              <div class="reward-character-name">{char_emoji} {char_name}</div>
              <div class="reward-meta">{rarity} / {series}</div>
              <div class="reward-catch">{catch}</div>
              <div class="reward-quest">クエスト：{quest_name}<br><span style="font-size:13px; opacity:.88;">{linked_name}</span></div>
              <div class="reward-apples">🍎 リンゴ +{apples}　{sub_label}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("OK（タップで確認）", key=f"clear_effect_ok_{effect_id}", type="primary", use_container_width=True):
            st.session_state.clear_effect = None
            st.rerun()
    with c2:
        if event.get("quest_id"):
            st.link_button("このクエストをもう一度見る", app_focus_url(event.get("quest_id")), use_container_width=True)
    st.divider()


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

def recommend_quests(
    objectives: List[str],
    stay: str,
    season: str,
    area: str,
    keyword: str = "",
    include_story: bool = False,
) -> List[Dict]:
    """
    目的・エリアを実証実験用の固定分類で絞り込む。
    include_story=True の時だけ、ストーリーモードの章も一覧・マップに表示する。
    """
    rows = []
    current_season = get_current_season()
    all_quests = list(QUESTS) + (list(STORY_QUESTS) if include_story else [])
    quest_order = {q.get("quest_id", ""): i for i, q in enumerate(all_quests)}

    selected_purposes = [obj for obj in objectives if obj and obj != "すべて"]

    for q in all_quests:
        qid = q.get("quest_id", "")
        purpose_group = classified_purpose(q)
        area_group = classified_area(q)
        display_q = display_quest_for_list(q)

        # ユーザー指定の分類に含めていないクエストは、一覧検索には出さない。
        if purpose_group not in PURPOSE_GROUP_QUEST_IDS:
            continue
        if area_group not in AREA_GROUP_QUEST_IDS:
            continue

        if selected_purposes and purpose_group not in selected_purposes:
            continue
        if area != "指定なし" and area_group != area:
            continue
        if not season_match(q.get("season", ""), season):
            continue
        if keyword:
            kw = keyword.strip().lower()
            search_target = f"{display_q.get('quest_name','')} {display_q.get('linked_name','')} {display_q.get('description','')} {' '.join(display_q.get('tags',[]))}".lower()
            if kw not in search_target:
                continue

        obj_score = 1
        stay_score = stay_match_score(q, stay)
        if stay == "日帰り" and q.get("stay_fit") == "宿泊推奨":
            stay_score = 0
        season_bonus = 20 if q.get("season") == current_season else 0

        # ストーリー未解放は下に回す。見せるが、通常クエストより優先しない。
        story_penalty = -50 if is_story_quest(q) and not story_is_unlocked(q) else 0
        order_bonus = -quest_order.get(qid, 999) / 100
        score = obj_score * 10 + stay_score * 3 + season_bonus + story_penalty + order_bonus
        rows.append((score, q))

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


# ---------------------------------------------------------------------
# Business hours / holiday display helpers
# ---------------------------------------------------------------------
WEEKDAY_LABELS = ["月", "火", "水", "木", "金", "土", "日"]


def jp_now() -> datetime:
    """日本時間の現在日時を返す。"""
    try:
        return datetime.now(ZoneInfo("Asia/Tokyo"))
    except Exception:
        return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9)))


def _is_blank_schedule_text(text: str) -> bool:
    return not text or str(text).strip() in {"ー", "-", "なし", "未設定", "nan", "None"}


def _time_from_hm(hm: str):
    h, m = hm.split(":")
    return int(h), int(m)


def _time_ranges_from_text(text: str) -> List[Tuple[int, int, int, int]]:
    ranges = []
    for start, end in re.findall(r"(\d{1,2}:\d{2})\s*[-~〜]\s*(\d{1,2}:\d{2})", str(text)):
        sh, sm = _time_from_hm(start)
        eh, em = _time_from_hm(end)
        ranges.append((sh, sm, eh, em))
    return ranges


def _is_time_in_ranges(now_dt: datetime, ranges: List[Tuple[int, int, int, int]]) -> bool:
    now_minutes = now_dt.hour * 60 + now_dt.minute
    for sh, sm, eh, em in ranges:
        start = sh * 60 + sm
        end = eh * 60 + em
        if start <= end:
            if start <= now_minutes <= end:
                return True
        else:
            if now_minutes >= start or now_minutes <= end:
                return True
    return False


def _md_in_range(now_dt: datetime, start_month: int, start_day: int, end_month: int, end_day: int) -> bool:
    today = (now_dt.month, now_dt.day)
    start = (start_month, start_day)
    end = (end_month, end_day)
    if start <= end:
        return start <= today <= end
    return today >= start or today <= end


def _month_in_range(month: int, start_month: int, end_month: int) -> bool:
    if start_month <= end_month:
        return start_month <= month <= end_month
    return month >= start_month or month <= end_month


def _nth_weekday_of_month(now_dt: datetime) -> int:
    return (now_dt.day - 1) // 7 + 1


def is_closed_today(q: Dict, now_dt: Optional[datetime] = None) -> Tuple[bool, str, bool]:
    """定休日判定。戻り値は (休みか, 理由, 不定休など要確認か)。"""
    now_dt = now_dt or jp_now()
    closed = str(q.get("closed_days", "")).strip()
    if _is_blank_schedule_text(closed):
        return False, "", False
    if "不定休" in closed:
        return False, "定休日は不定休です。来訪前に公式情報を確認してください。", True
    if "年末年始" in closed and ((now_dt.month == 12 and now_dt.day >= 29) or (now_dt.month == 1 and now_dt.day <= 3)):
        return True, f"本日は定休日です（{closed}）。", False
    if "12/29~1/1" in closed and ((now_dt.month == 12 and now_dt.day >= 29) or (now_dt.month == 1 and now_dt.day <= 1)):
        return True, f"本日は定休日です（{closed}）。", False

    weekday = now_dt.weekday()
    nth = _nth_weekday_of_month(now_dt)

    if "1・6月の第2水曜日" in closed and now_dt.month in {1, 6} and weekday == 2 and nth == 2:
        return True, f"本日は定休日です（{closed}）。", False
    if "毎月第2・4水曜日" in closed and weekday == 2 and nth in {2, 4}:
        return True, f"本日は定休日です（{closed}）。", False
    if "毎週水曜日" in closed and weekday == 2:
        return True, f"本日は定休日です（{closed}）。", False
    if "水曜日" in closed and "第" not in closed and weekday == 2:
        return True, f"本日は定休日です（{closed}）。", False
    if "火曜日" in closed and weekday == 1:
        return True, f"本日は定休日です（{closed}）。", False
    if "土・日曜日" in closed and weekday in {5, 6}:
        return True, f"本日は定休日です（{closed}）。", False
    if "土曜日" in closed and weekday == 5:
        return True, f"本日は定休日です（{closed}）。", False
    if "日曜日" in closed and weekday == 6:
        return True, f"本日は定休日です（{closed}）。", False

    return False, "", False


def schedule_open_status(q: Dict, now_dt: Optional[datetime] = None) -> Dict:
    """時期・営業時間・定休日から、現在やっているかの表示情報を作る。"""
    now_dt = now_dt or jp_now()
    time_info = str(q.get("time_info") or q.get("business_hours") or q.get("period") or "").strip()
    closed_days = str(q.get("closed_days", "")).strip()
    is_closed, closed_reason, uncertain_closed = is_closed_today(q, now_dt)

    if is_closed:
        return {"level": "error", "status": "休業日", "message": f"現在はやっていない可能性が高いです。{closed_reason}", "time_info": time_info, "closed_days": closed_days}

    uncertain_note = closed_reason if uncertain_closed else ""

    if _is_blank_schedule_text(time_info):
        return {"level": "info" if not uncertain_note else "warning", "status": "時間指定なし" if not uncertain_note else "要確認", "message": uncertain_note or "営業時間・開催時間の指定がないスポットです。屋外スポット等は、現地状況を確認してください。", "time_info": time_info, "closed_days": closed_days}

    if re.search(r"\d{1,2}/\d{1,2}", time_info) and ":" not in time_info:
        event_dates = [(int(m), int(d)) for m, d in re.findall(r"(\d{1,2})/(\d{1,2})", time_info)]
        if (now_dt.month, now_dt.day) in event_dates:
            return {"level": "success" if not uncertain_note else "warning", "status": "開催日", "message": f"本日は開催日です。{uncertain_note}".strip(), "time_info": time_info, "closed_days": closed_days}
        return {"level": "warning", "status": "開催日ではありません", "message": f"現在は開催期間外です。開催日程：{time_info}", "time_info": time_info, "closed_days": closed_days}

    selected_text = time_info
    normalized = time_info.replace(" ", "")

    if "平日" in normalized and "土日祝" in normalized:
        if now_dt.weekday() >= 5:
            m = re.search(r"土日祝(\d{1,2}:\d{2}\s*[-~〜]\s*\d{1,2}:\d{2})", normalized)
        else:
            m = re.search(r"平日(\d{1,2}:\d{2}\s*[-~〜]\s*\d{1,2}:\d{2})", normalized)
        if m:
            selected_text = m.group(1)
    elif "3/20~10/19" in normalized and "10/20~3/19" in normalized:
        selected_text = "9:00-18:00" if _md_in_range(now_dt, 3, 20, 10, 19) else "9:00-17:00"
    elif "3~10月" in normalized and "11~2月" in normalized:
        selected_text = "9:00-18:00" if _month_in_range(now_dt.month, 3, 10) else "9:00-17:00"

    ranges = _time_ranges_from_text(selected_text)
    if ranges:
        in_hours = _is_time_in_ranges(now_dt, ranges)
        if in_hours:
            return {"level": "success" if not uncertain_note else "warning", "status": "営業時間内" if not uncertain_note else "営業時間内・要確認", "message": f"現在は営業時間内です。{uncertain_note}".strip(), "time_info": time_info, "closed_days": closed_days}
        return {"level": "warning", "status": "営業時間外", "message": f"現在は営業時間外です。営業時間：{time_info}", "time_info": time_info, "closed_days": closed_days}

    return {"level": "info" if not uncertain_note else "warning", "status": "要確認" if uncertain_note else "時間情報あり", "message": uncertain_note or "時期・営業時間が登録されています。来訪前に公式情報も確認してください。", "time_info": time_info, "closed_days": closed_days}


def schedule_status_badge_html(q: Dict) -> str:
    status = schedule_open_status(q)
    level = status.get("level", "info")
    colors = {"success": ("#dcfce7", "#166534", "#86efac"), "warning": ("#fef9c3", "#854d0e", "#fde68a"), "error": ("#fee2e2", "#991b1b", "#fecaca"), "info": ("#e0f2fe", "#075985", "#bae6fd")}
    bg, fg, border = colors.get(level, colors["info"])
    return f'<div style="margin:6px 0; padding:7px 9px; border-radius:10px; background:{bg}; color:{fg}; border:1px solid {border}; font-size:12px;"><b>{html.escape(status.get("status", ""))}</b><br>{html.escape(status.get("message", ""))}</div>'


def render_schedule_notice(q: Dict) -> None:
    """クエストカードに営業時間・定休日・現在の営業判定を表示する。"""
    time_info = str(q.get("time_info") or q.get("business_hours") or "").strip()
    closed_days = str(q.get("closed_days", "")).strip()
    if time_info and time_info != "ー":
        st.markdown(f"**時期・営業時間：** {time_info}")
    if closed_days and closed_days != "ー":
        st.markdown(f"**定休日：** {closed_days}")

    status = schedule_open_status(q)
    message = status.get("message", "")
    label = status.get("status", "")
    if status.get("level") == "success":
        st.success(f"{label}：{message}")
    elif status.get("level") == "warning":
        st.warning(f"{label}：{message}")
    elif status.get("level") == "error":
        st.error(f"{label}：{message}")
    else:
        st.info(f"{label}：{message}")

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
    st.caption("クリア条件：GPS判定・写真")

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


def app_focus_url(qid: str) -> str:
    """マップのポップアップから、同じアプリ内の該当クエスト表示へ移動するURLを作る。"""
    params = {}
    pid = st.session_state.get("participant_id", "")
    if pid:
        params["pid"] = pid
    params["focus_qid"] = qid
    return "?" + urllib.parse.urlencode(params)


def quest_map_popup_html(q: Dict, include_distance: bool = True) -> str:
    qid = q.get("quest_id", "")
    display_q = display_quest_for_list(q)
    dist = format_distance(distance_to_quest_m(q)) if include_distance else "距離不明"
    tags = " / ".join([str(t) for t in display_q.get("tags", [])])
    official_url = html.escape(display_q.get("official_url", ""), quote=True)
    maps_url = html.escape(google_maps_search_url(display_q.get("linked_name", ""), display_q.get("area", "")), quote=True)
    quest_url = html.escape(app_focus_url(qid), quote=True)
    description = html.escape(display_q.get("description", ""))
    condition = html.escape(display_q.get("condition", ""))
    official_html = f'<a href="{official_url}" target="_blank" style="font-size:12px;">公式ページ</a>' if official_url else ''
    maps_html = f'<a href="{maps_url}" target="_blank" style="font-size:12px;">Googleマップ</a>' if display_q.get("linked_name") != "シークレット" else ''
    return f"""
    <div style="font-family:sans-serif; width:310px; line-height:1.45;">
      <h4 style="margin:0 0 6px 0;">📍 {html.escape(display_q.get('quest_name',''))}</h4>
      <div style="font-size:12px; color:#555; margin-bottom:6px;">
        {html.escape(display_q.get('linked_name',''))}<br>
        {html.escape(display_q.get('area',''))} / {html.escape(display_q.get('quest_type',''))} / {html.escape(display_q.get('season',''))}
      </div>
      {schedule_status_badge_html(q)}
      <p style="font-size:13px; margin:6px 0;"><b>内容</b><br>{description}</p>
      <p style="font-size:13px; margin:6px 0;"><b>達成条件</b><br>{condition}</p>
      <p style="font-size:12px; color:#555; margin:6px 0;"><b>タグ</b><br>{html.escape(tags)}</p>
      <p style="font-size:12px; color:#2563eb; margin:6px 0;"><b>現在地からの距離</b>：{html.escape(dist)}</p>
      <div style="margin-top:10px; display:flex; gap:8px; flex-wrap:wrap;">
        <a href="{quest_url}" target="_top" style="font-size:12px; font-weight:700; color:#fff; background:#2563eb; padding:6px 10px; border-radius:8px; text-decoration:none;">このクエストを見る</a>
        {official_html}
        {maps_html}
      </div>
    </div>
    """


def render_quest_map(quests_to_show: Optional[List[Dict]] = None, map_title: str = "🗺️ クエストマップ") -> Optional[str]:
    if map_title:
        st.subheader(map_title)
    st.caption("地図のピンをタップすると、選んだクエストがすぐ下に表示されます。")

    if folium is None or st_folium is None:
        st.error("地図を表示するには folium と streamlit-folium が必要です。requirements.txt に追加してください。")
        return None

    all_quests = list(quests_to_show) if quests_to_show is not None else list(QUESTS) + list(STORY_QUESTS)
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
    c3.metric("参加済み", len([q for q in all_quests if q.get("quest_id") in st.session_state.completed]))

    # 天草・九州が初期表示になるようにする。
    m = folium.Map(
        location=[32.45, 130.20],
        zoom_start=9,
        min_zoom=7,
        max_bounds=True,
        tiles="OpenStreetMap",
    )
    try:
        m.fit_bounds([[32.05, 129.85], [32.68, 130.55]])
    except Exception:
        pass

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
        "祭り、イベント": "red",
        "歴史、文化、ミュージアム": "cadetblue",
        "食": "orange",
        "自然、海": "green",
        "体験、工芸、ものづくり": "darkblue",
    }

    bounds = []
    for q in quests_with_coords:
        coord = get_coord(q)
        if not coord:
            continue
        bounds.append(coord)
        display_q = display_quest_for_list(q)
        qtype = display_q.get("quest_type", "")
        qid = q.get("quest_id", "")
        completed = qid in st.session_state.completed
        icon_color = "gray" if completed else type_color.get(qtype, "darkgreen")
        tooltip = f"{'✅ ' if completed else ''}{display_q.get('quest_name','')}"
        folium.Marker(
            location=coord,
            tooltip=tooltip,
            popup=folium.Popup(quest_map_popup_html(q), max_width=360),
            icon=folium.Icon(color=icon_color, icon="flag" if completed else "map-marker", prefix="fa"),
        ).add_to(m)

    if bounds and len(bounds) > 1:
        try:
            m.fit_bounds(bounds)
        except Exception:
            pass

    map_state = st_folium(
        m,
        width=None,
        height=480,
        use_container_width=True,
        returned_objects=["last_object_clicked"],
        key=f"quest_map_{abs(hash(tuple(q.get('quest_id','') for q in all_quests)))}",
    )

    selected_qid = st.session_state.get("map_selected_qid", "")
    clicked = (map_state or {}).get("last_object_clicked") or {}
    if clicked and clicked.get("lat") is not None and clicked.get("lng") is not None:
        click_lat = float(clicked["lat"])
        click_lng = float(clicked["lng"])
        # マーカー座標とクリック座標を照合。約20m以内ならそのクエストを選択。
        closest_qid = ""
        closest_d = float("inf")
        for candidate in quests_with_coords:
            candidate_coord = get_coord(candidate)
            if not candidate_coord:
                continue
            d = haversine_m(click_lat, click_lng, candidate_coord[0], candidate_coord[1])
            if d < closest_d:
                closest_d = d
                closest_qid = candidate.get("quest_id", "")
        if closest_qid and closest_d <= 25:
            selected_qid = closest_qid
            st.session_state.map_selected_qid = closest_qid

    if quests_without_coords:
        with st.expander("座標未登録のクエストを確認する", expanded=False):
            st.warning("以下のクエストは座標が未登録のため、地図に表示できません。")
            st.dataframe(pd.DataFrame([{
                "quest_id": q.get("quest_id", ""),
                "クエスト名": display_quest_for_list(q).get("quest_name", ""),
                "施設・イベント": display_quest_for_list(q).get("linked_name", ""),
                "エリア": classified_area(q),
            } for q in quests_without_coords]), use_container_width=True)

    return selected_qid


def render_locked_story_card(q: Dict, ui_scope: str = "story_locked") -> None:
    """未解放ストーリーを一覧に出す時のカード。場所名は見せない。"""
    display_q = display_quest_for_list(q)
    with st.container(border=True):
        st.markdown(f"### 🔒 {display_q.get('quest_name','')}")
        st.caption(f"未解放 / {display_q.get('quest_type','')} / {display_q.get('area','')} / {display_q.get('season','')}")
        render_placeholder_place_card(display_q, compact=True)
        st.warning("この章はまだ解放されていません。ストーリーモードを順番に進めると、目的地とクエスト内容が表示されます。")
        st.markdown("**紐づく実在施設・イベント：** シークレット")
        st.markdown("**達成条件：** 前のストーリークエストをクリアすると解放されます。")


def quest_card(q: Dict, show_actions: bool = True, ui_scope: str = "quest") -> None:
    if not q.get("quest_id"): return
    completed = q["quest_id"] in st.session_state.completed

    with st.container(border=True):
        st.markdown(f"### 📍 {q.get('quest_name','')}")
        st.caption(f"{'✅ 参加済み' if completed else '未参加'} / {q.get('quest_type','')} / {q.get('area','')} / {q.get('season','')} / {q.get('connection_level','')}")
        render_place_photo(q, compact=not show_actions)
        st.write(q.get("description",""))
        st.markdown(f"**紐づく実在施設・イベント：** {q.get('linked_name','')}")
        phone = quest_phone(q)
        if phone:
            st.markdown(f"**電話番号：** [{phone}]({tel_url(phone)})")
        if q.get("period"): st.markdown(f"**開催・利用時期：** {q['period']}")
        render_schedule_notice(q)
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
                reward_preview = get_character_for_quest(q)
                reward_cid = reward_preview.get("character_id", "")
                was_unlocked = reward_cid in st.session_state.unlocked_character_ids

                st.session_state.completed.add(q["quest_id"])
                if q["quest_id"] not in st.session_state.completed_at:
                    st.session_state.completed_at[q["quest_id"]] = datetime.now(timezone.utc).isoformat()
                if q["quest_id"] not in st.session_state.completed_order: st.session_state.completed_order.append(q["quest_id"])
                
                char = award_character_for_quest(q)
                save_diary_record(q, st.session_state.notes.get(q["quest_id"], ""), st.session_state.sns_texts.get(q["quest_id"], make_sns_text(q)), st.session_state.x_post_urls.get(q["quest_id"], ""))
                
                apples_awarded = 2
                st.session_state.apples += apples_awarded
                trigger_clear_effect(q, char, apples_awarded=apples_awarded, new_character=(not was_unlocked), already_completed=already_completed)
                save_user_data() # ★ 自動保存
                st.rerun()

        reward_char = get_character_for_quest(q)
        reward_owned = reward_char.get("character_id") in st.session_state.unlocked_character_ids
        with st.expander("🎁 このクエストで仲間になるキャラクター", expanded=False):
            # クエスト詳細では未獲得でも獲得予定キャラクターを見せる。
            # 図鑑側では、獲得するまで「？」のシークレット表示を維持する。
            render_character_card(reward_char, locked=False, compact=True, show_enhance=False)
            if reward_owned:
                st.success("獲得済みです！（図鑑からリンゴをあげて育成できます）")
            else:
                st.info("このクエストをクリアすると、このキャラクターを獲得できます。図鑑では獲得するまでシークレット表示になります。")

        cols = st.columns(2)
        if q.get("official_url"):
            cols[0].link_button("🔗 公式ページ", q.get("official_url",""), use_container_width=True)
        cols[1].link_button("🗺️ Googleマップ", google_maps_search_url(q.get("linked_name",""), q.get("area","")), use_container_width=True)

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


def _option_index(options: List[str], value: str, default: int = 0) -> int:
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return default


def render_profile_setup() -> None:
    """実証実験で最低限必要な年代を、利用開始時に1回だけ取得する。"""
    if st.session_state.get("profile_age"):
        return

    st.info("🧪 テストマーケティングの集計のため、最初に年代だけ教えてください。個人を特定する情報は入力しません。")
    with st.form("profile_age_form"):
        age = st.selectbox("年代", AGE_OPTIONS, index=0)
        submitted = st.form_submit_button("年代を登録してアプリを始める", type="primary", use_container_width=True)
    if submitted:
        if age == "選択してください":
            st.warning("年代を選択してください。")
        else:
            st.session_state.profile_age = age
            answers = dict(st.session_state.get("survey_answers", {}) or {})
            answers["age"] = age
            st.session_state.survey_answers = answers
            save_user_data()
            st.rerun()
    st.stop()


def render_usage_guide() -> None:
    expanded = not bool(st.session_state.get("guide_seen", False))
    with st.expander("📘 はじめての方へ｜アプリの使い方", expanded=expanded):
        st.markdown("""
**① クエストを選ぶ**  
「おすすめ」または「全クエストモード」から、行ってみたい場所を選びます。マップから探すこともできます。

**② 現地でクエストに挑戦**  
対象スポットへ行き、GPS判定と写真添付を行うとクリアできます。

**③ キャラクターとリンゴを獲得**  
クエストをクリアするとキャラクターとリンゴを獲得できます。

**④ ストーリーモードにも挑戦**  
天草四郎ゆかりの地を順番に巡るモードです。前の章をクリアすると次の章が解放されます。

**⑤ 旅の記録を残す**  
足跡マップ・旅日記や旅のまとめで、訪れた場所や感想を振り返れます。

**⑥ 最後にアンケートへ回答**  
「アンケート」タブから、使った機能や再訪意欲について回答してください。
        """)
        if not st.session_state.get("guide_seen", False):
            if st.button("✅ 使い方を確認しました", use_container_width=True):
                st.session_state.guide_seen = True
                save_user_data()
                st.rerun()


def render_survey() -> None:
    st.subheader("📝 テストマーケティング アンケート")
    st.write("ご協力ありがとうございます。回答はアプリ改善と、天草への再訪につながるかの検証に使用します。")
    if st.session_state.get("survey_submitted"):
        st.success("✅ アンケートは回答済みです。内容を変更して再送信することもできます。")

    ans = dict(st.session_state.get("survey_answers", {}) or {})
    age_value = st.session_state.get("profile_age") or ans.get("age", "")
    gender_options = ["選択してください", "男性", "女性", "回答しない・その他"]
    region_options = ["選択してください", "天草", "熊本県内（天草外）", "九州地方（熊本県外）", "関東地方", "関西地方", "その他"]
    companion_options = ["一人旅", "家族（配偶者・パートナー）", "家族（子ども連れ）", "家族（親・その他親族）", "友人・知人", "恋人", "旅行ではない（天草在住・日常利用）", "その他"]
    game_options = ["選択してください", "よくする", "たまにする", "あまりしない", "全くしない"]
    visit_options = ["選択してください", "初めて", "2回目", "3〜5回目", "6回目以上（リピーター）", "天草在住"]
    change_options = ["選択してください", "1：大きく下がった", "2：やや下がった", "3：変わらない", "4：やや高まった", "5：大きく高まった", "該当しない（天草在住）"]
    intent_options = ["選択してください", "1：全くそう思わない", "2：あまりそう思わない", "3：どちらともいえない", "4：そう思う", "5：とてもそう思う", "該当しない（天草在住）"]
    satisfaction_options = ["選択してください", "1：とても不満", "2：やや不満", "3：どちらともいえない", "4：満足", "5：とても満足"]

    with st.form("test_marketing_survey"):
        st.markdown("### ■ あなた自身について（基本属性）")
        age = st.selectbox("Q1. 年代を教えてください。", AGE_OPTIONS[1:], index=max(0, _option_index(AGE_OPTIONS[1:], age_value, 0)))
        gender = st.selectbox("Q2. 性別を教えてください。", gender_options, index=_option_index(gender_options, ans.get("gender", "")))
        region = st.selectbox("Q3. お住まいの地域を教えてください。", region_options, index=_option_index(region_options, ans.get("region", "")))
        region_other = st.text_input("Q3-2. 「その他」の場合、地域を入力してください。", value=ans.get("region_other", ""))
        companions = st.multiselect("Q4. 今回の旅の同行者を教えてください。（複数選択可）", companion_options, default=ans.get("companions", []))
        companion_other = st.text_input("Q4-2. 「その他」の場合、同行者を入力してください。", value=ans.get("companion_other", ""))
        gaming = st.selectbox("Q5. 普段、ゲーム（スマホアプリ、据え置き機など）はしますか？", game_options, index=_option_index(game_options, ans.get("gaming", "")))
        visits = st.selectbox("Q6. 天草への訪問は今回で何回目ですか？", visit_options, index=_option_index(visit_options, ans.get("visits", "")))

        st.markdown("### ■ アプリの機能について")
        st.caption("各機能について、実際に使ったうえでの満足度を教えてください。使っていない機能は「使っていない」を選択してください。")
        feature_answers = {}
        saved_features = ans.get("feature_ratings", {}) or {}
        for i, feature in enumerate(FEATURE_SURVEY_ITEMS, start=7):
            feature_answers[feature] = st.radio(f"Q{i}. {feature}", FEATURE_RATING_OPTIONS, index=_option_index(FEATURE_RATING_OPTIONS, saved_features.get(feature, "使っていない")), horizontal=True, key=f"survey_feature_{feature}")

        qn = 7 + len(FEATURE_SURVEY_ITEMS)
        st.markdown("### ■ アプリを通しての再訪意欲")
        revisit_change = st.selectbox(f"Q{qn}. このアプリを使ったことで、天草に『また来たい』という気持ちは高まりましたか？", change_options, index=_option_index(change_options, ans.get("revisit_change", "")))
        revisit_intent = st.selectbox(f"Q{qn+1}. 今後1年以内に、天草を再び訪れたいと思いますか？", intent_options, index=_option_index(intent_options, ans.get("revisit_intent", "")))
        reuse_intent = st.selectbox(f"Q{qn+2}. 次回天草を訪れる際にも、このアプリを使いたいと思いますか？", intent_options, index=_option_index(intent_options, ans.get("reuse_intent", "")))

        st.markdown("### ■ アプリ全体について")
        satisfaction = st.selectbox(f"Q{qn+3}. アプリ全体の満足度を教えてください。", satisfaction_options, index=_option_index(satisfaction_options, ans.get("overall_satisfaction", "")))
        good_points = st.text_area(f"Q{qn+4}. 良かった点を教えてください。", value=ans.get("good_points", ""), height=100)
        improvement_points = st.text_area(f"Q{qn+5}. 改善してほしい点を教えてください。", value=ans.get("improvement_points", ""), height=100)
        requested_features = st.text_area(f"Q{qn+6}. 追加してほしい機能があれば教えてください。", value=ans.get("requested_features", ""), height=100)
        submitted = st.form_submit_button("📨 アンケートを送信する", type="primary", use_container_width=True)

    if submitted:
        required_missing = []
        if gender == "選択してください": required_missing.append("性別")
        if region == "選択してください": required_missing.append("居住地域")
        if not companions: required_missing.append("同行者")
        if "一人旅" in companions and len(companions) > 1: required_missing.append("同行者（一人旅と他の選択肢は同時に選べません）")
        if gaming == "選択してください": required_missing.append("ゲーム頻度")
        if visits == "選択してください": required_missing.append("天草訪問回数")
        if revisit_change == "選択してください": required_missing.append("再訪意欲の変化")
        if revisit_intent == "選択してください": required_missing.append("1年以内の再訪意向")
        if reuse_intent == "選択してください": required_missing.append("アプリ再利用意向")
        if satisfaction == "選択してください": required_missing.append("全体満足度")
        if region == "その他" and not region_other.strip(): required_missing.append("その他の居住地域")
        if "その他" in companions and not companion_other.strip(): required_missing.append("その他の同行者")

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

            # クエスト進捗・アプリ全体の状態も従来どおり保存
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


# =====================================================================
# ★ UI構築
# =====================================================================
st.set_page_config(
    page_title="天草つながりクエスト",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def apply_charming_blue_theme() -> None:
    """スマホでも見やすい、青を基調にしたチャーミングなUI。"""
    st.markdown(
        """
        <style>
        :root {
          --ama-blue: #1479d3;
          --ama-blue-dark: #075aa8;
          --ama-sky: #55bde9;
          --ama-pale: #edf8ff;
          --ama-pale-2: #f7fcff;
          --ama-ink: #16324a;
          --ama-border: #cfeafa;
        }
        .stApp {
          background:
            radial-gradient(circle at 8% 0%, rgba(85,189,233,.18), transparent 28%),
            radial-gradient(circle at 92% 8%, rgba(20,121,211,.10), transparent 24%),
            linear-gradient(180deg, #f7fcff 0%, #ffffff 48%, #f5fbff 100%);
          color: var(--ama-ink);
        }
        [data-testid="stMainBlockContainer"] {
          max-width: 1120px;
          padding-top: 1.1rem;
          padding-bottom: 5rem;
        }
        .amakusa-hero {
          position: relative;
          overflow: hidden;
          padding: 20px 22px;
          margin: 2px 0 14px;
          border: 1px solid rgba(255,255,255,.9);
          border-radius: 26px;
          background: linear-gradient(135deg, #0b6fc5 0%, #35aee1 58%, #7bd5ef 100%);
          box-shadow: 0 12px 34px rgba(18, 112, 184, .22);
          color: white;
        }
        .amakusa-hero:after {
          content: "◌  ◦  ○  ◌";
          position: absolute;
          right: 16px;
          top: 8px;
          font-size: 34px;
          letter-spacing: 5px;
          color: rgba(255,255,255,.25);
        }
        .amakusa-hero-title {
          position: relative; z-index: 1;
          font-size: clamp(26px, 5vw, 40px);
          line-height: 1.1;
          font-weight: 900;
          letter-spacing: .02em;
        }
        .amakusa-hero-sub {
          position: relative; z-index: 1;
          margin-top: 8px;
          font-size: 14px;
          font-weight: 700;
          opacity: .95;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
          border-color: var(--ama-border) !important;
          border-radius: 20px !important;
          background: rgba(255,255,255,.94);
          box-shadow: 0 5px 18px rgba(30, 116, 176, .07);
        }
        div[data-testid="stExpander"] {
          border: 1px solid var(--ama-border);
          border-radius: 16px;
          overflow: hidden;
          background: rgba(255,255,255,.92);
        }
        div[data-testid="stExpander"] summary {
          color: var(--ama-blue-dark);
          font-weight: 800;
        }
        .stButton > button, .stLinkButton > a {
          min-height: 46px;
          border-radius: 14px !important;
          font-weight: 800 !important;
          border-color: #b9ddf5 !important;
        }
        .stButton > button[kind="primary"] {
          background: linear-gradient(135deg, var(--ama-blue-dark), var(--ama-blue)) !important;
          border: none !important;
          box-shadow: 0 7px 16px rgba(11,111,197,.22);
        }
        [data-testid="stNotification"] {
          border-radius: 15px;
        }
        [data-baseweb="tab-list"] {
          gap: 6px;
          overflow-x: auto;
          scrollbar-width: none;
          padding: 4px 2px 8px;
        }
        [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
        [data-baseweb="tab"] {
          flex: 0 0 auto;
          min-height: 42px;
          padding: 8px 13px;
          border-radius: 999px;
          background: #eaf7ff;
          color: #23628f;
          font-weight: 800;
          white-space: nowrap;
        }
        [aria-selected="true"][data-baseweb="tab"] {
          background: linear-gradient(135deg, #dff3ff, #cceeff);
          color: #075aa8;
        }
        [data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {
          border-radius: 13px !important;
          border-color: #cde6f7 !important;
          background: #fbfeff !important;
        }
        [data-testid="stMetric"] {
          background: #f0f9ff;
          border: 1px solid #d7effc;
          border-radius: 16px;
          padding: 10px 12px;
        }
        [data-testid="stImage"] img { border-radius: 16px; }
        iframe { border-radius: 18px !important; }
        h1, h2, h3 { color: #125f9d; }

        @media (max-width: 768px) {
          [data-testid="stMainBlockContainer"] {
            padding: .65rem .72rem 4.5rem;
          }
          .amakusa-hero {
            padding: 18px 16px;
            border-radius: 20px;
            margin-bottom: 10px;
          }
          .amakusa-hero-title { font-size: 28px; }
          .amakusa-hero-sub { font-size: 13px; max-width: 88%; }
          .stButton > button, .stLinkButton > a { min-height: 48px; font-size: 15px; }
          [data-baseweb="tab"] { min-height: 44px; padding: 9px 12px; }
          [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .55rem; }
          [data-testid="column"] { min-width: min(100%, 250px); flex: 1 1 250px !important; }
          h2 { font-size: 1.45rem !important; }
          h3 { font-size: 1.18rem !important; }
          p, .stMarkdown { line-height: 1.7; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_hero() -> None:
    st.markdown(
        """
        <div class="amakusa-hero">
          <div class="amakusa-hero-title">🌊 天草つながりクエスト</div>
          <div class="amakusa-hero-sub">天草をめぐって、見つけて、集める。あなたの旅をクエストにしよう。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


init_state()
apply_charming_blue_theme()
render_app_hero()

render_participant_setup()
if not st.session_state.get("data_loaded", False):
    load_user_data()
    st.session_state.data_loaded = True
    st.session_state.loaded_participant_id = st.session_state.get("participant_id")

render_profile_setup()
render_usage_guide()
render_clear_reward_effect()

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

# マップのポップアップから遷移した時に、タブ選択状態に関係なく該当クエストを表示する。
global_focus_qid = _get_query_param("focus_qid")
if global_focus_qid:
    global_focus_q = get_quest(global_focus_qid)
    if global_focus_q.get("quest_id"):
        st.markdown("## ✨ 選んだクエスト")
        if is_story_quest(global_focus_q) and not story_is_unlocked(global_focus_q):
            render_locked_story_card(global_focus_q, ui_scope=f"global_focus_{global_focus_qid}")
        else:
            quest_card(display_quest_for_list(global_focus_q), show_actions=True, ui_scope=f"global_focus_{global_focus_qid}")
        st.divider()

main_tab, list_tab, story_tab, map_tab, character_tab, summary_tab, survey_tab = st.tabs([
    "🌟 おすすめ", "🗺️ 全クエスト", "📖 ストーリー", "👣 旅日記", "🎁 図鑑", "🎒 旅まとめ", "📝 アンケート"
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
    st.subheader("🔍 全クエスト")
    st.write("地図や条件から、今行きたいクエストを探せます。")
    focused_qid = _get_query_param("focus_qid") or st.session_state.get("map_selected_qid", "")

    with st.expander("🔎 条件で絞り込む", expanded=False):
        filter_row1 = st.columns(2)
        sel_tag = filter_row1[0].selectbox("目的", ["すべて"] + OBJECTIVES)
        sel_area = filter_row1[1].selectbox("エリア", ["すべて", "上天草", "天草", "苓北"])
        filter_row2 = st.columns(2)
        sel_season = filter_row2[0].selectbox("行く時期", SEASONS, index=6)
        kw = filter_row2[1].text_input("キーワード", key="list_kw", placeholder="例：イルカ、海鮮")

    obj_filter = [sel_tag] if sel_tag != "すべて" else []
    area_filter = sel_area if sel_area != "すべて" else "指定なし"

    f_quests = recommend_quests(obj_filter, "まだ決めていない", sel_season, area_filter, kw, include_story=True)

    # 地図のピンをタップすると、選んだクエストを直下に表示する。
    map_selected_qid = render_quest_map(f_quests, map_title="🗺️ 地図から選ぶ")
    if map_selected_qid:
        focused_qid = map_selected_qid

    focused_q = next((q for q in f_quests if q.get("quest_id") == focused_qid), None)
    if focused_q:
        st.markdown("### ✨ 選んだクエスト")
        if is_story_quest(focused_q) and not story_is_unlocked(focused_q):
            render_locked_story_card(focused_q, ui_scope=f"focused_{focused_qid}")
        else:
            quest_card(display_quest_for_list(focused_q), show_actions=True, ui_scope=f"focused_{focused_qid}")
        st.divider()

    st.markdown("### 該当クエスト")
    st.write(f"**該当クエスト： {len(f_quests)} 件**")
    
    for q in f_quests:
        display_q = display_quest_for_list(q)
        expanded = q.get("quest_id") == focused_qid
        with st.expander(f"📍 {display_q.get('quest_name','')} （{display_q.get('area','')} / {display_q.get('quest_type','')}）", expanded=expanded):
            if is_story_quest(q) and not story_is_unlocked(q):
                render_locked_story_card(q, ui_scope=f"list_locked_{q['quest_id']}")
            else:
                quest_card(display_q, show_actions=True, ui_scope=f"list_{q['quest_id']}")

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
            story_phone = quest_phone(sq)
            if story_phone:
                st.markdown(f"**電話番号：** [{story_phone}]({tel_url(story_phone)})")
            render_place_photo(sq, compact=True)
            render_schedule_notice(sq)
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
                    reward_preview = get_character_for_quest(sq)
                    reward_cid = reward_preview.get("character_id", "")
                    was_unlocked = reward_cid in st.session_state.unlocked_character_ids

                    st.session_state.completed.add(sq["quest_id"])
                    if sq["quest_id"] not in st.session_state.completed_at:
                        st.session_state.completed_at[sq["quest_id"]] = datetime.now(timezone.utc).isoformat()
                    st.session_state.story_progress += 1
                    char = award_character_for_quest(sq)
                    apples_awarded = 3
                    st.session_state.apples += apples_awarded
                    save_diary_record(sq, "ストーリーモードでクリアしました！", make_sns_text(sq), "")
                    trigger_clear_effect(sq, char, apples_awarded=apples_awarded, new_character=(not was_unlocked), already_completed=False)
                    save_user_data() # ★ 自動保存
                    st.rerun()

with map_tab: render_footprint_map()

with character_tab: render_character_collection()


with summary_tab:
    st.subheader("🎒 旅のまとめ")
    done = [get_quest(q) for q in st.session_state.completed if get_quest(q).get("quest_id")]
    if not done: st.info("まだ参加記録がありません。")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("参加クエスト", len(done))
        c2.metric("仲間キャラ", len(st.session_state.unlocked_character_ids))
        c3.metric("所持リンゴ", st.session_state.apples)

with survey_tab:
    render_survey()

# 管理機能は通常利用者には見せず、URLに ?admin=1 を付けた時だけ表示する。
if _get_query_param("admin") == "1":
    st.divider()
    with st.expander("⚙️ 管理者用メニュー", expanded=False):
        st.subheader("データ確認・表紙写真の登録")
        st.write("通常クエストとストーリーモードの表紙写真を登録・変更できます。")

        admin_photo_tab, admin_story_photo_tab = st.tabs(
            ["📍 通常クエスト", "📖 ストーリーモード"]
        )

        # -------------------------------------------------------------
        # 通常クエストの表紙写真
        # -------------------------------------------------------------
        with admin_photo_tab:
            st.markdown("### 通常クエストの表紙写真")

            normal_options = {
                f"{q.get('quest_name','')}｜{q.get('linked_name','')}": q
                for q in QUESTS
            }

            normal_label = st.selectbox(
                "写真を登録する通常クエストを選択",
                list(normal_options.keys()),
                key="admin_normal_photo_quest",
            )

            target_q = normal_options.get(normal_label)

            if target_q:
                existing_photo = place_photo_path(target_q["quest_id"])

                if existing_photo:
                    st.image(
                        str(existing_photo),
                        caption=f"現在の表紙写真：{target_q.get('linked_name','')}",
                        width=320,
                    )
                else:
                    st.info("現在、写真は未登録（仮イラスト）です。")

                up_file = st.file_uploader(
                    f"「{target_q.get('quest_name','')}」の新しい写真をアップロード",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"admin_normal_photo_upload_{target_q['quest_id']}",
                )

                if up_file is not None:
                    if st.button(
                        "この写真を通常クエストの表紙に設定",
                        key=f"admin_normal_photo_save_{target_q['quest_id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        save_place_photo(target_q["quest_id"], up_file)
                        st.success("通常クエストの表紙写真を登録しました。")
                        st.rerun()

        # -------------------------------------------------------------
        # ストーリーモードの表紙写真
        # -------------------------------------------------------------
        with admin_story_photo_tab:
            st.markdown("### ストーリーモードの表紙写真")
            st.caption(
                "第1章〜第6章の目的地写真を登録できます。"
                "登録した写真はストーリーモードの各章に表示されます。"
            )

            story_options = {
                f"第{i+1}章｜{q.get('quest_name','')}｜{q.get('linked_name','')}": q
                for i, q in enumerate(STORY_QUESTS)
            }

            story_label = st.selectbox(
                "写真を登録するストーリークエストを選択",
                list(story_options.keys()),
                key="admin_story_photo_quest",
            )

            target_story_q = story_options.get(story_label)

            if target_story_q:
                st.markdown(
                    f"**目的地：** {target_story_q.get('linked_name','')}"
                )

                existing_story_photo = place_photo_path(
                    target_story_q["quest_id"]
                )

                if existing_story_photo:
                    st.image(
                        str(existing_story_photo),
                        caption=(
                            "現在登録されているストーリー表紙写真："
                            f"{target_story_q.get('linked_name','')}"
                        ),
                        width=320,
                    )

                    if st.button(
                        "現在のストーリー表紙写真を削除",
                        key=f"admin_story_photo_delete_{target_story_q['quest_id']}",
                        use_container_width=True,
                    ):
                        for ext in PLACE_PHOTO_EXTS:
                            old_photo = (
                                PLACE_PHOTO_DIR
                                / f"{target_story_q['quest_id']}.{ext}"
                            )
                            if old_photo.exists():
                                old_photo.unlink()

                        st.success(
                            "ストーリーモードの表紙写真を削除しました。"
                        )
                        st.rerun()
                else:
                    st.info(
                        "現在、この章の表紙写真は未登録です。"
                        "登録するまでは仮イラストが表示されます。"
                    )

                story_up_file = st.file_uploader(
                    (
                        f"「{target_story_q.get('quest_name','')}」"
                        "の表紙写真をアップロード"
                    ),
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"admin_story_photo_upload_{target_story_q['quest_id']}",
                )

                if story_up_file is not None:
                    st.image(
                        story_up_file,
                        caption="登録前のプレビュー",
                        width=320,
                    )

                    if st.button(
                        "この写真をストーリーモードの表紙に設定",
                        key=f"admin_story_photo_save_{target_story_q['quest_id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        save_place_photo(
                            target_story_q["quest_id"],
                            story_up_file,
                        )
                        st.success(
                            "ストーリーモードの表紙写真を登録しました。"
                            "各章の画面に反映されます。"
                        )
                        st.rerun()

        st.divider()

        st.download_button(
            "通常クエストDBのCSVダウンロード",
            pd.DataFrame(QUESTS)
            .to_csv(index=False)
            .encode("utf-8-sig"),
            "db.csv",
            "text/csv",
        )

        st.download_button(
            "ストーリークエストDBのCSVダウンロード",
            pd.DataFrame(STORY_QUESTS)
            .to_csv(index=False)
            .encode("utf-8-sig"),
            "story_db.csv",
            "text/csv",
        )
