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
        "quest_type": "ミュージアム",
        "area": "御所浦",
        "season": "通年",
        "period": "通年",
        "stay_fit": "宿泊推奨",
        "connection_level": "知る",
        "tags": ["ミュージアム", "親子で遊ぶ", "自然・海"],
        "description": "御所浦の化石・地質・島の成り立ちを学び、自然と地域の関係に触れるクエスト。",
        "condition": "展示を見て、印象に残った化石を記録する。",
        "official_url": "https://goshouramuseum.jp/",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_dolphin_center",
        "quest_name": "道の駅 天草市イルカセンターでイルカを知る",
        "linked_name": "道の駅 天草市イルカセンター",
        "quest_type": "自然・海",
        "area": "五和",
        "season": "通年",
        "period": "通年",
        "stay_fit": "日帰り可",
        "connection_level": "体験する",
        "tags": ["自然・海", "親子で遊ぶ", "写真"],
        "description": "イルカウォッチングを通じて、天草の豊かな海に触れるクエスト。",
        "condition": "施設を訪れ、知ったことを記録する。",
        "official_url": "https://www.t-island.jp/spot/2837",
        "status": "確認済み",
    },
    {
        "quest_id": "spot_lisola",
        "quest_name": "リゾラテラス天草で海辺の食を楽しむ",
        "linked_name": "リゾラテラス天草",
        "quest_type": "食",
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
        "quest_type": "食",
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
        "quest_type": "食",
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

# ★ 新規追加の30クエスト (各ジャンル3個ずつ)
ADDITIONAL_QUESTS: List[Dict] = [
    {"quest_id": "fes_gokyo", "quest_name": "天草五橋祭を楽しむ", "linked_name": "天草五橋祭", "quest_type": "祭り・イベント", "area": "上天草", "season": "秋", "period": "秋", "stay_fit": "宿泊推奨", "connection_level": "参加する", "tags": ["祭り・イベント", "写真", "地元の人"], "description": "天草五橋の開通を記念するお祭りで、白竜船のパレードや花火を楽しもう。", "condition": "お祭りの様子を記録する", "official_url": "https://kami-amakusa.jp/", "status": "確認済み"},
    {"quest_id": "fes_sakitsu", "quest_name": "崎津みなと祭りで夜空を見上げる", "linked_name": "崎津みなと祭り", "quest_type": "祭り・イベント", "area": "崎津", "season": "夏", "period": "夏", "stay_fit": "宿泊推奨", "connection_level": "参加する", "tags": ["祭り・イベント", "写真", "癒し"], "description": "世界遺産の漁村で打ち上がる美しい花火を堪能しよう。", "condition": "花火や祭りの風景を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "fes_triathlon", "quest_name": "天草国際トライアスロンを応援する", "linked_name": "天草国際トライアスロン", "quest_type": "祭り・イベント", "area": "本渡", "season": "春", "period": "春", "stay_fit": "日帰り可", "connection_level": "参加する", "tags": ["祭り・イベント", "地元の人"], "description": "国内外から集まるアスリートたちを沿道から応援しよう。", "condition": "応援の熱気を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},

    {"quest_id": "hist_gionbashi", "quest_name": "国の重要文化財・祇園橋を渡る", "linked_name": "祇園橋", "quest_type": "歴史・文化", "area": "本渡", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["歴史・文化", "写真"], "description": "国内最大級の石造桁橋である祇園橋を歩き、歴史の重みを感じよう。", "condition": "橋を渡り、風景を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "hist_suzuki", "quest_name": "鈴木神社で天草復興の歴史を知る", "linked_name": "鈴木神社", "quest_type": "歴史・文化", "area": "本渡", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["歴史・文化", "地元の人"], "description": "島原・天草一揆の後に天草を復興させた鈴木重成公を祀る神社を参拝しよう。", "condition": "神社を参拝し、学んだことを記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "hist_sakitsu_suwa", "quest_name": "崎津諏訪神社で信仰の共存を感じる", "linked_name": "崎津諏訪神社", "quest_type": "歴史・文化", "area": "崎津", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["歴史・文化", "写真"], "description": "キリスト教と神道が共存した崎津の歴史を象徴する神社を訪れよう。", "condition": "鳥居越しの教会の風景を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},

    {"quest_id": "mus_collegio", "quest_name": "天草コレジヨ館で西洋文化の伝来を学ぶ", "linked_name": "天草コレジヨ館", "quest_type": "ミュージアム", "area": "苓北", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["ミュージアム", "歴史・文化", "雨でも楽しむ"], "description": "天正遣欧少年使節が持ち帰ったグーテンベルク印刷機などの復元品を見学しよう。", "condition": "展示の感想を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "mus_reihoku_hist", "quest_name": "苓北町歴史資料館で町の成り立ちを知る", "linked_name": "苓北町歴史資料館", "quest_type": "ミュージアム", "area": "苓北", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["ミュージアム", "歴史・文化", "雨でも楽しむ"], "description": "富岡城の歴史や天草西海岸の文化に関する資料を調査しよう。", "condition": "興味深かった展示を記録する", "official_url": "https://kankou.reihoku-kumamoto.jp/", "status": "確認済み"},
    {"quest_id": "mus_sumoto", "quest_name": "栖本歴史民俗資料館で暮らしの歴史に触れる", "linked_name": "栖本歴史民俗資料館", "quest_type": "ミュージアム", "area": "本渡", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["ミュージアム", "歴史・文化", "雨でも楽しむ"], "description": "昔の天草の農具や漁具など、人々の暮らしを支えた道具を見学しよう。", "condition": "昔の暮らしについて感じたことを記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},

    {"quest_id": "food_yakko", "quest_name": "名店「奴寿司」で極上の寿司を味わう", "linked_name": "奴寿司", "quest_type": "食", "area": "本渡", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "食べる", "tags": ["食", "自然・海"], "description": "全国から客が訪れる名店で、天草の新鮮な魚にひと手間加えたお寿司を堪能しよう。", "condition": "食べたお寿司の感想を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "food_tanaka", "quest_name": "たなか畜産で天草黒牛の焼肉を食べる", "linked_name": "たなか畜産", "quest_type": "食", "area": "本渡", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "食べる", "tags": ["食", "地元の人"], "description": "天草で育った最高級の黒毛和牛「天草黒牛」の焼肉をお腹いっぱい食べよう。", "condition": "お肉の美味しさを記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "food_tsuruya", "quest_name": "苓州ツルヤで天草ちゃんぽんをすする", "linked_name": "苓州ツルヤ", "quest_type": "食", "area": "苓北", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "食べる", "tags": ["食", "地元の人"], "description": "三大ちゃんぽんの一つ「天草ちゃんぽん」。海鮮のダシが効いたスープを味わおう。", "condition": "ちゃんぽんの感想を記録する", "official_url": "https://kankou.reihoku-kumamoto.jp/", "status": "確認済み"},

    {"quest_id": "nat_kuradake", "quest_name": "天草最高峰・倉岳からのパノラマを満喫する", "linked_name": "倉岳", "quest_type": "自然・海", "area": "天草", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "体験する", "tags": ["自然・海", "絶景", "写真"], "description": "標高682mの倉岳山頂から、八代海と御所浦の島々を見下ろす絶景を楽しもう。", "condition": "山頂からの景色を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "nat_shiratsuru", "quest_name": "白鶴浜海水浴場で透き通る海を楽しむ", "linked_name": "白鶴浜海水浴場", "quest_type": "自然・海", "area": "天草西海岸・大江", "season": "夏", "period": "夏", "stay_fit": "日帰り可", "connection_level": "体験する", "tags": ["自然・海", "親子で遊ぶ", "癒し"], "description": "白砂が1.3km続く美しいビーチで、海水浴やビーチ散策を満喫しよう。", "condition": "海の透明度や風景を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "nat_myoken", "quest_name": "国指定の名勝・妙見浦のダイナミックな岩礁を見る", "linked_name": "妙見浦", "quest_type": "自然・海", "area": "天草西海岸・大江", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["自然・海", "絶景", "写真"], "description": "荒波に削られた象の形をした奇岩など、西海岸特有のダイナミックな景観を観察しよう。", "condition": "奇岩の風景を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},

    {"quest_id": "craft_maruoyaki", "quest_name": "丸尾焼で天草陶磁器の器に出会う", "linked_name": "丸尾焼", "quest_type": "工芸・ものづくり", "area": "本渡", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る・買う", "tags": ["工芸・ものづくり", "写真"], "description": "天草で最も歴史ある窯元の一つ。日常使いの美しい器を探してみよう。", "condition": "気になった器を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "craft_mizuno", "quest_name": "水の平焼で伝統の海鼠釉（なまこゆう）を見る", "linked_name": "水の平焼", "quest_type": "工芸・ものづくり", "area": "本渡", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る・買う", "tags": ["工芸・ものづくり", "歴史・文化"], "description": "独特の美しい模様を生み出す「海鼠釉」の作品を見学し、天草陶石の魅力を知ろう。", "condition": "陶器の模様の感想を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "craft_takahama", "quest_name": "高浜焼 寿芳窯で白磁の美しさに触れる", "linked_name": "高浜焼 寿芳窯", "quest_type": "工芸・ものづくり", "area": "苓北", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る・買う", "tags": ["工芸・ものづくり", "歴史・文化"], "description": "真っ白で透明感のある「天草陶石」を活かした美しい白磁の器を見学しよう。", "condition": "白磁の美しさを記録する", "official_url": "https://kankou.reihoku-kumamoto.jp/", "status": "確認済み"},

    {"quest_id": "local_salt", "quest_name": "天草の塩づくりを体験して職人と交流する", "linked_name": "天草塩の会", "quest_type": "地元の人", "area": "天草", "season": "通年", "period": "通年", "stay_fit": "宿泊推奨", "connection_level": "体験する", "tags": ["地元の人", "工芸・ものづくり", "食"], "description": "海水を釜で煮詰める昔ながらの塩づくりを見学し、塩の職人さんと交流しよう。", "condition": "塩の味や職人さんの話を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "local_sakitsu_guide", "quest_name": "地元ガイドと歩く崎津集落めぐり", "linked_name": "崎津集落ガイドツアー", "quest_type": "地元の人", "area": "崎津", "season": "通年", "period": "通年", "stay_fit": "宿泊推奨", "connection_level": "参加する", "tags": ["地元の人", "歴史・文化"], "description": "地元に暮らすガイドさんの案内で、崎津集落の路地裏や歴史の裏話を聞きながら歩こう。", "condition": "ガイドさんから聞いた裏話を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "local_kamaboko", "quest_name": "牛深でかまぼこ屋の活気に触れる", "linked_name": "牛深のかまぼこ店めぐり", "quest_type": "地元の人", "area": "牛深", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "買う・食べる", "tags": ["地元の人", "食"], "description": "海産物が豊富な牛深で、アツアツの揚げかまぼこ（ばくだん等）を買いながら地元の人と交流しよう。", "condition": "お店の人との会話や味を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},

    {"quest_id": "play_seadonut", "quest_name": "海中水族館シードーナツで海の生き物と遊ぶ", "linked_name": "海中水族館シードーナツ", "quest_type": "親子で遊ぶ", "area": "上天草", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "体験する", "tags": ["親子で遊ぶ", "自然・海", "雨でも楽しむ"], "description": "海に浮かぶドーナツ型の水族館で、イルカや魚たちと間近でふれあおう。", "condition": "一番面白かった生き物を記録する", "official_url": "https://kami-amakusa.jp/", "status": "確認済み"},
    {"quest_id": "play_pearlgarden", "quest_name": "天草パールガーデンで家族の思い出を作る", "linked_name": "天草パールガーデン", "quest_type": "親子で遊ぶ", "area": "上天草", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "体験する", "tags": ["親子で遊ぶ", "食", "癒し"], "description": "真珠のアクセサリー作り体験や、カフェでのんびりとした家族の時間を過ごそう。", "condition": "体験したことや食べたものを記録する", "official_url": "https://kami-amakusa.jp/", "status": "確認済み"},
    {"quest_id": "play_sup", "quest_name": "波の穏やかな海でSUP（サップ）に挑戦する", "linked_name": "天草SUP体験", "quest_type": "親子で遊ぶ", "area": "上天草", "season": "夏", "period": "夏〜秋", "stay_fit": "日帰り可", "connection_level": "体験する", "tags": ["親子で遊ぶ", "自然・海", "絶景"], "description": "親子で一緒にボードの上に立ち、海の上を散歩するSUPアクティビティに挑戦しよう。", "condition": "SUPの感想や海の様子を記録する", "official_url": "https://kami-amakusa.jp/", "status": "確認済み"},

    {"quest_id": "photo_kuradake_torii", "quest_name": "天空の鳥居で奇跡の一枚を撮る", "linked_name": "倉岳神社の鳥居", "quest_type": "写真", "area": "天草", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["写真", "絶景", "自然・海"], "description": "海と空に浮かぶように建つ倉岳神社の鳥居越しに、素晴らしい写真を撮影しよう。", "condition": "絶景の写真を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "photo_nishihira", "quest_name": "巨大なアコウの木と自然の生命力を撮る", "linked_name": "西平椿公園（アコウの木）", "quest_type": "写真", "area": "天草西海岸・大江", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "知る", "tags": ["写真", "自然・海", "絶景"], "description": "岩を包み込むように根を張る巨大なアコウの木の前で、大自然の生命力を写真に収めよう。", "condition": "アコウの木の迫力を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "photo_shimoda_sunset", "quest_name": "下田の夕陽に染まる海を撮る", "linked_name": "下田の夕陽", "quest_type": "写真", "area": "天草西海岸・大江", "season": "通年", "period": "通年", "stay_fit": "宿泊推奨", "connection_level": "体験する", "tags": ["写真", "絶景", "癒し"], "description": "日本の夕陽百選にも選ばれた、東シナ海に沈む美しい夕陽をカメラに収めよう。", "condition": "夕陽の写真を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},

    {"quest_id": "heal_shimoda_onsen", "quest_name": "下田温泉で旅の疲れを癒やす", "linked_name": "下田温泉", "quest_type": "癒し", "area": "天草西海岸・大江", "season": "通年", "period": "通年", "stay_fit": "宿泊推奨", "connection_level": "休む", "tags": ["癒し", "歴史・文化"], "description": "開湯700年の歴史を持つ天草最古の温泉で、源泉掛け流しの湯に浸かってリラックスしよう。", "condition": "温泉の感想を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"},
    {"quest_id": "heal_matsushima_onsen", "quest_name": "松島温泉で海を眺めながら湯に浸かる", "linked_name": "松島温泉", "quest_type": "癒し", "area": "上天草", "season": "通年", "period": "通年", "stay_fit": "宿泊推奨", "connection_level": "休む", "tags": ["癒し", "絶景", "自然・海"], "description": "日本の夕陽百選に選ばれた松島の海を眺めながら、美肌の湯と呼ばれる温泉で癒されよう。", "condition": "温泉と景色の感想を記録する", "official_url": "https://kami-amakusa.jp/", "status": "確認済み"},
    {"quest_id": "heal_perla", "quest_name": "ペルラの湯舟で有明海を一望する", "linked_name": "ペルラの湯舟", "quest_type": "癒し", "area": "本渡", "season": "通年", "period": "通年", "stay_fit": "日帰り可", "connection_level": "休む", "tags": ["癒し", "絶景"], "description": "「海の湯」「山の湯」などの露天風呂から、有明海の大パノラマを眺めてリフレッシュしよう。", "condition": "露天風呂からの景色を記録する", "official_url": "https://www.t-island.jp/", "status": "確認済み"}
]
QUESTS.extend(ADDITIONAL_QUESTS)

OBJECTIVES = [
    "祭り・イベント", "歴史・文化", "ミュージアム", "食", "自然・海",
    "工芸・ものづくり", "地元の人", "親子で遊ぶ", "写真", "癒し", "特になし"
]
STAY_OPTIONS = ["日帰り", "宿泊", "まだ決めていない"]
SEASONS = ["今日・今週", "春", "夏", "秋", "冬", "通年", "日程未定"]
AREAS = ["指定なし"] + sorted(list(set(q["area"] for q in QUESTS if q.get("quest_type") != "ストーリー")))

QUEST_COORDS: Dict[str, Tuple[float, float]] = {
    # -----------------------------
    # 既存・主要クエスト
    # -----------------------------
    "event_ushibuka_haiya_2026": (32.198000, 130.025400),
    "event_hondo_haiya_2025": (32.458700, 130.191900),
    "spot_goshoura_museum": (32.319700, 130.327800),
    "spot_dolphin_center": (32.558200, 130.169600),
    "spot_lisola": (32.527691, 130.426280),
    "food_sun_haraippai_amakusa_daio": (32.528347, 130.426949),
    "food_fukuzumi_kaisendon": (32.518682, 130.422624),

    # -----------------------------
    # 追加クエスト：祭り・イベント
    # -----------------------------
    "fes_gokyo": (32.528347, 130.426949),
    "fes_sakitsu": (32.315400, 130.026400),
    "fes_triathlon": (32.477000, 130.194000),

    # -----------------------------
    # 追加クエスト：歴史・文化
    # -----------------------------
    "hist_gionbashi": (32.456367, 130.188060),
    "hist_suzuki": (32.465944, 130.129751),
    "hist_sakitsu_suwa": (32.315000, 130.027000),

    # -----------------------------
    # 追加クエスト：ミュージアム
    # -----------------------------
    "mus_collegio": (32.315165, 130.081998),
    "mus_reihoku_hist": (32.530673, 130.032076),
    "mus_sumoto": (32.460822, 130.198703),

    # -----------------------------
    # 追加クエスト：食
    # -----------------------------
    "food_yakko": (32.450294, 130.201396),
    "food_tanaka": (32.495055, 130.147205),
    "food_tsuruya": (32.450900, 130.201800),

    # -----------------------------
    # 追加クエスト：自然・海
    # -----------------------------
    "nat_kuradake": (32.407000, 130.336000),
    "nat_shiratsuru": (32.379249, 129.995180),
    "nat_myoken": (32.396209, 129.997767),

    # -----------------------------
    # 追加クエスト：工芸・ものづくり
    # -----------------------------
    "craft_maruoyaki": (32.464504, 130.187494),
    "craft_mizuno": (32.472431, 130.175638),
    "craft_takahama": (32.374751, 129.997038),

    # -----------------------------
    # 追加クエスト：地元の人
    # -----------------------------
    "local_salt": (32.333681, 129.992822),
    "local_sakitsu_guide": (32.315400, 130.026400),
    "local_kamaboko": (32.198000, 130.025400),

    # -----------------------------
    # 追加クエスト：親子で遊ぶ
    # -----------------------------
    "play_seadonut": (32.528347, 130.426949),
    "play_pearlgarden": (32.528347, 130.426949),
    "play_sup": (32.527691, 130.426280),

    # -----------------------------
    # 追加クエスト：写真
    # -----------------------------
    "photo_kuradake_torii": (32.407000, 130.336000),
    "photo_nishihira": (32.347558, 129.979153),
    "photo_shimoda_sunset": (32.424921, 130.011144),

    # -----------------------------
    # 追加クエスト：癒し
    # -----------------------------
    "heal_shimoda_onsen": (32.424921, 130.011144),
    "heal_matsushima_onsen": (32.518143, 130.426588),
    "heal_perla": (32.476000, 130.202000),

    # -----------------------------
    # ストーリーモード
    # -----------------------------
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
    "event_ushibuka_haiya_2026": "shirasui",
    "event_hondo_haiya_2025": "hoshimi",
    "spot_dolphin_center": "irukacchi",
    "spot_lisola": "kairun",
    "fes_gokyo": "shirasui",
    "hist_gionbashi": "amanya",
    "mus_collegio": "amanya",
    "food_yakko": "kairun",
    "nat_kuradake": "irukacchi",
    "craft_maruoyaki": "amanya",
    "local_salt": "kairun",
    "play_seadonut": "irukacchi",
    "photo_kuradake_torii": "hoshimi",
    "heal_shimoda_onsen": "amanya",
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
    return char

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
# ★ 安全装置対応：絶対エラーで落ちない get_quest() ★
# -----------------------------
def get_quest(quest_id: str) -> Dict:
    """万が一クエストIDが消えていても、空の辞書を返してアプリの停止（StopIteration）を防ぐ"""
    return next((q for q in QUESTS if q.get("quest_id") == quest_id), {})


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
        "photo_capture_open": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # ★ 究極のセーフティガード：存在しないクエスト（幽霊データ）の記憶を起動時に完全に消去する
    valid_qids = {q.get("quest_id") for q in QUESTS if q.get("quest_id")}
    st.session_state.completed = {qid for qid in st.session_state.completed if qid in valid_qids}
    st.session_state.completed_order = [qid for qid in st.session_state.completed_order if qid in valid_qids]
    st.session_state.favorites = {qid for qid in st.session_state.favorites if qid in valid_qids}


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

def parse_objective_text(text: str, existing: Optional[List[str]] = None, max_items: int = 3) -> List[str]:
    items: List[str] = list(existing or [])
    for token in re.split(r"[、,，/／\s]+", str(text)):
        token = token.strip()
        if token and token not in items:
            items.append(token)
        if len(items) >= max_items: break
    return items[:max_items]

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

        # 完全一致なら最も強く評価。
        if term_norm in tag_texts:
            score += 5
        # 部分一致も評価する。例：「海」→「自然・海」、「歴史」→「歴史・文化」。
        elif any(term_norm in tag_text or tag_text in term_norm for tag_text in tag_texts):
            score += 3
        # タグにない場合でも、クエスト名・説明文に含まれていれば評価する。
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
    """カメラ撮影・フォルダ選択のどちらからでも、クリア判定用写真として保存する。"""
    if not qid or uploaded_file is None:
        return
    st.session_state.photos[qid] = getattr(uploaded_file, "name", "camera_photo.jpg") or "camera_photo.jpg"
    st.session_state.photo_data[qid] = uploaded_file.getvalue()
    st.session_state.photo_mime[qid] = getattr(uploaded_file, "type", None) or "image/jpeg"


def has_clear_photo(q: Dict) -> bool:
    qid = q.get("quest_id", "")
    return bool(qid and st.session_state.photo_data.get(qid))


def render_photo_clear_panel(q: Dict, ui_scope: str = "quest") -> bool:
    """GPSに加えて必要な、写真によるクリア確認UI。写真がある時だけTrueを返す。"""
    qid = q.get("quest_id", "")
    if not qid:
        return False

    st.markdown("#### 📸 写真によるクリア確認")
    st.caption("クリア条件：GPS判定OKに加えて、現地で撮った写真、または写真フォルダから選んだ写真の添付が必要です。")

    if has_clear_photo(q):
        st.success("写真確認OK：クリア用写真が添付されています。")
        st.image(st.session_state.photo_data[qid], caption="クリア用写真", width=320)
        if st.button("写真を撮り直す・選び直す", key=f"{ui_scope}_reset_clear_photo_{qid}", use_container_width=True):
            st.session_state.photos.pop(qid, None)
            st.session_state.photo_data.pop(qid, None)
            st.session_state.photo_mime.pop(qid, None)
            st.session_state.photo_capture_open.add(qid)
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
    """クエストマップのピンを押したときに表示するHTML。"""
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
    """全クエストを地図上に表示する。現在地があれば青ピンで表示する。"""
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

    # 天草全体が見える中心位置
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
                if q["quest_id"] not in st.session_state.completed_order: st.session_state.completed_order.append(q["quest_id"])
                
                char = award_character_for_quest(q)
                save_diary_record(q, st.session_state.notes.get(q["quest_id"], ""), st.session_state.sns_texts.get(q["quest_id"], make_sns_text(q)), st.session_state.x_post_urls.get(q["quest_id"], ""))
                
                st.session_state.apples += 2
                
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


# =====================================================================
# ★ UI構築（サイドバー廃止、画面上部へ移動）
# =====================================================================
st.set_page_config(page_title="天草つながりクエスト", page_icon="🌊", layout="wide")
init_state()

st.title("🌊 天草つながりクエスト")
st.caption("実在する天草の施設・祭り・地域イベントだけをクエスト化するプロトタイプ")

col_log, col_prog = st.columns([1, 1])
with col_log:
    today_str = date.today().isoformat()
    if st.session_state.last_login_date != today_str:
        if st.button("🎁 今日のログインボーナス：🍎 リンゴを3個もらう", use_container_width=True):
            st.session_state.apples += 3
            st.session_state.last_login_date = today_str
            st.rerun()
    else:
        st.success(f"🎁 本日受取済み！ 所持リンゴ: {st.session_state.apples}個")

with col_prog:
    total_q = len([q for q in QUESTS if q.get("quest_type") != "ストーリー"])
    # 幽霊クエストを排除してカウント
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
                    st.session_state.story_progress += 1
                    char = award_character_for_quest(sq)
                    st.session_state.apples += 3
                    save_diary_record(sq, "ストーリーモードでクリアしました！", make_sns_text(sq), "")
                    st.success(f"クエストクリア！ {char.get('emoji','')} {char.get('name','')} が仲間になり、次のクエストが解放されました！")
                    st.balloons()
                    st.rerun()

with map_tab: render_footprint_map()

with character_tab: render_character_collection()

with gps_tab:
    render_quest_map()

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