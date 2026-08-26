# -*- coding: utf-8 -*-
"""天草つながりクエスト / Streamlit テストマーケティング版"""
from __future__ import annotations

import base64
import html
import json
import math
import re
import urllib.parse
import uuid
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

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

BASE_DIR = Path(__file__).resolve().parent
SAVE_FILE = BASE_DIR / "save_data.json"
PLACE_PHOTO_DIR = BASE_DIR / "quest_place_photos"
CHARACTER_IMAGE_DIR = BASE_DIR / "character_images"
STORY_ASSET_DIR = BASE_DIR / "story_assets"
IMG_EXTS = ["jpg", "jpeg", "png", "webp", "JPG", "JPEG", "PNG", "WEBP"]
APP_STATE_QUEST_ID = "__app_state__"
SURVEY_QUEST_ID = "__survey__"
PUBLIC_DIARY_PREFIX = "__public_diary__::"
CUSTOM_DIARY_PREFIX = "__custom_diary__::"

AGE_OPTIONS = ["選択してください", "10代", "20代", "30代", "40代", "50代", "60代", "70代以上"]
FEATURE_SURVEY_ITEMS = [
    "おすすめクエスト", "全クエスト・検索", "クエストマップ", "GPS・写真でのクエストクリア",
    "ストーリーモード", "キャラクター収集", "キャラクター育成", "旅日記・足跡マップ",
    "旅のまとめ", "ログインボーナス",
]
FEATURE_RATING_OPTIONS = ["使っていない", "1：とても不満", "2：やや不満", "3：どちらともいえない", "4：満足", "5：とても満足"]

# =====================================================================
# クエストデータ
# =====================================================================
STORY_QUESTS: List[Dict] = [
    dict(quest_id="story_1_shiro", quest_name="天草四郎との出会い", linked_name="天草四郎ミュージアム", quest_type="ストーリー", area="上天草", season="通年", period="通年", stay_fit="日帰り可", connection_level="知る", tags=["歴史・文化", "ストーリー", "ミュージアム"], description="天草四郎ゆかりの地をめぐる旅が今、始まる。まずはミュージアムで四郎の生い立ちを学ぼう。", condition="天草四郎ミュージアムを訪れる", official_url="https://www.t-island.jp/spot/137", trivia="【プチ情報】島原・天草一揆の歴史や天草四郎について学べる施設です。"),
    dict(quest_id="story_2_senganzan", quest_name="絶景の山で仲間を集めろ", linked_name="千巌山", quest_type="ストーリー", area="上天草", season="通年", period="通年", stay_fit="日帰り可", connection_level="知る", tags=["自然・海", "ストーリー", "絶景"], description="かつて天草四郎が陣を敷いたとされる山。山頂からの絶景の中で仲間を集めよう。", condition="千巌山を訪れる", official_url="https://www.t-island.jp/spot/45", trivia="【プチ情報】山頂から天草五橋や島々を見渡せます。"),
    dict(quest_id="story_3_ueno", quest_name="天草大王コロッケで腹ごしらえ", linked_name="ファミリーショップうえの", quest_type="ストーリー", area="上天草", season="通年", period="通年", stay_fit="日帰り可", connection_level="食べる", tags=["食", "ストーリー", "地元の人"], description="長旅の腹ごしらえに、地元で愛される天草大王コロッケを味わおう。", condition="ファミリーショップうえのを訪れ、コロッケを味わう", official_url="https://www.t-island.jp/", trivia="【プチ情報】天草大王は国内最大級の地鶏として知られています。"),
    dict(quest_id="story_4_kirishitan", quest_name="奇跡の旗を探し出せ", linked_name="天草キリシタン館", quest_type="ストーリー", area="本渡", season="通年", period="通年", stay_fit="日帰り可", connection_level="知る", tags=["歴史・文化", "ストーリー", "ミュージアム"], description="天草のキリシタン史をたどり、一揆軍が掲げた陣中旗の歴史に触れよう。", condition="天草キリシタン館を訪れる", official_url="https://www.t-island.jp/spot/3", trivia="【プチ情報】国指定重要文化財の天草四郎陣中旗が収蔵されています。"),
    dict(quest_id="story_5_tomioka", quest_name="難攻不落の城を調査せよ", linked_name="富岡城跡", quest_type="ストーリー", area="苓北", season="通年", period="通年", stay_fit="日帰り可", connection_level="知る", tags=["歴史・文化", "ストーリー", "絶景"], description="一揆軍が攻撃しても落とすことができなかった堅固な富岡城の跡地を調査しよう。", condition="富岡城跡を訪れる", official_url="https://kankou.reihoku-kumamoto.jp/list00417.html", trivia="【プチ情報】島原・天草一揆の際に一揆軍の攻撃を受けた城です。"),
    dict(quest_id="story_6_sakitsu", quest_name="平和な街へたどり着け", linked_name="崎津集落", quest_type="ストーリー", area="崎津", season="通年", period="通年", stay_fit="宿泊推奨", connection_level="知る", tags=["歴史・文化", "ストーリー", "写真"], description="潜伏キリシタンの歴史と、美しい漁村の風景を目に焼き付けよう。", condition="崎津集落を訪れる", official_url="https://www.t-island.jp/spot/2754", trivia="【プチ情報】世界文化遺産『長崎と天草地方の潜伏キリシタン関連遺産』の構成資産です。"),
]

QUESTS: List[Dict] = [
    dict(quest_id="spot_fukuzumi", quest_name="いけす料理ふくずみで海鮮を味わう", linked_name="いけす料理 ふくずみ", quest_type="食", area="上天草", season="通年", period="通年", stay_fit="日帰り可", connection_level="食べる", tags=["食", "自然・海"], description="いけす料理で新鮮な海鮮丼や海の幸を味わおう。", condition="店舗を訪れ、海鮮料理を食べ感想を記録する", official_url="https://kami-amakusa.jp/"),
    dict(quest_id="spot_hamankura", quest_name="浜崎鮮魚 浜んくらで豪快な魚料理を食べる", linked_name="浜崎鮮魚 浜んくら", quest_type="食", area="上天草", season="通年", period="通年", stay_fit="日帰り可", connection_level="食べる", tags=["食", "自然・海"], description="鮮魚店直営の食事処で、天草の新鮮な魚介を使った料理を楽しもう。", condition="店舗を訪れ、料理の感想を記録する", official_url="https://kami-amakusa.jp/"),
    dict(quest_id="spot_ikoi", quest_name="いこい食堂で天草ちゃんぽんをすする", linked_name="いこい食堂", quest_type="食", area="苓北", season="通年", period="通年", stay_fit="日帰り可", connection_level="食べる", tags=["食", "地元の人"], description="地元で愛されるいこい食堂で、天草ちゃんぽんを味わおう。", condition="ちゃんぽんを食べ、味の感想を記録する", official_url="https://kankou.reihoku-kumamoto.jp/"),
    dict(quest_id="spot_lisola", quest_name="リゾラテラス天草で塩パンと絶景を楽しむ", linked_name="リゾラテラス天草", quest_type="食", area="上天草", season="通年", period="通年", stay_fit="日帰り可", connection_level="食べる・買う", tags=["食", "自然・海", "絶景", "癒し"], description="海辺のリゾート施設で塩パンと海の景色を楽しもう。", condition="塩パンを買い、景色の感想を記録する", official_url="https://www.seacruise.jp/lisolaterrace/"),
    dict(quest_id="play_seadonut", quest_name="海中水族館シードーナツで海の生き物と遊ぶ", linked_name="海中水族館シードーナツ", quest_type="親子で遊ぶ", area="上天草", season="通年", period="通年", stay_fit="日帰り可", connection_level="体験する", tags=["親子で遊ぶ", "自然・海", "ミュージアム"], description="海に浮かぶ水族館で、海の生き物たちとふれあおう。", condition="一番面白かった生き物を記録する", official_url="https://kami-amakusa.jp/"),
    dict(quest_id="nat_oppai", quest_name="おっぱい岩の不思議な形を見る", linked_name="おっぱい岩", quest_type="自然・海", area="苓北", season="通年", period="干潮時", stay_fit="日帰り可", connection_level="知る", tags=["自然・海", "写真", "絶景"], description="干潮時に姿を現すユニークな奇岩を見に行こう。", condition="岩の形を確認し、写真を記録する", official_url="https://kankou.reihoku-kumamoto.jp/"),
    dict(quest_id="photo_kuradake", quest_name="倉岳神社の天空の鳥居から絶景を撮る", linked_name="倉岳神社", quest_type="写真", area="天草", season="通年", period="通年", stay_fit="日帰り可", connection_level="知る", tags=["写真", "絶景", "自然・海"], description="山頂の鳥居越しに天草のパノラマ絶景を撮影しよう。", condition="山頂からの景色を記録する", official_url="https://www.t-island.jp/"),
    dict(quest_id="photo_nishihira", quest_name="西平椿公園でラピュタの木に驚く", linked_name="西平椿公園（ラピュタの木）", quest_type="写真", area="天草西海岸・大江", season="通年", period="通年", stay_fit="日帰り可", connection_level="知る", tags=["写真", "自然・海", "絶景"], description="巨大なアコウの木の生命力を感じよう。", condition="木の迫力について感想を記録する", official_url="https://www.t-island.jp/"),
    dict(quest_id="food_aosa", quest_name="大漁食堂あおさで新鮮な海鮮を堪能する", linked_name="大漁食堂 あおさ", quest_type="食", area="牛深", season="通年", period="通年", stay_fit="日帰り可", connection_level="食べる", tags=["食", "自然・海"], description="牛深で新鮮な海鮮料理を堪能しよう。", condition="海鮮料理を食べ、感想を記録する", official_url="https://kaisaikan.com/restaurant/"),
    dict(quest_id="food_kura", quest_name="天草海鮮蔵でてんこ盛り丼を食らう", linked_name="天草海鮮 蔵", quest_type="食", area="五和", season="通年", period="通年", stay_fit="日帰り可", connection_level="食べる", tags=["食", "自然・海", "地元の人"], description="五和町の海鮮蔵で天草の海の幸を楽しもう。", condition="料理を食べ、味の感想を記録する", official_url="https://kaisenkura.com/"),
    dict(quest_id="event_ushibuka", quest_name="牛深ハイヤ祭りの熱気を感じる", linked_name="牛深ハイヤ祭り", quest_type="祭り・イベント", area="牛深", season="春", period="春", stay_fit="宿泊推奨", connection_level="参加する", tags=["祭り・イベント", "歴史・文化", "地元の人"], description="牛深ハイヤ祭りでハイヤ節と踊りの熱気を感じよう。", condition="祭りの様子や踊りの感想を記録する", official_url="https://www.t-island.jp/event/2400"),
    dict(quest_id="event_hanashobu", quest_name="天草花しょうぶ祭りで満開の花を愛でる", linked_name="天草花しょうぶ祭り（西の久保公園）", quest_type="祭り・イベント", area="本渡", season="春", period="春〜初夏", stay_fit="日帰り可", connection_level="参加する", tags=["祭り・イベント", "自然・海", "写真"], description="西の久保公園で花菖蒲とイベントを楽しもう。", condition="花の風景やイベントの感想を記録する", official_url="https://www.t-island.jp/"),
    dict(quest_id="event_hondo", quest_name="天草ほんどハイヤ祭りで夜の熱気を体験する", linked_name="天草ほんどハイヤ祭り", quest_type="祭り・イベント", area="本渡", season="夏", period="夏", stay_fit="宿泊推奨", connection_level="参加する", tags=["祭り・イベント", "食", "地元の人"], description="本渡の夏の夜を彩るハイヤ祭りを楽しもう。", condition="お祭りの体験を記録する", official_url="https://www.t-island.jp/event/2349"),
    dict(quest_id="play_oninoshiro", quest_name="鬼の城公園で展望塔から絶景を見る", linked_name="鬼の城公園", quest_type="親子で遊ぶ", area="五和", season="通年", period="通年", stay_fit="日帰り可", connection_level="知る", tags=["親子で遊ぶ", "自然・海", "絶景"], description="鬼の伝説が残る公園で展望塔から海峡を見渡そう。", condition="展望塔からの景色や公園の感想を記録する", official_url="https://www.t-island.jp/spot/58"),
    dict(quest_id="craft_unshu", quest_name="雲舟窯で温かみのある天草陶磁器に出会う", linked_name="雲舟窯", quest_type="工芸・ものづくり", area="苓北", season="通年", period="通年", stay_fit="日帰り可", connection_level="知る・買う", tags=["工芸・ものづくり", "写真"], description="苓北町の窯元を訪れ、天草陶磁器の魅力に触れよう。", condition="気になった器や窯元の雰囲気を記録する", official_url="https://amakusatoujiki.com/kamamoto/unsyuugama"),
    dict(quest_id="spot_dolphin", quest_name="イルカセンターで野生のイルカを知る", linked_name="道の駅 天草市イルカセンター", quest_type="自然・海", area="五和", season="通年", period="通年", stay_fit="日帰り可", connection_level="体験する", tags=["自然・海", "親子で遊ぶ", "写真"], description="イルカセンターを訪れ、早崎海峡に暮らすイルカについて知ろう。", condition="イルカや海についての感想を記録する", official_url="https://www.t-island.jp/spot/2837"),
]

OBJECTIVES = ["祭り、イベント", "歴史、文化、ミュージアム", "食", "自然、海", "体験、工芸、ものづくり"]
SEASONS = ["今日・今週", "春", "夏", "秋", "冬", "通年", "日程未定"]
PURPOSE_GROUP_QUEST_IDS = {
    "祭り、イベント": ["event_hondo", "event_ushibuka", "event_hanashobu"],
    "歴史、文化、ミュージアム": ["story_1_shiro", "story_4_kirishitan", "story_5_tomioka"],
    "食": ["spot_fukuzumi", "spot_hamankura", "spot_ikoi", "spot_lisola", "food_kura", "food_aosa", "story_3_ueno"],
    "自然、海": ["play_seadonut", "nat_oppai", "photo_kuradake", "photo_nishihira", "play_oninoshiro", "story_2_senganzan", "story_6_sakitsu"],
    "体験、工芸、ものづくり": ["craft_unshu", "spot_dolphin"],
}
AREA_GROUP_QUEST_IDS = {
    "上天草": ["spot_fukuzumi", "spot_hamankura", "spot_lisola", "play_seadonut", "story_1_shiro", "story_2_senganzan", "story_3_ueno"],
    "天草": ["event_hondo", "photo_kuradake", "photo_nishihira", "food_aosa", "food_kura", "event_ushibuka", "event_hanashobu", "play_oninoshiro", "spot_dolphin", "story_4_kirishitan", "story_6_sakitsu"],
    "苓北": ["spot_ikoi", "nat_oppai", "craft_unshu", "story_5_tomioka"],
}
QUEST_ID_TO_PURPOSE = {qid: p for p, ids in PURPOSE_GROUP_QUEST_IDS.items() for qid in ids}
QUEST_ID_TO_AREA = {qid: a for a, ids in AREA_GROUP_QUEST_IDS.items() for qid in ids}
STORY_QUEST_ORDER = {q["quest_id"]: i + 1 for i, q in enumerate(STORY_QUESTS)}

QUEST_COORDS = {
    "event_hondo": (32.4556566, 130.199987), "spot_fukuzumi": (32.5188852015741, 130.422679537183),
    "spot_hamankura": (32.5481646571749, 130.421738907566), "spot_ikoi": (32.524330828054, 130.033959225541),
    "spot_lisola": (32.5276741360745, 130.42622494288), "play_seadonut": (32.5298923684305, 130.42834666602),
    "nat_oppai": (32.5404691864404, 130.11210456602), "photo_kuradake": (32.4278836342759, 130.327333059979),
    "photo_nishihira": (32.3475201478057, 129.978735082671), "food_aosa": (32.1940616800265, 130.027649879495),
    "food_kura": (32.5496148153241, 130.167306337185), "event_ushibuka": (32.1967404084772, 130.026386830685),
    "event_hanashobu": (32.4675531230178, 130.171460442328), "play_oninoshiro": (32.5046979770165, 130.16423590639),
    "craft_unshu": (32.5193809395413, 130.035016163127), "spot_dolphin": (32.5457113115041, 130.130597437849),
    "story_1_shiro": (32.575919182804, 130.421189844898), "story_2_senganzan": (32.5131997358584, 130.419315860399),
    "story_3_ueno": (32.5181662627699, 130.453448537183), "story_4_kirishitan": (32.4601451315796, 130.184069279509),
    "story_5_tomioka": (32.5294112782553, 130.031524608348), "story_6_sakitsu": (32.3120676064363, 130.025899539258),
}

SCHEDULES = {
    "event_hondo": ("7/25、7/26、8/1（2026年度）", "ー"), "spot_fukuzumi": ("11:00-14:30、17:00-19:30", "毎週水曜日"),
    "spot_hamankura": ("11:00-23:00", "不定休"), "spot_ikoi": ("11:00-13:30", "土・日曜日"),
    "spot_lisola": ("平日9:00-17:30、土日祝9:00-18:00", "なし"), "play_seadonut": ("3/20~10/19 9:00-18:00、10/20~3/19 9:00-17:00", "なし"),
    "food_aosa": ("11:00-15:00、17:00-21:00", "なし"), "food_kura": ("11:00-16:00", "不定休"),
    "event_ushibuka": ("4/17、4/18、4/19（2026年度）", "ー"), "event_hanashobu": ("6/6、6/7（2026年度）", "ー"),
    "craft_unshu": ("10:00-17:00", "不定休"), "spot_dolphin": ("3~10月 9:00-18:00、11~2月 9:00-17:00", "毎月第2・4水曜日、年末年始"),
    "story_1_shiro": ("9:00-17:00", "12/29~1/1、1・6月の第2水曜日"), "story_3_ueno": ("9:00-18:00", "日曜日"),
    "story_4_kirishitan": ("9:00-17:00", "火曜日"),
}
for q in QUESTS + STORY_QUESTS:
    if q["quest_id"] in SCHEDULES:
        q["time_info"], q["closed_days"] = SCHEDULES[q["quest_id"]]
        if "2026年度" in q["time_info"]:
            q["period"] = q["time_info"]

# =====================================================================
# キャラクター
# =====================================================================
def two_stage(cid, n1, n2, emoji, rarity="ノーマル", series="天草"):
    return {"rarity": rarity, "series": series, "stages": [
        {"name": n1, "emoji": emoji, "catch": "天草の魅力から生まれた仲間！", "img_id": f"{cid}①"},
        {"name": n2, "emoji": emoji, "catch": "旅の思い出とリンゴの力で進化した姿！", "img_id": f"{cid}②"},
    ]}

CHARACTERS = {
    "basic_char_hukuzumi": two_stage("basic_char_hukuzumi", "ふくずみの海鮮っ子", "ふくずみ海鮮大将", "🐟", series="食・海鮮"),
    "basic_char_hamankura": two_stage("basic_char_hamankura", "浜んくら魚っ子", "浜んくら鮮魚大将", "🐟", series="食・鮮魚"),
    "basic_char_ikoi_shokudou": two_stage("basic_char_ikoi_shokudou", "いこいちゃんぽん", "いこいちゃんぽん大将", "🍜", series="食・ちゃんぽん"),
    "basic_char_rizoraterasu": two_stage("basic_char_rizoraterasu", "リゾラしおパン", "リゾラテラスの光パン", "🥐", series="食・リゾート"),
    "basic_char_si-do-natsu": two_stage("basic_char_si-do-natsu", "シードナッツ", "シードーナツ海王", "🐬", "レア", "自然・水族館"),
    "basic_char_oppaiiwa": two_stage("basic_char_oppaiiwa", "おっぱい岩ころん", "おっぱい岩まもりん", "🪨", series="自然・奇岩"),
    "basic_char_kuratake_jinja": two_stage("basic_char_kuratake_jinja", "倉岳とりい丸", "倉岳天空守", "⛩️", "レア", "自然・神社"),
    "basic_nishihiratsubaki": two_stage("basic_nishihiratsubaki", "椿のラピュタっ子", "西平椿の森守", "🌳", "レア", "自然・公園"),
    "basic_char_aosa": two_stage("basic_char_aosa", "あおさ丸", "大漁あおさ大将", "🍚", series="食・海鮮食堂"),
    "basic_char_kaisen_kura": two_stage("basic_char_kaisen_kura", "海鮮蔵うにころ", "海鮮蔵てんこ盛り王", "🦐", "レア", "食・海鮮"),
    "basic_char_usibuka_haiyamatsuri": two_stage("basic_char_usibuka_haiyamatsuri", "牛深ハイヤっ子", "牛深ハイヤ舞将", "🎆", "レア", "祭り・ハイヤ"),
    "basic_char_hanasyobumatsuri": two_stage("basic_char_hanasyobumatsuri", "花しょうぶのしずく", "花しょうぶ姫", "🌸", series="祭り・花"),
    "basic_char_hondo_haiyamatsuri": two_stage("basic_char_hondo_haiyamatsuri", "ほんどハイヤっ子", "ほんどハイヤ大踊り", "🎇", "レア", "祭り・ハイヤ"),
    "basic_char_oninoshiro_koen": two_stage("basic_char_oninoshiro_koen", "鬼の城こおに", "鬼の城展望鬼", "👹", series="自然・公園"),
    "basic_char_unsyukkama": two_stage("basic_char_unsyukkama", "雲舟こだぬき", "雲舟陶芸守", "🏺", series="工芸・陶磁器"),
    "basic_char_iruka_senta": two_stage("basic_char_iruka_senta", "イルカセンターっち", "イルカセンター海翔", "🐬", "レア", "体験・イルカ"),
}
for cid, names, emoji, rarity, series in [
    ("story_char_amakusa_siro", ["天草四郎（志士）", "天草四郎・覚醒", "天草四郎・聖将大天草"], "⚔️", "スーパーレア", "ストーリー・歴史"),
    ("story_char_senganzan", ["千巌まる", "千巌大権現", "千巌・銀河龍神"], "⛰️", "レア", "ストーリー・自然"),
    ("story_char_amakusa_daio", ["天草大王", "天草大王・覚醒", "天草大王・極"], "🐔", "ウルトラレア", "ストーリー・食"),
    ("story_char_maria_kannon", ["マリア観音", "聖母マリア・覚醒", "聖母マリア・星核創世神"], "🕊️", "スーパーレア", "ストーリー・祈り"),
    ("story_char_tomiokajo", ["とみっち", "とみまる", "富岡城・守護大将"], "🏯", "レア", "ストーリー・城郭"),
    ("story_char_sakitsu_syuraku", ["ピースピヨ", "オリーブ鳩", "聖愛の平和神鳩"], "🕊️", "スーパーレア", "ストーリー・平和"),
]:
    CHARACTERS[cid] = {"rarity": rarity, "series": series, "stages": [
        {"name": n, "emoji": emoji, "catch": "ストーリーを進めて出会った特別な仲間！", "img_id": f"{cid}{mark}"}
        for n, mark in zip(names, ["①", "②", "③"])
    ]}

QUEST_CHARACTER_REWARDS = {
    "spot_fukuzumi": "basic_char_hukuzumi", "spot_hamankura": "basic_char_hamankura", "spot_ikoi": "basic_char_ikoi_shokudou",
    "spot_lisola": "basic_char_rizoraterasu", "play_seadonut": "basic_char_si-do-natsu", "nat_oppai": "basic_char_oppaiiwa",
    "photo_kuradake": "basic_char_kuratake_jinja", "photo_nishihira": "basic_nishihiratsubaki", "food_aosa": "basic_char_aosa",
    "food_kura": "basic_char_kaisen_kura", "event_ushibuka": "basic_char_usibuka_haiyamatsuri", "event_hanashobu": "basic_char_hanasyobumatsuri",
    "event_hondo": "basic_char_hondo_haiyamatsuri", "play_oninoshiro": "basic_char_oninoshiro_koen", "craft_unshu": "basic_char_unsyukkama",
    "spot_dolphin": "basic_char_iruka_senta", "story_1_shiro": "story_char_amakusa_siro", "story_2_senganzan": "story_char_senganzan",
    "story_3_ueno": "story_char_amakusa_daio", "story_4_kirishitan": "story_char_maria_kannon", "story_5_tomioka": "story_char_tomiokajo",
    "story_6_sakitsu": "story_char_sakitsu_syuraku",
}

# =====================================================================
# 状態・保存
# =====================================================================
def safe_secret(name, default=""):
    try: return str(st.secrets.get(name, default)).strip()
    except Exception: return default

def jp_now():
    try: return datetime.now(ZoneInfo("Asia/Tokyo"))
    except Exception: return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9)))

def get_quest(qid):
    return next((q for q in QUESTS + STORY_QUESTS if q["quest_id"] == qid), {})

def init_state():
    defaults = dict(completed=set(), completed_order=[], completed_at={}, favorites=set(), notes={}, photos={}, photo_data={}, photo_mime={}, photo_storage_paths={}, photo_edit_open=set(), diary_visibility={}, sns_texts={}, diary={}, unlocked_character_ids=set(), unlocked_character_order=[], quest_character_rewards={}, user_lat=None, user_lon=None, user_accuracy=None, user_location_source="未取得", gps_required=True, gps_radius_m=300, manual_location_enabled=False, apples=0, character_apples={}, last_login_date=None, story_progress=0, participant_id="", data_loaded=False, clear_effect=None, clear_effect_counter=0, profile_age="", guide_seen=False, survey_answers={}, survey_submitted=False, survey_submitted_at=None, quest_session_ended=False, quest_end_feedback={}, map_selected_qid="", nickname="", quest_visit_dates={}, custom_diary_entries=[], custom_diary_draft_lat=None, custom_diary_draft_lon=None, custom_diary_draft_id="", custom_diary_draft_photo_path="", custom_diary_draft_photo_name="")
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def state_dict():
    return {
        "completed": list(st.session_state.completed), "completed_order": st.session_state.completed_order, "completed_at": st.session_state.completed_at,
        "favorites": list(st.session_state.favorites), "notes": st.session_state.notes, "photos": st.session_state.photos, "photo_storage_paths": st.session_state.photo_storage_paths, "diary_visibility": st.session_state.diary_visibility, "sns_texts": st.session_state.sns_texts,
        "diary": st.session_state.diary, "unlocked_character_ids": list(st.session_state.unlocked_character_ids), "unlocked_character_order": st.session_state.unlocked_character_order,
        "quest_character_rewards": st.session_state.quest_character_rewards, "apples": st.session_state.apples, "character_apples": st.session_state.character_apples,
        "last_login_date": st.session_state.last_login_date, "story_progress": st.session_state.story_progress, "profile_age": st.session_state.profile_age,
        "guide_seen": st.session_state.guide_seen, "survey_answers": st.session_state.survey_answers, "survey_submitted": st.session_state.survey_submitted,
        "survey_submitted_at": st.session_state.survey_submitted_at, "quest_session_ended": st.session_state.quest_session_ended, "quest_end_feedback": st.session_state.quest_end_feedback, "nickname": st.session_state.nickname, "participant_id": st.session_state.participant_id, "quest_visit_dates": st.session_state.quest_visit_dates, "custom_diary_entries": st.session_state.custom_diary_entries,
    }

def apply_state(d):
    if not isinstance(d, dict): return
    for k, v in d.items():
        if k not in st.session_state: continue
        if k in {"completed", "favorites", "unlocked_character_ids", "photo_edit_open"}: v = set(v or [])
        st.session_state[k] = v

def supabase_configured():
    return create_client is not None and bool(safe_secret("SUPABASE_URL")) and bool(safe_secret("SUPABASE_SERVICE_ROLE_KEY") or safe_secret("SUPABASE_SECRET_KEY"))

@st.cache_resource
def get_supabase_client() -> Optional["Client"]:
    if not supabase_configured(): return None
    return create_client(safe_secret("SUPABASE_URL"), safe_secret("SUPABASE_SERVICE_ROLE_KEY") or safe_secret("SUPABASE_SECRET_KEY"))


def diary_photo_bucket():
    """
    旅日記・クエスト写真用のSupabase Storage bucket名。
    Streamlit Secrets に SUPABASE_DIARY_PHOTO_BUCKET を設定した場合はその名前を使う。
    未設定時は diary-photos を使う。
    """
    return safe_secret("SUPABASE_DIARY_PHOTO_BUCKET", "diary-photos") or "diary-photos"


def ensure_diary_photo_bucket():
    """
    diary-photos bucket が無い場合、Service Role Key を使って自動作成を試みる。
    既に存在する場合はそのまま利用する。
    戻り値: (成功したか, エラーメッセージ)
    """
    if not supabase_configured():
        return False, "Supabaseが設定されていません。"

    sb = get_supabase_client()
    if sb is None:
        return False, "Supabaseに接続できません。"

    bucket_name = diary_photo_bucket()

    try:
        buckets = sb.storage.list_buckets()
        existing_names = set()

        for b in buckets or []:
            if isinstance(b, dict):
                name = b.get("name") or b.get("id")
            else:
                name = getattr(b, "name", None) or getattr(b, "id", None)
            if name:
                existing_names.add(str(name))

        if bucket_name in existing_names:
            return True, ""

        # supabase-py のバージョン差を吸収して作成
        try:
            sb.storage.create_bucket(
                bucket_name,
                options={
                    "public": False,
                    "file_size_limit": 15 * 1024 * 1024,
                    "allowed_mime_types": [
                        "image/jpeg",
                        "image/png",
                        "image/webp",
                    ],
                },
            )
        except TypeError:
            sb.storage.create_bucket(
                bucket_name,
                {
                    "public": False,
                    "file_size_limit": 15 * 1024 * 1024,
                    "allowed_mime_types": [
                        "image/jpeg",
                        "image/png",
                        "image/webp",
                    ],
                },
            )

        return True, ""

    except Exception as e:
        # 「すでに存在する」系は成功扱い
        msg = str(e)
        if "already" in msg.lower() or "exists" in msg.lower() or "duplicate" in msg.lower():
            return True, ""
        return False, msg


def _photo_extension_from_name(filename):
    suffix = Path(str(filename or "")).suffix.lower().lstrip(".")
    if suffix not in {"jpg", "jpeg", "png", "webp"}:
        suffix = "jpg"
    return suffix


def _photo_extension(uploaded_file):
    return _photo_extension_from_name(getattr(uploaded_file, "name", ""))


def upload_photo_bytes_to_supabase(qid, raw, filename="photo.jpg", mime="image/jpeg"):
    """
    画像bytesをSupabase Storageへ永続保存する共通処理。
    戻り値: (成功したか, storage_path, エラーメッセージ)
    """
    if not supabase_configured():
        return False, "", "Supabaseが設定されていません。"

    pid = str(st.session_state.get("participant_id", "")).strip()
    if not pid:
        return False, "", "参加者IDがありません。"

    sb = get_supabase_client()
    if sb is None:
        return False, "", "Supabaseに接続できません。"

    bucket_ok, bucket_error = ensure_diary_photo_bucket()
    if not bucket_ok:
        return False, "", (
            "写真保存用Storageを準備できませんでした。"
            f" 詳細: {bucket_error}"
        )

    ext = _photo_extension_from_name(filename)
    safe_qid = re.sub(r"[^A-Za-z0-9_.-]", "_", str(qid))
    new_path = f"participants/{pid}/{safe_qid}/{uuid.uuid4().hex}.{ext}"

    try:
        file_options = {
            "content-type": mime or "image/jpeg",
            "cache-control": "3600",
            "upsert": "false",
        }

        try:
            sb.storage.from_(diary_photo_bucket()).upload(
                new_path,
                raw,
                file_options=file_options,
            )
        except TypeError:
            # supabase-py のバージョン差対策
            sb.storage.from_(diary_photo_bucket()).upload(
                new_path,
                raw,
                file_options,
            )

        old_path = st.session_state.photo_storage_paths.get(qid, "")
        if old_path and old_path != new_path:
            try:
                sb.storage.from_(diary_photo_bucket()).remove([old_path])
            except Exception:
                pass

        return True, new_path, ""

    except Exception as e:
        return False, "", str(e)


def upload_diary_photo_to_supabase(qid, uploaded_file):
    """
    アルバムから選んだ写真をSupabase Storageへ保存する。
    変更時は新しい写真を先に保存し、成功後に古い写真を削除する。
    戻り値: (成功したか, storage_path, エラーメッセージ)
    """
    return upload_photo_bytes_to_supabase(
        qid=qid,
        raw=uploaded_file.getvalue(),
        filename=getattr(uploaded_file, "name", "photo.jpg"),
        mime=getattr(uploaded_file, "type", None) or "image/jpeg",
    )


def ensure_photo_in_storage(qid):
    """
    公開時にStorageパスが無い場合でも、
    現在セッションに写真bytesが残っていれば自動アップロードして復旧する。
    戻り値: (成功したか, storage_path, エラーメッセージ)
    """
    current_path = st.session_state.photo_storage_paths.get(qid, "")
    if current_path:
        return True, current_path, ""

    raw = st.session_state.photo_data.get(qid)
    if not raw:
        return False, "", (
            "公開用の写真データが見つかりません。"
            "「写真を変更する」から写真を選び直して保存してください。"
        )

    filename = st.session_state.photos.get(qid) or f"{qid}.jpg"
    mime = st.session_state.photo_mime.get(qid) or "image/jpeg"

    ok, storage_path, error = upload_photo_bytes_to_supabase(
        qid=qid,
        raw=raw,
        filename=filename,
        mime=mime,
    )
    if ok:
        st.session_state.photo_storage_paths[qid] = storage_path
        try:
            save_user_data()
        except Exception:
            pass
        try:
            save_quest_supabase(qid)
        except Exception:
            pass

    return ok, storage_path, error


def diary_photo_signed_url(qid, expires_in=3600):
    """
    private bucket の写真を表示するための一時URLを取得する。
    """
    storage_path = st.session_state.photo_storage_paths.get(qid, "")
    if not storage_path or not supabase_configured():
        return ""

    try:
        result = (
            get_supabase_client()
            .storage
            .from_(diary_photo_bucket())
            .create_signed_url(storage_path, expires_in)
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
                or result.get("signed_url")
                or ""
            )

        return (
            getattr(result, "signedURL", "")
            or getattr(result, "signed_url", "")
            or ""
        )
    except Exception:
        return ""

def registered_photo_source(qid):
    """
    今のセッションで選択した写真があればbytesを優先。
    再訪時はSupabase Storageの署名付きURLを返す。
    """
    raw = st.session_state.photo_data.get(qid)
    if raw:
        return raw

    signed_url = diary_photo_signed_url(qid)
    if signed_url:
        return signed_url

    return ""


def diary_photo_signed_url_from_path(storage_path, expires_in=3600):
    """
    private bucket 内の任意パスから署名付きURLを作る。
    みんなの足跡マップでも使う。
    """
    if not storage_path or not supabase_configured():
        return ""

    try:
        result = (
            get_supabase_client()
            .storage
            .from_(diary_photo_bucket())
            .create_signed_url(storage_path, expires_in)
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
                or result.get("signed_url")
                or ""
            )

        return (
            getattr(result, "signedURL", "")
            or getattr(result, "signed_url", "")
            or ""
        )
    except Exception:
        return ""

def public_diary_progress_id(qid):
    """
    公開旅日記を既存の quest_progress テーブルに保存するための特別ID。
    新しいDBテーブルを作らずに運用できる。
    """
    return f"{PUBLIC_DIARY_PREFIX}{qid}"


def render_visibility_selector(qid, scope):
    """
    旅日記の公開範囲を選ぶUI。
    defaultは private。
    """
    current = st.session_state.diary_visibility.get(qid, "private")
    options = [
        "🔒 プライベート（自分だけ）",
        "🌍 全体公開（みんなの足跡に表示）",
    ]

    index = 1 if current == "public" else 0
    label = st.radio(
        "旅日記の公開範囲",
        options,
        index=index,
        horizontal=True,
        key=f"{scope}_visibility_{qid}",
    )

    visibility = "public" if label.startswith("🌍") else "private"
    st.session_state.diary_visibility[qid] = visibility

    if visibility == "public":
        st.info(
            "全体公開すると、ニックネーム・写真・感想が"
            "「みんなの足跡」に表示されます。"
            "現在地は公開されず、クエスト場所の固定ピンだけが表示されます。"
            "人物や車のナンバーなど、公開したくないものが写っていないか確認してください。"
        )
    else:
        st.caption(
            "プライベートは自分だけが見られます。"
            "他の参加者には表示されません。"
        )

    return visibility


def save_public_diary_entry(qid):
    """
    公開旅日記を既存の quest_progress テーブルへ同期する。
    - public: __public_diary__::<quest_id> という特別行を作成/更新
    - private: その特別行を削除
    これにより public_diary 専用テーブルは不要。
    """
    pid = str(st.session_state.get("participant_id", "")).strip()
    visibility = st.session_state.diary_visibility.get(qid, "private")

    if not pid or not supabase_configured():
        return False, "公開機能を利用するための接続設定を確認してください。"

    sb = get_supabase_client()
    if sb is None:
        return False, "公開機能に接続できませんでした。もう一度お試しください。"

    public_qid = public_diary_progress_id(qid)

    try:
        if visibility != "public":
            try:
                (
                    sb.table("quest_progress")
                    .delete()
                    .eq("participant_id", pid)
                    .eq("quest_id", public_qid)
                    .execute()
                )
            except Exception:
                pass
            return True, "旅日記をプライベートに設定しました。"

        if qid not in st.session_state.completed:
            return False, "クエストをクリアすると全体公開できます。"

        # Storageパスが無い場合でも、セッション内の写真から自動復旧を試みる
        photo_ok, photo_storage_path, photo_error = ensure_photo_in_storage(qid)
        if not photo_ok:
            return False, (
                "写真を公開用に保存できませんでした。"
                "「写真を変更する」から写真を選び直して、もう一度保存してください。"
                + (f"（{photo_error}）" if photo_error else "")
            )

        q = get_quest(qid)
        payload = {
            "participant_id": pid,
            "quest_id": qid,
            "nickname": st.session_state.get("nickname", "") or "参加者",
            "linked_name": q.get("linked_name", ""),
            "quest_name": q.get("quest_name", ""),
            "area": classified_area(q),
            "note": st.session_state.notes.get(qid, ""),
            "photo_storage_path": photo_storage_path,
            "visibility": "public",
            "completed_at": st.session_state.completed_at.get(qid),
            "updated_at": jp_now().isoformat(),
        }

        row = {
            "participant_id": pid,
            "quest_id": public_qid,
            "completed": True,
            "completed_at": payload["updated_at"],
            "favorite": False,
            "note": json.dumps(payload, ensure_ascii=False),
            "photo_uploaded": True,
            "sns_text": "",
            "x_post_url": "",
            "character_id": "",
        }

        upsert_progress(row)
        return True, "公開しました！「みんなの足跡」から確認できます。"

    except Exception as e:
        return False, f"公開の保存に失敗しました。もう一度お試しください。（{e}）"


def load_public_diary_rows():
    """
    全参加者の公開旅日記を取得する。
    ・既存クエストの公開旅日記
    ・参加者が自由に立てた公開ピン
    の両方を返す。
    """
    if not supabase_configured():
        return [], "Supabaseが設定されていません。"

    sb = get_supabase_client()
    if sb is None:
        return [], "Supabaseに接続できません。"

    try:
        try:
            rows = (
                sb.table("quest_progress")
                .select("*")
                .like("quest_id", f"{PUBLIC_DIARY_PREFIX}%")
                .order("completed_at", desc=True)
                .execute()
                .data
                or []
            )
        except Exception:
            all_rows = (
                sb.table("quest_progress")
                .select("*")
                .order("completed_at", desc=True)
                .execute()
                .data
                or []
            )
            rows = [
                r for r in all_rows
                if str(r.get("quest_id", "")).startswith(PUBLIC_DIARY_PREFIX)
            ]

        normalized = []

        for r in rows:
            try:
                payload = json.loads(r.get("note") or "{}")
            except Exception:
                continue

            if not isinstance(payload, dict):
                continue
            if payload.get("visibility") != "public":
                continue

            # 自由ピン
            if payload.get("is_custom_pin"):
                try:
                    lat = float(payload.get("lat"))
                    lon = float(payload.get("lon"))
                except Exception:
                    continue

                item = dict(payload)
                item["participant_id"] = item.get("participant_id") or r.get("participant_id")
                item["nickname"] = item.get("nickname") or "参加者"
                item["linked_name"] = item.get("title") or "自由旅日記"
                item["quest_name"] = "自由に追加した旅の足跡"
                item["area"] = "自由スポット"
                item["completed_at"] = item.get("visited_date") or r.get("completed_at")
                item["photo_url"] = diary_photo_signed_url_from_path(
                    item.get("photo_storage_path", "")
                )
                item["lat"] = lat
                item["lon"] = lon
                normalized.append(item)
                continue

            # 通常クエスト
            qid = str(payload.get("quest_id", "")).strip()
            q = get_quest(qid)
            if not q:
                continue

            item = dict(payload)
            item["participant_id"] = item.get("participant_id") or r.get("participant_id")
            item["linked_name"] = item.get("linked_name") or q.get("linked_name", "")
            item["quest_name"] = item.get("quest_name") or q.get("quest_name", "")
            item["area"] = item.get("area") or classified_area(q)
            item["photo_url"] = diary_photo_signed_url_from_path(
                item.get("photo_storage_path", "")
            )
            coord = QUEST_COORDS.get(qid)
            if coord:
                item["lat"], item["lon"] = coord
            normalized.append(item)

        return normalized, ""

    except Exception as e:
        return [], str(e)



def public_diary_popup_html(row):
    """
    公開旅日記マーカー用のPopup HTML
    """
    nickname = html.escape(str(row.get("nickname", "参加者")))
    linked_name = html.escape(str(row.get("linked_name", "")))
    note = html.escape(str(row.get("note", "") or "感想はまだありません。")).replace("\n", "<br>")
    area = html.escape(str(row.get("area", "")))
    date_text = html.escape(str(row.get("completed_at", "") or "")[:10])
    photo_url = row.get("photo_url", "")

    image_html = ""
    if photo_url:
        image_html = (
            f'<img src="{photo_url}" '
            'style="width:100%;max-width:220px;border-radius:12px;margin:8px 0;">'
        )

    return f"""
    <div style="width:240px;font-family:sans-serif;">
      <div style="font-weight:800;color:#125f9d;">{nickname} さん</div>
      <div style="font-size:13px;color:#576c80;margin:2px 0 4px;">{date_text} / {area}</div>
      <div style="font-weight:700;">📍 {linked_name}</div>
      {image_html}
      <div style="font-size:13px;line-height:1.6;">{note}</div>
    </div>
    """

def save_selected_photo(qid, uploaded_file):
    """
    選択した写真を登録する。
    Supabase Storageに保存できる場合は永続保存。
    ローカル開発時はsession_stateにも保持する。
    戻り値: (永続保存できたか, メッセージ)
    """
    raw = uploaded_file.getvalue()

    # まず現在のセッションで表示・クリア判定できるように保存
    st.session_state.photos[qid] = uploaded_file.name
    st.session_state.photo_data[qid] = raw
    st.session_state.photo_mime[qid] = uploaded_file.type or "image/jpeg"

    persistent = False
    message = ""

    if supabase_configured():
        ok, storage_path, error = upload_diary_photo_to_supabase(qid, uploaded_file)
        if ok:
            st.session_state.photo_storage_paths[qid] = storage_path
            persistent = True
            message = "写真を登録しました。後から変更できます。"
        else:
            message = (
                "写真は端末上では登録できましたが、共有用の保存に失敗しました。"
                "通信環境を確認して、もう一度写真を保存してください。"
                f"（詳細: {error}）"
            )
    else:
        message = (
            "写真を登録しました。"
            "Supabase未設定のため、ローカル開発では再起動後に写真本体が消える場合があります。"
        )

    save_user_data()
    try:
        save_quest_supabase(qid)
    except Exception:
        pass

    # すでにクリア済みで全体公開設定なら、写真差し替えを公開側にも反映
    if qid in st.session_state.completed:
        try:
            save_public_diary_entry(qid)
        except Exception:
            pass

    return persistent, message

def render_registered_photo_editor(qid, scope):
    """
    写真の新規登録・変更UI。
    スマホでは file_uploader から写真ライブラリ / アルバムを選択できる。
    戻り値: 写真が登録済みか
    """
    existing = bool(
        st.session_state.photos.get(qid)
        or st.session_state.photo_storage_paths.get(qid)
    )

    # 登録済み写真を表示
    if existing:
        st.markdown("**📷 登録済みの写真**")
        src = registered_photo_source(qid)

        if src:
            st.image(
                src,
                caption="現在登録されている写真",
                use_container_width=True,
            )
        else:
            st.success("📷 写真は登録済みです。")

        if qid not in st.session_state.photo_edit_open:
            if st.button(
                "🔄 写真を変更する",
                key=f"{scope}_open_photo_edit_{qid}",
                use_container_width=True,
            ):
                st.session_state.photo_edit_open.add(qid)
                st.rerun()

    editing = (
        (not existing)
        or qid in st.session_state.photo_edit_open
    )

    if editing:
        if existing:
            st.info(
                "新しい写真を選択して「この写真に変更する」を押すと、"
                "現在の写真と入れ替わります。"
            )
        else:
            st.info(
                "スマホでは「アルバム・写真ライブラリ」から"
                "すでに撮影した写真を選択できます。"
            )

        upload = st.file_uploader(
            "🖼️ アルバムから写真を選択",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
            key=f"{scope}_album_photo_{qid}",
            help="スマホの写真ライブラリ・アルバム、または端末内の画像ファイルから選択できます。",
        )

        if upload is not None:
            st.image(
                upload.getvalue(),
                caption="選択中の写真（まだ登録されていません）",
                use_container_width=True,
            )

            button_label = (
                "✅ この写真に変更する"
                if existing
                else "✅ この写真を登録する"
            )

            if st.button(
                button_label,
                key=f"{scope}_save_photo_{qid}",
                type="primary",
                use_container_width=True,
            ):
                persistent, message = save_selected_photo(qid, upload)

                if qid in st.session_state.photo_edit_open:
                    st.session_state.photo_edit_open.discard(qid)

                if persistent or not supabase_configured():
                    st.success(message)
                else:
                    st.warning(message)

                st.rerun()

        if existing:
            if st.button(
                "キャンセル",
                key=f"{scope}_cancel_photo_edit_{qid}",
                use_container_width=True,
            ):
                st.session_state.photo_edit_open.discard(qid)
                st.rerun()

    return existing



def normalize_nickname(value):
    """名前照合用。前後空白・全角空白・大文字小文字の差を吸収する。"""
    value = str(value or "").replace("\u3000", " ").strip()
    value = re.sub(r"\s+", " ", value)
    return value.casefold()


def get_participant_by_id(participant_id):
    """participantsテーブルから参加者を1件取得する。"""
    pid = str(participant_id or "").strip()
    if not pid or not supabase_configured():
        return None
    sb = get_supabase_client()
    if sb is None:
        return None
    try:
        rows = (
            sb.table("participants")
            .select("*")
            .eq("participant_id", pid)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def find_participant_by_nickname(nickname):
    """
    ニックネームから既存参加者を探す。
    1) participants.nickname / participants.name
    2) quest_progress の __app_state__ に保存された nickname
    の順に検索する。

    これにより、長い participant_id を再入力しなくても
    同じニックネームで過去の進捗へ戻れる。
    """
    target = normalize_nickname(nickname)
    if not target or not supabase_configured():
        return None

    sb = get_supabase_client()
    if sb is None:
        return None

    # まずparticipantsテーブルの名前列を確認
    try:
        rows = sb.table("participants").select("*").execute().data or []
        for row in rows:
            existing_name = row.get("nickname", row.get("name", ""))
            if normalize_nickname(existing_name) == target:
                return {
                    "participant_id": str(row.get("participant_id", "") or "").strip(),
                    "nickname": str(existing_name or nickname).strip(),
                }
    except Exception:
        pass

    # nickname列が無い既存DBでも動くよう、アプリ状態JSONから探す
    try:
        rows = (
            sb.table("quest_progress")
            .select("participant_id,quest_id,note")
            .eq("quest_id", APP_STATE_QUEST_ID)
            .execute()
            .data
            or []
        )
        for row in rows:
            try:
                state = json.loads(row.get("note") or "{}")
            except Exception:
                continue
            if not isinstance(state, dict):
                continue
            existing_name = str(state.get("nickname", "") or "").strip()
            if normalize_nickname(existing_name) == target:
                return {
                    "participant_id": str(row.get("participant_id", "") or "").strip(),
                    "nickname": existing_name,
                }
    except Exception:
        pass

    return None


def nickname_is_taken(nickname, exclude_participant_id=""):
    """別の参加者が同じニックネームを使っているか確認する。"""
    found = find_participant_by_nickname(nickname)
    if not found:
        return False
    exclude_pid = str(exclude_participant_id or "").strip()
    return not (exclude_pid and found.get("participant_id") == exclude_pid)


def register_participant(participant_id, nickname):
    """
    quest_progress保存より先にparticipantsへ親レコードを作る。
    nickname列の有無に依存しないよう、participant_idだけでも登録できる設計。
    戻り値: (成功, メッセージ)
    """
    pid = str(participant_id or "").strip()
    nick = str(nickname or "").replace("\u3000", " ").strip()

    if not pid:
        return False, "参加者IDを作成できませんでした。"
    if not supabase_configured():
        return True, ""

    sb = get_supabase_client()
    if sb is None:
        return False, "Supabaseに接続できません。"

    if get_participant_by_id(pid):
        return True, ""

    # 同名が既に存在する場合は、新規登録ではなくログイン側で扱う
    existing = find_participant_by_nickname(nick) if nick else None
    if existing and existing.get("participant_id") != pid:
        return False, "この参加者名はすでに登録されています。"

    # まずnickname列つきで試す
    try:
        sb.table("participants").insert({
            "participant_id": pid,
            "nickname": nick,
        }).execute()
        return True, ""
    except Exception as e1:
        msg1 = str(e1)

        # 既存DBにnickname列が無い場合はparticipant_idだけで登録
        try:
            sb.table("participants").insert({
                "participant_id": pid,
            }).execute()
            return True, ""
        except Exception as e2:
            msg2 = str(e2)
            low = (msg1 + " " + msg2).lower()
            if "duplicate" in low or "unique" in low or "23505" in low:
                # participant_idが既にあるなら成功扱い
                if get_participant_by_id(pid):
                    return True, ""
                return False, "この参加者名はすでに登録されています。"
            return False, f"参加者情報の登録に失敗しました。（{msg2}）"


def ensure_current_participant():
    """
    quest_progress保存前の安全弁。
    participantsに親レコードが無ければ現在のIDで自動作成する。
    """
    pid = str(st.session_state.get("participant_id", "") or "").strip()
    nick = str(st.session_state.get("nickname", "") or "").strip()

    if not pid:
        return False
    if not supabase_configured():
        return True
    if get_participant_by_id(pid):
        return True

    ok, _ = register_participant(pid, nick)
    return ok


def update_participant_nickname(participant_id, new_nickname):
    """
    参加者名変更。
    同名の別参加者がいる場合は拒否。
    nickname列が無いDBでも、__app_state__ に保存されるため継続利用できる。
    """
    pid = str(participant_id or "").strip()
    nick = str(new_nickname or "").replace("\u3000", " ").strip()

    if not pid or not nick:
        return False, "参加者名を入力してください。"
    if nickname_is_taken(nick, exclude_participant_id=pid):
        return False, "この参加者名はすでに使われています。別の名前を入力してください。"

    if not supabase_configured():
        return True, ""

    sb = get_supabase_client()
    if sb is None:
        return False, "Supabaseに接続できません。"

    # nickname列があれば同期。無ければ無視し、app_state側の名前を正とする。
    try:
        sb.table("participants").update({
            "nickname": nick,
        }).eq("participant_id", pid).execute()
    except Exception:
        pass

    return True, ""

def upsert_progress(row):
    sb = get_supabase_client()
    if sb is None:
        return False

    # quest_progress は participants の子テーブル。
    # 必ず先に participants に現在の参加者を登録して外部キーエラーを防ぐ。
    if not ensure_current_participant():
        return False

    pid, qid = row["participant_id"], row["quest_id"]
    found = (
        sb.table("quest_progress")
        .select("*")
        .eq("participant_id", pid)
        .eq("quest_id", qid)
        .limit(1)
        .execute()
        .data
        or []
    )
    if found:
        (
            sb.table("quest_progress")
            .update(row)
            .eq("participant_id", pid)
            .eq("quest_id", qid)
            .execute()
        )
    else:
        sb.table("quest_progress").insert(row).execute()
    return True

def save_app_state_supabase():
    pid = st.session_state.participant_id.strip()
    if not pid or not supabase_configured(): return False
    return upsert_progress({"participant_id": pid, "quest_id": APP_STATE_QUEST_ID, "completed": False, "completed_at": None, "favorite": False, "note": json.dumps(state_dict(), ensure_ascii=False), "photo_uploaded": False, "sns_text": "", "x_post_url": "", "character_id": ""})

def save_quest_supabase(qid):
    pid = st.session_state.participant_id.strip()
    if not pid or not supabase_configured():
        return False

    completed_at = st.session_state.completed_at.get(qid)
    visit_date = st.session_state.quest_visit_dates.get(qid)
    if visit_date:
        # DB上でも実際に行った日が分かるよう、日付をcompleted_atへ反映
        completed_at = f"{visit_date}T12:00:00+09:00"

    return upsert_progress({
        "participant_id": pid,
        "quest_id": qid,
        "completed": qid in st.session_state.completed,
        "completed_at": completed_at,
        "favorite": qid in st.session_state.favorites,
        "note": st.session_state.notes.get(qid, ""),
        "photo_uploaded": bool(
            st.session_state.photos.get(qid)
            or st.session_state.photo_storage_paths.get(qid)
        ),
        "sns_text": st.session_state.sns_texts.get(qid, ""),
        "x_post_url": "",
        "character_id": st.session_state.quest_character_rewards.get(qid, ""),
    })


QUEST_FEEDBACK_PREFIX = "__quest_feedback__::"

def quest_feedback_row_id(qid):
    return f"{QUEST_FEEDBACK_PREFIX}{qid}"

def save_quest_end_feedback(qid, payload):
    """
    既存の全体アンケートとは別に、
    クエストごとの3問アンケートを quest_progress にJSON保存する。
    DBの列追加は不要。
    """
    pid = st.session_state.participant_id.strip()
    if not pid or not supabase_configured():
        return False

    row = {
        "participant_id": pid,
        "quest_id": quest_feedback_row_id(qid),
        "completed": True,
        "completed_at": payload.get("submitted_at"),
        "favorite": False,
        "note": json.dumps(payload, ensure_ascii=False),
        "photo_uploaded": False,
        "sns_text": "",
        "x_post_url": "",
        "character_id": "",
    }
    return upsert_progress(row)

def load_quest_end_feedback_from_row(row):
    qid = str(row.get("quest_id", ""))
    if not qid.startswith(QUEST_FEEDBACK_PREFIX):
        return False

    actual_qid = qid[len(QUEST_FEEDBACK_PREFIX):]
    if not get_quest(actual_qid):
        return True

    try:
        payload = json.loads(row.get("note") or "{}")
        if isinstance(payload, dict):
            st.session_state.quest_end_feedback[actual_qid] = payload
    except Exception:
        pass

    return True

def save_survey_to_quest_progress(payload):
    """
    アンケートを現在の参加者に紐づけて保存する。
    participants親レコードを先に保証し、foreign keyエラーを防ぐ。
    """
    pid = st.session_state.participant_id.strip()
    if not pid or not supabase_configured():
        return False

    if not ensure_current_participant():
        raise RuntimeError(
            "参加者情報をSupabaseのparticipantsテーブルへ登録できませんでした。"
        )

    return upsert_progress({
        "participant_id": pid,
        "quest_id": SURVEY_QUEST_ID,
        "completed": True,
        "completed_at": payload["submitted_at"],
        "favorite": False,
        "note": json.dumps(payload, ensure_ascii=False),
        "photo_uploaded": False,
        "sns_text": "",
        "x_post_url": "",
        "character_id": "",
    })

def save_user_data():
    try: SAVE_FILE.write_text(json.dumps(state_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass
    try: save_app_state_supabase()
    except Exception: pass

def load_user_data():
    pid = st.session_state.participant_id.strip()

    # URLのparticipant_idから参加者名を復元する。
    # 再訪時は「名前」ではなく一意のparticipant_idで同じ進捗を読み込む。
    if supabase_configured() and pid:
        participant = get_participant_by_id(pid)
        if participant:
            saved_nickname = participant.get("nickname", participant.get("name", ""))
            if saved_nickname:
                st.session_state.nickname = str(saved_nickname).strip()

    # Streamlit Community Cloud などSupabase運用時は、参加者IDごとに読み込む。
    # participant_id がない新規参加者に共有ローカルsaveを読み込ませないことで、
    # 他の参加者の名前や進捗が表示されることを防ぐ。
    if supabase_configured():
        if not pid:
            return
        try:
            rows = get_supabase_client().table("quest_progress").select("*").eq("participant_id", pid).execute().data or []
            app = next((r for r in rows if r.get("quest_id") == APP_STATE_QUEST_ID), None)
            if app and app.get("note"):
                apply_state(json.loads(app["note"]))

            survey = next((r for r in rows if r.get("quest_id") == SURVEY_QUEST_ID), None)
            if survey and survey.get("note"):
                st.session_state.survey_answers = json.loads(survey["note"])
                st.session_state.survey_submitted = True

            for r in rows:
                qid = r.get("quest_id")

                # クエスト終了時の3問アンケートは通常クエスト進捗とは別に読む
                if load_quest_end_feedback_from_row(r):
                    continue

                # 自由旅日記も通常クエスト進捗とは別に読む
                if load_custom_diary_from_row(r):
                    continue

                if not qid or qid in {APP_STATE_QUEST_ID, SURVEY_QUEST_ID} or not get_quest(qid):
                    continue

                if r.get("completed"):
                    st.session_state.completed.add(qid)
                    if qid not in st.session_state.completed_order:
                        st.session_state.completed_order.append(qid)
                    if r.get("completed_at"):
                        st.session_state.completed_at[qid] = r["completed_at"]
                        try:
                            st.session_state.quest_visit_dates[qid] = str(r["completed_at"])[:10]
                        except Exception:
                            pass

                if r.get("note") is not None:
                    st.session_state.notes[qid] = r.get("note") or ""

                if r.get("photo_uploaded"):
                    st.session_state.photos[qid] = "写真添付済み"

                if r.get("character_id"):
                    cid = r["character_id"]
                    st.session_state.quest_character_rewards[qid] = cid
                    st.session_state.unlocked_character_ids.add(cid)
                    if cid not in st.session_state.unlocked_character_order:
                        st.session_state.unlocked_character_order.append(cid)
            return
        except Exception:
            # 参加者データの混同を避けるため、Supabase設定済みの本番環境では
            # 接続エラー時に共有ローカルsaveへフォールバックしない。
            return

    # Supabase未設定のローカル開発時のみローカルsaveを利用。
    if SAVE_FILE.exists():
        try:
            apply_state(json.loads(SAVE_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass

# =====================================================================
# 分類・画像・GPS
# =====================================================================
def classified_purpose(q): return QUEST_ID_TO_PURPOSE.get(q.get("quest_id"), q.get("quest_type", ""))
def classified_area(q): return QUEST_ID_TO_AREA.get(q.get("quest_id"), q.get("area", ""))
def is_story(q): return q.get("quest_id") in STORY_QUEST_ORDER
def chapter(q): return STORY_QUEST_ORDER.get(q.get("quest_id"))
def story_unlocked(q): return not is_story(q) or (chapter(q) - 1) <= int(st.session_state.story_progress)

def display_quest(q):
    d = dict(q); d["quest_type"] = classified_purpose(q); d["area"] = classified_area(q)
    if is_story(q):
        c = chapter(q)
        if story_unlocked(q): d["quest_name"] = f"ストーリーモード第{c}章：{q['quest_name']}"
        else: d.update(quest_name=f"ストーリーモード第{c}章（シークレット）", linked_name="シークレット", description="前の章をクリアすると目的地と内容が解放されます。", condition="前のストーリークエストをクリアする", official_url="")
    return d

def find_local_image(folder: Path, stem: str):
    for ext in IMG_EXTS:
        p = folder / f"{stem}.{ext}"
        if p.exists(): return p
    return None

def render_place_photo(q, compact=False):
    p = find_local_image(PLACE_PHOTO_DIR, q["quest_id"])
    if p: st.image(str(p), caption=q.get("linked_name", ""), use_container_width=True)
    else:
        h = 110 if compact else 210
        st.markdown(f'<div style="height:{h}px;border-radius:18px;background:#edf8ff;border:1px solid #cfeafa;display:flex;align-items:center;justify-content:center;text-align:center;font-size:22px;font-weight:800;color:#24506b">📍 {html.escape(q.get("linked_name", "天草のクエスト"))}</div>', unsafe_allow_html=True)

def character_image_path(img_id):
    p = find_local_image(CHARACTER_IMAGE_DIR, img_id)
    if p: return str(p)
    alt = img_id.replace("①", "1").replace("②", "2").replace("③", "3")
    p = find_local_image(CHARACTER_IMAGE_DIR, alt)
    if p: return str(p)
    base = re.sub(r"[①②③123]$", "", img_id)
    p = find_local_image(CHARACTER_IMAGE_DIR, base)
    if p: return str(p)
    url = safe_secret("SUPABASE_URL").rstrip("/")
    if url:
        bucket = safe_secret("SUPABASE_CHARACTER_IMAGE_BUCKET", "character-images") or "character-images"
        ext = safe_secret("SUPABASE_CHARACTER_IMAGE_EXT", "png").lstrip(".") or "png"
        return f"{url}/storage/v1/object/public/{urllib.parse.quote(bucket)}/{urllib.parse.quote(img_id + '.' + ext)}"
    return ""

def get_character_stage(cid):
    b = CHARACTERS[cid]; fed = int(st.session_state.character_apples.get(cid, 0)); stages = b["stages"]
    idx = 2 if len(stages) >= 3 and fed >= 20 else (1 if len(stages) >= 2 and fed >= 10 else 0)
    d = dict(b); d.update(stages[idx]); d.update(character_id=cid, stage_idx=idx, fed_apples=fed, stage_count=len(stages)); return d

def set_location(lat, lon, acc=None, source="GPS"):
    st.session_state.user_lat, st.session_state.user_lon, st.session_state.user_accuracy, st.session_state.user_location_source = lat, lon, acc, source

def current_location():
    if st.session_state.user_lat is None or st.session_state.user_lon is None: return None
    return float(st.session_state.user_lat), float(st.session_state.user_lon)

def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0; a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(math.radians(lon2-lon1)/2)**2
    return 2*r*math.atan2(math.sqrt(a), math.sqrt(1-a))

def distance(q):
    loc, c = current_location(), QUEST_COORDS.get(q["quest_id"])
    return haversine_m(loc[0], loc[1], c[0], c[1]) if loc and c else None

def fmt_dist(d): return "距離不明" if d is None else (f"約{d:.0f}m" if d < 1000 else f"約{d/1000:.1f}km")

def google_maps_url(q): return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{q.get('linked_name','')} 天草")

def schedule_notice(q):
    t, closed = q.get("time_info", "ー"), q.get("closed_days", "ー")
    if t != "ー": st.caption(f"営業時間・開催情報：{t}")
    if closed not in {"", "ー", "なし"}: st.caption(f"定休日：{closed}（最新情報は公式サイトをご確認ください）")

# =====================================================================
# クエスト処理
# =====================================================================
def make_sns_text(q): return f"天草つながりクエストで『{q['linked_name']}』に参加しました。\n{q['description']}\n#天草つながりクエスト #天草観光 #天草旅"
def x_url(text): return "https://twitter.com/intent/tweet?" + urllib.parse.urlencode({"text": text})

def complete_quest(q):
    qid = q["quest_id"]; already = qid in st.session_state.completed
    if not already:
        st.session_state.completed.add(qid); st.session_state.completed_order.append(qid); st.session_state.completed_at[qid] = jp_now().isoformat(); st.session_state.apples += 3
        if is_story(q) and chapter(q) == st.session_state.story_progress + 1: st.session_state.story_progress = chapter(q)
    cid = QUEST_CHARACTER_REWARDS[qid]; new = cid not in st.session_state.unlocked_character_ids
    st.session_state.quest_character_rewards[qid] = cid; st.session_state.unlocked_character_ids.add(cid)
    if cid not in st.session_state.unlocked_character_order: st.session_state.unlocked_character_order.append(cid)
    st.session_state.sns_texts[qid] = st.session_state.sns_texts.get(qid) or make_sns_text(q)
    st.session_state.clear_effect_counter += 1
    st.session_state.clear_effect = {"id": st.session_state.clear_effect_counter, "qid": qid, "new": new, "apples": 0 if already else 3}
    save_user_data()
    try:
        save_quest_supabase(qid)
    except Exception:
        pass

    # クリア時点で全体公開が選ばれていれば、みんなの足跡にも同期
    try:
        save_public_diary_entry(qid)
    except Exception:
        pass

def render_clear_effect():
    e = st.session_state.clear_effect
    if not e: return
    q = get_quest(e["qid"]); char = get_character_stage(QUEST_CHARACTER_REWARDS[e["qid"]]); img = character_image_path(char["img_id"])
    st.balloons(); st.markdown("## 🎉 QUEST CLEAR!"); st.success("新しい仲間をGET！" if e["new"] else "クエストクリア！")
    c1, c2 = st.columns([1, 2])
    with c1:
        if img: st.image(img, use_container_width=True)
        else: st.markdown(f"# {char['emoji']}")
    with c2:
        st.markdown(f"### {char['name']}"); st.caption(f"{char['rarity']} / {char['series']}"); st.write(char['catch']); st.write(f"🍎 リンゴ +{e['apples']}")
    if st.button("OK（タップで確認）", type="primary", use_container_width=True): st.session_state.clear_effect = None; st.rerun()
    st.divider()

def render_locked(q):
    d = display_quest(q)
    with st.container(border=True):
        st.markdown(f"### 🔒 {d['quest_name']}"); st.warning("前の章をクリアすると、この章の目的地と内容が解放されます。")

def quest_card(q, scope):
    original = get_quest(q["quest_id"])
    if is_story(original) and not story_unlocked(original): render_locked(original); return
    qid = q["quest_id"]; done = qid in st.session_state.completed
    with st.container(border=True):
        st.markdown(f"### {'✅' if done else '📍'} {q['quest_name']}"); st.caption(f"{'クリア済み' if done else '未クリア'} / {classified_purpose(original)} / {classified_area(original)}")
        render_place_photo(original); st.write(q.get("description", "")); st.markdown(f"**場所：** {q.get('linked_name','')}"); st.markdown(f"**達成条件：** {q.get('condition','')}"); schedule_notice(original)
        c1, c2 = st.columns(2)
        if q.get("official_url"): c1.link_button("公式情報", q["official_url"], use_container_width=True)
        c2.link_button("Googleマップ", google_maps_url(original), use_container_width=True)
        visit_day = st.date_input(
            "📅 行った日",
            value=visit_date_default(qid),
            max_value=date.today(),
            key=f"{scope}_visit_date_{qid}",
        )
        st.session_state.quest_visit_dates[qid] = visit_day.isoformat()

        note = st.text_area("旅のメモ・感想", value=st.session_state.notes.get(qid, ""), key=f"{scope}_note_{qid}")
        st.session_state.notes[qid] = note
        st.markdown("#### 📷 クエスト・旅日記の写真")
        render_registered_photo_editor(qid, scope)

        st.markdown("#### 🌍 公開設定")
        render_visibility_selector(qid, scope)

        # CLEAR判定は写真のみ。
        # GPS現在地が一致していなくても写真を登録すればCLEARできる。
        photo_ok = bool(
            st.session_state.photos.get(qid)
            or st.session_state.photo_storage_paths.get(qid)
        )

        if not photo_ok:
            st.info("📷 クエストクリアには写真の登録が必要です。")

        if st.button(
            "もう一度クリア演出を見る" if done else "🎉 クエストをクリアする",
            key=f"{scope}_clear_{qid}",
            type="primary",
            disabled=not photo_ok,
            use_container_width=True,
        ):
            complete_quest(original)
            st.rerun()
        if done:
            if st.button(
                "💾 旅日記・公開設定を保存",
                key=f"{scope}_save_diary_visibility_{qid}",
                use_container_width=True,
            ):
                save_user_data()
                try:
                    save_quest_supabase(qid)
                except Exception:
                    pass

                ok, msg = save_public_diary_entry(qid)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

            text = st.text_area("SNS投稿用文章", value=st.session_state.sns_texts.get(qid, make_sns_text(original)), key=f"{scope}_sns_{qid}")
            st.session_state.sns_texts[qid] = text
            st.link_button("Xで共有", x_url(text), use_container_width=True)

# =====================================================================
# マップ・図鑑・まとめ
# =====================================================================
def render_map(qs):
    st.subheader("🗺️ クエストマップ")
    if folium is None or st_folium is None: st.error("requirements.txt に folium と streamlit-folium を追加してください。"); return
    m = folium.Map(location=[32.45, 130.19], zoom_start=9, tiles="OpenStreetMap")
    loc = current_location()
    if loc: folium.Marker(loc, tooltip="現在地", icon=folium.Icon(color="blue")).add_to(m)
    for q in qs:
        c = QUEST_COORDS.get(q["quest_id"])
        if not c: continue
        d = display_quest(q); color = "green" if q["quest_id"] in st.session_state.completed else ("gray" if is_story(q) and not story_unlocked(q) else "blue")
        folium.Marker(c, tooltip=d["linked_name"], popup=folium.Popup(f"<b>{html.escape(d['linked_name'])}</b><br>{html.escape(d['quest_name'])}", max_width=280), icon=folium.Icon(color=color, icon="flag")).add_to(m)
    st_folium(m, width=None, height=500, key="main_quest_map")


def visit_date_default(qid):
    """クエストの訪問日。未登録ならクリア日または今日を初期値にする。"""
    saved = str(st.session_state.quest_visit_dates.get(qid, "") or "").strip()
    if saved:
        try:
            return date.fromisoformat(saved[:10])
        except Exception:
            pass

    completed = str(st.session_state.completed_at.get(qid, "") or "").strip()
    if completed:
        try:
            return date.fromisoformat(completed[:10])
        except Exception:
            pass

    return date.today()


def custom_public_diary_progress_id(entry_id):
    return f"{PUBLIC_DIARY_PREFIX}custom::{entry_id}"


def save_custom_diary_entry(entry):
    """
    自由旅日記をquest_progressへ保存する。
    private/publicどちらも自分の記録として保存し、
    publicの場合は「みんなの足跡」用の公開行も同期する。
    """
    pid = st.session_state.participant_id.strip()
    if not pid or not supabase_configured():
        return False

    entry_id = str(entry.get("entry_id", "") or "").strip()
    if not entry_id:
        entry_id = uuid.uuid4().hex
        entry["entry_id"] = entry_id

    private_qid = f"{CUSTOM_DIARY_PREFIX}{entry_id}"

    private_row = {
        "participant_id": pid,
        "quest_id": private_qid,
        "completed": True,
        "completed_at": entry.get("visited_date") or jp_now().date().isoformat(),
        "favorite": False,
        "note": json.dumps(entry, ensure_ascii=False),
        "photo_uploaded": bool(entry.get("photo_storage_path")),
        "sns_text": "",
        "x_post_url": "",
        "character_id": "",
    }
    upsert_progress(private_row)

    public_qid = custom_public_diary_progress_id(entry_id)
    visibility = str(entry.get("visibility", "private") or "private")

    sb = get_supabase_client()
    if visibility == "public":
        public_payload = dict(entry)
        public_payload["visibility"] = "public"
        public_payload["is_custom_pin"] = True
        public_payload["nickname"] = st.session_state.get("nickname", "") or "参加者"

        public_row = {
            "participant_id": pid,
            "quest_id": public_qid,
            "completed": True,
            "completed_at": entry.get("visited_date") or jp_now().date().isoformat(),
            "favorite": False,
            "note": json.dumps(public_payload, ensure_ascii=False),
            "photo_uploaded": bool(entry.get("photo_storage_path")),
            "sns_text": "",
            "x_post_url": "",
            "character_id": "",
        }
        upsert_progress(public_row)
    else:
        try:
            (
                sb.table("quest_progress")
                .delete()
                .eq("participant_id", pid)
                .eq("quest_id", public_qid)
                .execute()
            )
        except Exception:
            pass

    return True


def load_custom_diary_from_row(row):
    qid = str(row.get("quest_id", "") or "")
    if not qid.startswith(CUSTOM_DIARY_PREFIX):
        return False

    try:
        payload = json.loads(row.get("note") or "{}")
    except Exception:
        return True

    if not isinstance(payload, dict):
        return True

    entry_id = str(payload.get("entry_id", "") or qid[len(CUSTOM_DIARY_PREFIX):])
    payload["entry_id"] = entry_id
    payload.setdefault("visibility", "private")

    existing_ids = {
        str(e.get("entry_id", ""))
        for e in st.session_state.custom_diary_entries
        if isinstance(e, dict)
    }
    if entry_id not in existing_ids:
        st.session_state.custom_diary_entries.append(payload)
    else:
        # 保存済みの最新内容で更新
        for i, e in enumerate(st.session_state.custom_diary_entries):
            if isinstance(e, dict) and str(e.get("entry_id", "")) == entry_id:
                st.session_state.custom_diary_entries[i] = payload
                break
    return True


def custom_diary_photo_signed_url(entry):
    path = str(entry.get("photo_storage_path", "") or "")
    return diary_photo_signed_url_from_path(path) if path else ""


def upload_custom_diary_draft_photo(uploaded_file):
    """
    自由ピン用写真を、旅日記本体を保存する前にStorageへ登録する。
    file_uploaderの内容がrerunで消えてもStorageパスをsession_stateに保持する。
    """
    if uploaded_file is None:
        return False, "写真を選択してください。"

    draft_id = str(st.session_state.get("custom_diary_draft_id", "") or "").strip()
    if not draft_id:
        draft_id = uuid.uuid4().hex
        st.session_state.custom_diary_draft_id = draft_id

    ok, storage_path, error = upload_photo_bytes_to_supabase(
        qid=f"custom_{draft_id}",
        raw=uploaded_file.getvalue(),
        filename=getattr(uploaded_file, "name", "photo.jpg"),
        mime=getattr(uploaded_file, "type", None) or "image/jpeg",
    )
    if not ok:
        return False, error or "写真の保存に失敗しました。"

    st.session_state.custom_diary_draft_photo_path = storage_path
    st.session_state.custom_diary_draft_photo_name = getattr(uploaded_file, "name", "photo.jpg")
    return True, "写真を登録しました。"



def render_custom_diary_creator():
    st.markdown("### 📌 自由に旅の足跡を追加")
    st.caption("地図をタップして好きな場所にピンを立て、写真・感想・行った日を記録できます。")

    if folium is None or st_folium is None:
        st.warning("自由ピン機能には folium と streamlit-folium が必要です。")
        return

    if not st.session_state.custom_diary_draft_id:
        st.session_state.custom_diary_draft_id = uuid.uuid4().hex

    m = folium.Map(location=[32.43, 130.19], zoom_start=9, tiles="OpenStreetMap")

    for e in st.session_state.custom_diary_entries:
        try:
            lat = float(e.get("lat"))
            lon = float(e.get("lon"))
        except Exception:
            continue
        title = html.escape(str(e.get("title", "旅の記録")))
        folium.Marker(
            [lat, lon],
            tooltip=title,
            icon=folium.Icon(color="purple", icon="camera"),
        ).add_to(m)

    # 選択中のピンも表示
    if (
        st.session_state.custom_diary_draft_lat is not None
        and st.session_state.custom_diary_draft_lon is not None
    ):
        folium.Marker(
            [
                st.session_state.custom_diary_draft_lat,
                st.session_state.custom_diary_draft_lon,
            ],
            tooltip="選択中の場所",
            icon=folium.Icon(color="red", icon="map-marker"),
        ).add_to(m)

    clicked = st_folium(
        m,
        width=None,
        height=430,
        key="custom_diary_pin_map",
    )

    last_clicked = (clicked or {}).get("last_clicked") if isinstance(clicked, dict) else None
    if last_clicked:
        st.session_state.custom_diary_draft_lat = last_clicked.get("lat")
        st.session_state.custom_diary_draft_lon = last_clicked.get("lng")

    lat = st.session_state.custom_diary_draft_lat
    lon = st.session_state.custom_diary_draft_lon

    if lat is None or lon is None:
        st.info("地図上の記録したい場所をタップしてください。")
        return

    st.success(f"📍 ピン位置：{float(lat):.5f}, {float(lon):.5f}")

    # 写真はフォーム外で先に確定保存する。
    # これによりStreamlitのrerunでアップロード画像が消える問題を防ぐ。
    st.markdown("#### 📷 写真")
    draft_photo_path = str(
        st.session_state.get("custom_diary_draft_photo_path", "") or ""
    )

    if draft_photo_path:
        signed = diary_photo_signed_url_from_path(draft_photo_path)
        if signed:
            st.image(signed, caption="登録済みの写真", use_container_width=True)
        else:
            st.success("写真は登録済みです。")

        if st.button(
            "写真を変更する",
            key="custom_diary_change_photo",
            use_container_width=True,
        ):
            st.session_state.custom_diary_draft_photo_path = ""
            st.session_state.custom_diary_draft_photo_name = ""
            st.rerun()
    else:
        custom_upload = st.file_uploader(
            "写真を選択",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"custom_diary_photo_{st.session_state.custom_diary_draft_id}",
            help="スマホの写真ライブラリ・アルバムから選択できます。",
        )

        if custom_upload is not None:
            st.image(
                custom_upload.getvalue(),
                caption="選択中の写真",
                use_container_width=True,
            )
            if st.button(
                "✅ この写真を登録",
                key="custom_diary_save_photo",
                type="primary",
                use_container_width=True,
            ):
                ok, msg = upload_custom_diary_draft_photo(custom_upload)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(f"写真を登録できませんでした。{msg}")

    st.markdown("#### 🌍 公開設定")
    visibility_label = st.radio(
        "この自由旅日記の公開範囲",
        [
            "🔒 プライベート（自分だけ）",
            "🌍 全体公開（みんなの足跡に表示）",
        ],
        index=0,
        horizontal=True,
        key=f"custom_diary_visibility_{st.session_state.custom_diary_draft_id}",
    )
    visibility = "public" if visibility_label.startswith("🌍") else "private"

    with st.form("custom_diary_form", clear_on_submit=False):
        title = st.text_input(
            "場所・タイトル",
            placeholder="例：海沿いで見つけた夕日スポット",
            max_chars=60,
        )
        visited_date = st.date_input(
            "行った日",
            value=date.today(),
            max_value=date.today(),
        )
        note = st.text_area(
            "旅のメモ・感想",
            placeholder="この場所で感じたこと、見つけたことを書いてください。",
            height=110,
        )
        submitted = st.form_submit_button(
            "📌 この場所を旅日記に追加",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not title.strip():
            st.error("場所・タイトルを入力してください。")
            return

        entry_id = str(st.session_state.custom_diary_draft_id or uuid.uuid4().hex)

        entry = {
            "entry_id": entry_id,
            "title": title.strip(),
            "visited_date": visited_date.isoformat(),
            "note": note.strip(),
            "lat": float(lat),
            "lon": float(lon),
            "photo_storage_path": str(
                st.session_state.get("custom_diary_draft_photo_path", "") or ""
            ),
            "visibility": visibility,
            "created_at": jp_now().isoformat(),
        }

        st.session_state.custom_diary_entries.append(entry)

        saved_ok = True
        try:
            saved_ok = save_custom_diary_entry(entry)
        except Exception as e:
            saved_ok = False
            st.error(f"Supabase保存エラー：{e}")

        save_user_data()

        if saved_ok or not supabase_configured():
            if visibility == "public":
                st.success("自由旅日記を追加し、「みんなの足跡」に公開しました。")
            else:
                st.success("自由旅日記を追加しました。")
        else:
            st.warning("端末には保存しましたが、Supabaseへの保存に失敗しました。")

        # 次の自由ピン用にドラフトを初期化
        st.session_state.custom_diary_draft_lat = None
        st.session_state.custom_diary_draft_lon = None
        st.session_state.custom_diary_draft_id = uuid.uuid4().hex
        st.session_state.custom_diary_draft_photo_path = ""
        st.session_state.custom_diary_draft_photo_name = ""
        st.rerun()




def replace_custom_diary_photo(entry, uploaded_file):
    """
    保存済みの自由旅日記写真を後から差し替える。
    新しい写真を先にSupabase Storageへ保存し、成功後に古い写真を削除する。
    戻り値: (成功, メッセージ)
    """
    if uploaded_file is None:
        return False, "新しい写真を選択してください。"

    entry_id = str(entry.get("entry_id", "") or "").strip()
    if not entry_id:
        return False, "旅日記IDが見つかりません。"

    old_path = str(entry.get("photo_storage_path", "") or "")

    ok, new_path, error = upload_photo_bytes_to_supabase(
        qid=f"custom_replace_{entry_id}",
        raw=uploaded_file.getvalue(),
        filename=getattr(uploaded_file, "name", "photo.jpg"),
        mime=getattr(uploaded_file, "type", None) or "image/jpeg",
    )

    if not ok:
        return False, error or "新しい写真の保存に失敗しました。"

    # 共通アップロード関数側では自由旅日記の古いpathを知らないため、ここで削除
    if old_path and old_path != new_path and supabase_configured():
        try:
            (
                get_supabase_client()
                .storage
                .from_(diary_photo_bucket())
                .remove([old_path])
            )
        except Exception:
            # 削除に失敗しても新しい写真は有効なので続行
            pass

    entry["photo_storage_path"] = new_path
    entry["updated_at"] = jp_now().isoformat()

    try:
        saved_ok = save_custom_diary_entry(entry)
    except Exception as e:
        return False, f"旅日記の更新保存に失敗しました。（{e}）"

    save_user_data()

    if not saved_ok and supabase_configured():
        return False, "旅日記の更新をSupabaseへ保存できませんでした。"

    return True, "写真を変更しました。"


def render_custom_diary_entries():
    entries = [
        e for e in st.session_state.custom_diary_entries
        if isinstance(e, dict)
    ]
    if not entries:
        return

    st.markdown("### 📍 自由に追加した旅日記")

    for e in sorted(
        entries,
        key=lambda x: str(x.get("visited_date", "")),
        reverse=True,
    ):
        entry_id = str(e.get("entry_id", ""))
        with st.container(border=True):
            st.markdown(f"**📌 {e.get('title', '旅の記録')}**")

            edited_date = st.date_input(
                "行った日",
                value=(
                    date.fromisoformat(str(e.get("visited_date"))[:10])
                    if str(e.get("visited_date", "") or "")
                    else date.today()
                ),
                max_value=date.today(),
                key=f"custom_entry_date_{entry_id}",
            )

            st.markdown("#### 📷 写真")
            photo_url = custom_diary_photo_signed_url(e)
            if photo_url:
                st.image(
                    photo_url,
                    caption="現在登録されている写真",
                    use_container_width=True,
                )
            elif e.get("photo_storage_path"):
                st.success("📷 写真は登録済みです。")
            else:
                st.caption("写真はまだ登録されていません。")

            edit_flag_key = f"custom_entry_photo_edit_{entry_id}"
            if edit_flag_key not in st.session_state:
                st.session_state[edit_flag_key] = False

            if not st.session_state[edit_flag_key]:
                button_label = (
                    "🔄 写真を変更する"
                    if e.get("photo_storage_path")
                    else "📷 写真を追加する"
                )
                if st.button(
                    button_label,
                    key=f"open_custom_entry_photo_edit_{entry_id}",
                    use_container_width=True,
                ):
                    st.session_state[edit_flag_key] = True
                    st.rerun()
            else:
                st.info(
                    "新しい写真を選択して保存すると、現在の写真と入れ替わります。"
                )

                replacement_upload = st.file_uploader(
                    "新しい写真を選択",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"replace_custom_entry_photo_{entry_id}",
                )

                if replacement_upload is not None:
                    st.image(
                        replacement_upload.getvalue(),
                        caption="変更後の写真（まだ保存されていません）",
                        use_container_width=True,
                    )

                pc1, pc2 = st.columns(2)

                with pc1:
                    if st.button(
                        "✅ この写真に変更",
                        key=f"save_custom_entry_photo_{entry_id}",
                        type="primary",
                        use_container_width=True,
                        disabled=replacement_upload is None,
                    ):
                        ok, msg = replace_custom_diary_photo(
                            e,
                            replacement_upload,
                        )
                        if ok:
                            st.session_state[edit_flag_key] = False
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                with pc2:
                    if st.button(
                        "キャンセル",
                        key=f"cancel_custom_entry_photo_{entry_id}",
                        use_container_width=True,
                    ):
                        st.session_state[edit_flag_key] = False
                        st.rerun()

            edited_note = st.text_area(
                "感想",
                value=str(e.get("note", "") or ""),
                key=f"custom_entry_note_{entry_id}",
            )

            current_visibility = str(e.get("visibility", "private") or "private")
            edited_visibility_label = st.radio(
                "公開範囲",
                [
                    "🔒 プライベート（自分だけ）",
                    "🌍 全体公開（みんなの足跡に表示）",
                ],
                index=1 if current_visibility == "public" else 0,
                horizontal=True,
                key=f"custom_entry_visibility_{entry_id}",
            )
            edited_visibility = (
                "public"
                if edited_visibility_label.startswith("🌍")
                else "private"
            )

            if st.button(
                "💾 この旅日記を保存",
                key=f"save_custom_entry_{entry_id}",
                use_container_width=True,
            ):
                e["visited_date"] = edited_date.isoformat()
                e["note"] = edited_note.strip()
                e["visibility"] = edited_visibility
                e["updated_at"] = jp_now().isoformat()

                try:
                    ok = save_custom_diary_entry(e)
                except Exception as ex:
                    ok = False
                    st.error(f"保存エラー：{ex}")

                save_user_data()

                if ok or not supabase_configured():
                    if edited_visibility == "public":
                        st.success("保存し、「みんなの足跡」に公開しました。")
                    else:
                        st.success("保存しました。")
                else:
                    st.warning("Supabaseへの保存に失敗しました。")

            try:
                lat = float(e.get("lat"))
                lon = float(e.get("lon"))
                st.link_button(
                    "Googleマップで場所を見る",
                    f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                    use_container_width=True,
                )
            except Exception:
                pass



def render_private_diary():
    st.subheader("🔒 自分の旅日記")

    render_custom_diary_creator()
    render_custom_diary_entries()
    st.divider()

    done = [
        qid
        for qid in st.session_state.completed_order
        if qid in st.session_state.completed
    ]

    if folium is not None and st_folium is not None:
        m = folium.Map(location=[32.43, 130.19], zoom_start=9)
        for i, qid in enumerate(done, 1):
            q = get_quest(qid)
            c = QUEST_COORDS.get(qid)
            if c:
                folium.Marker(
                    c,
                    tooltip=f"{i}. {q['linked_name']}",
                    icon=folium.Icon(color="green", icon="check"),
                ).add_to(m)
        st_folium(m, width=None, height=450, key="diary_map")

    if not done:
        st.info("まだ足跡はありません。クエストをクリアすると表示されます。")
        return

    for qid in reversed(done):
        q = get_quest(qid)
        with st.container(border=True):
            st.markdown(f"**{q['linked_name']}**")

            diary_visit_day = st.date_input(
                "📅 行った日",
                value=visit_date_default(qid),
                max_value=date.today(),
                key=f"diary_visit_date_{qid}",
            )
            st.session_state.quest_visit_dates[qid] = diary_visit_day.isoformat()

            render_registered_photo_editor(
                qid,
                scope=f"diary_photo_{qid}",
            )

            st.markdown("#### 🌍 公開設定")
            render_visibility_selector(qid, f"diary_visibility_{qid}")

            n = st.text_area(
                "感想",
                value=st.session_state.notes.get(qid, ""),
                key=f"diary_{qid}",
            )

            if st.button(
                "日記・公開設定を保存",
                key=f"diary_save_{qid}",
                use_container_width=True,
            ):
                st.session_state.notes[qid] = n
                save_user_data()

                try:
                    save_quest_supabase(qid)
                except Exception:
                    pass

                ok, msg = save_public_diary_entry(qid)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

def render_public_diary():
    st.subheader("🌍 みんなの足跡マップ")
    st.caption(
        "ここには、参加者が「全体公開」を選んだ旅日記だけが表示されます。"
        "位置はクエスト地点の固定座標です。"
    )

    rows, err = load_public_diary_rows()

    if err:
        st.warning(
            "みんなの足跡を読み込めませんでした。"
            "通信環境またはSupabase接続設定を確認してください。"
            f"（詳細: {err}）"
        )
        return

    if not rows:
        st.info(
            "まだ公開された旅日記はありません。"
            "自分の旅日記で「🌍 全体公開」を選ぶと、ここに表示されます。"
        )
        return

    if folium is not None and st_folium is not None:
        m = folium.Map(location=[32.43, 130.19], zoom_start=9)

        for row in rows:
            try:
                coord = (float(row.get("lat")), float(row.get("lon")))
            except Exception:
                qid = row.get("quest_id", "")
                coord = QUEST_COORDS.get(qid)

            if not coord:
                continue

            folium.Marker(
                coord,
                tooltip=f"{row.get('nickname', '参加者')} さん / {row.get('linked_name', '')}",
                popup=folium.Popup(
                    public_diary_popup_html(row),
                    max_width=290,
                ),
                icon=folium.Icon(color="blue", icon="camera"),
            ).add_to(m)

        st_folium(
            m,
            width=None,
            height=500,
            key="public_diary_map",
        )

    st.markdown("### 🧳 公開されている旅日記一覧")

    for row in rows:
        with st.container(border=True):
            st.markdown(
                f"**{row.get('nickname', '参加者')} さん** "
                f"｜ 📍 {row.get('linked_name', '')}"
            )
            st.caption(
                f"{str(row.get('completed_at', '') or '')[:10]} / "
                f"{row.get('area', '')}"
            )

            if row.get("photo_url"):
                st.image(
                    row["photo_url"],
                    use_container_width=True,
                )

            note = row.get("note", "") or "感想はまだありません。"
            st.write(note)

def render_diary():
    my_tab, public_tab = st.tabs(
        ["🔒 自分の旅日記", "🌍 みんなの足跡"]
    )

    with my_tab:
        render_private_diary()

    with public_tab:
        render_public_diary()

def render_character(char, locked=False):

    with st.container(border=True):
        if locked: st.markdown("# ❓"); st.markdown("**？？？**"); st.caption("対応するクエストをクリアすると解放されます。"); return
        img = character_image_path(char["img_id"])
        if img: st.image(img, use_container_width=True)
        else: st.markdown(f"# {char['emoji']}")
        st.markdown(f"**{char['name']}**"); st.caption(f"{char['rarity']} / {char['series']}")
        cid, fed, count = char["character_id"], char["fed_apples"], char["stage_count"]; maxfed = 20 if count >= 3 else 10
        st.progress(min(fed/maxfed, 1.0), text=f"育成：{fed}/{maxfed} 🍎")
        if fed < maxfed and st.button("🍎 リンゴをあげる", key=f"feed_{cid}", disabled=st.session_state.apples <= 0, use_container_width=True): st.session_state.apples -= 1; st.session_state.character_apples[cid] = fed + 1; save_user_data(); st.rerun()

def render_summary():
    st.subheader("🎒 旅のまとめ"); done = [qid for qid in st.session_state.completed_order if qid in st.session_state.completed]
    c1, c2, c3 = st.columns(3); c1.metric("クリア", len(done)); c2.metric("ストーリー", st.session_state.story_progress); c3.metric("仲間", len(st.session_state.unlocked_character_ids))
    if done:
        rows = [{
            "日付": st.session_state.quest_visit_dates.get(qid) or st.session_state.completed_at.get(qid, "")[:10],
            "場所": get_quest(qid)["linked_name"],
            "エリア": classified_area(get_quest(qid)),
        } for qid in done]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# =====================================================================
# クエスト終了画面（旅のまとめ + クエスト別3問アンケート）
# =====================================================================

def star_rating_options():
    return [
        "★1",
        "★2",
        "★3",
        "★4",
        "★5",
    ]

def star_value(label):
    try:
        return int(str(label).replace("★", "").strip())
    except Exception:
        return None

def render_end_feedback_for_quest(qid):
    q = get_quest(qid)
    if not q:
        return

    saved = dict(
        st.session_state.quest_end_feedback.get(qid, {})
        or {}
    )

    rating_options = star_rating_options()

    fun_default = saved.get("fun_rating")
    motive_default = saved.get("character_motivation_rating")

    fun_idx = (
        max(0, min(int(fun_default) - 1, 4))
        if fun_default in {1, 2, 3, 4, 5}
        else None
    )
    motive_idx = (
        max(0, min(int(motive_default) - 1, 4))
        if motive_default in {1, 2, 3, 4, 5}
        else None
    )

    with st.container(border=True):
        st.markdown(f"### 📍 {q.get('linked_name', '')}")
        st.caption(q.get("quest_name", ""))

        with st.form(f"quest_end_feedback_form_{qid}"):
            fun_label = st.radio(
                "**Q1. このクエストは楽しかったですか？**",
                rating_options,
                index=fun_idx,
                horizontal=True,
                key=f"end_fun_{qid}",
            )

            motive_label = st.radio(
                "**Q2. キャラクターを獲得できることは、この場所を訪れる動機になりましたか？**",
                rating_options,
                index=motive_idx,
                horizontal=True,
                key=f"end_motive_{qid}",
            )

            improvement = st.text_area(
                "**Q3. 改善してほしい点・分かりにくかった点があれば教えてください。（任意）**",
                value=saved.get("improvement", ""),
                height=110,
                key=f"end_improve_{qid}",
            )

            submit = st.form_submit_button(
                "このクエストの回答を保存",
                type="primary",
                use_container_width=True,
            )

        if submit:
            if fun_label is None or motive_label is None:
                st.error("Q1とQ2は★1〜5のいずれかを選択してください。")
            else:
                payload = {
                    "quest_id": qid,
                    "quest_name": q.get("quest_name", ""),
                    "linked_name": q.get("linked_name", ""),
                    "fun_rating": star_value(fun_label),
                    "character_motivation_rating": star_value(motive_label),
                    "improvement": improvement.strip(),
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                }

                st.session_state.quest_end_feedback[qid] = payload
                save_user_data()

                saved_ok = False
                err = None
                try:
                    saved_ok = save_quest_end_feedback(qid, payload)
                except Exception as e:
                    err = e

                if saved_ok:
                    st.success("回答を保存しました。ありがとうございます！")
                elif err:
                    st.warning(
                        "端末には保存しましたが、Supabaseへの保存に失敗しました。"
                        f" エラー: {err}"
                    )
                else:
                    st.success("回答を保存しました。")

        if saved:
            st.caption("✅ このクエストは回答済みです。再回答すると内容を更新できます。")

def render_quest_end_screen():
    st.markdown(
        """
        <div style="
            padding:24px 22px;
            border-radius:24px;
            background:linear-gradient(135deg,#1479d3,#55bde9);
            color:white;
            text-align:center;
            margin:10px 0 18px;
        ">
          <div style="font-size:31px;font-weight:900;">🏁 クエスト終了</div>
          <div style="font-size:15px;margin-top:8px;">
            天草での旅、おつかれさまでした。<br>
            旅の記録を振り返り、クリアしたクエストについて教えてください。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## 🎒 今回の旅のまとめ")
    render_summary()

    completed_ids = [
        qid
        for qid in st.session_state.completed_order
        if qid in st.session_state.completed and get_quest(qid)
    ]

    st.divider()
    st.markdown("## ⭐ クエスト終了アンケート")
    st.caption(
        "現在の全体アンケートとは別の、クエストごとの3問アンケートです。"
        "Q1・Q2は★1〜5、Q3は任意回答です。"
    )

    if not completed_ids:
        st.info(
            "まだクリアしたクエストがありません。"
            "写真を登録してクエストをCLEARすると、ここにアンケートが表示されます。"
        )
    else:
        answered_count = len(
            [
                qid
                for qid in completed_ids
                if qid in st.session_state.quest_end_feedback
            ]
        )

        st.progress(
            answered_count / len(completed_ids),
            text=f"回答済み：{answered_count} / {len(completed_ids)} クエスト",
        )

        for qid in completed_ids:
            render_end_feedback_for_quest(qid)

    st.divider()

    back_col, survey_col = st.columns(2)

    with back_col:
        if st.button(
            "← クエスト画面に戻る",
            use_container_width=True,
        ):
            st.session_state.quest_session_ended = False
            save_user_data()
            st.rerun()

    with survey_col:
        st.caption(
            "全体アンケートは従来どおり「📝 アンケート」から回答できます。"
        )


# =====================================================================
# アンケート（旅行消費・掲載店送客効果追加版）
# =====================================================================
def idx(options, value, default=0):
    try: return options.index(value)
    except (ValueError, TypeError): return default

def render_survey():
    st.subheader("📝 テストマーケティング アンケート")
    st.write("回答はアプリ改善、天草への再訪効果、クエスト掲載店・施設への送客効果の検証に使用します。")
    if st.session_state.survey_submitted: st.success("✅ 回答済みです。内容を変更して再送信できます。")
    ans = dict(st.session_state.survey_answers or {})
    gender_opts = ["選択してください", "男性", "女性", "回答しない・その他"]
    region_opts = ["選択してください", "天草", "熊本県内（天草外）", "九州地方（熊本県外）", "関東地方", "関西地方", "その他"]
    companion_opts = ["一人旅", "家族（配偶者・パートナー）", "家族（子ども連れ）", "家族（親・その他親族）", "友人・知人", "恋人", "旅行ではない（天草在住・日常利用）", "その他"]
    game_opts = ["選択してください", "よくする", "たまにする", "あまりしない", "全くしない"]
    visit_opts = ["選択してください", "初めて", "2回目", "3〜5回目", "6回目以上（リピーター）", "天草在住"]
    change_opts = ["選択してください", "1：大きく下がった", "2：やや下がった", "3：変わらない", "4：やや高まった", "5：大きく高まった", "該当しない（天草在住）"]
    intent_opts = ["選択してください", "1：全くそう思わない", "2：あまりそう思わない", "3：どちらともいえない", "4：そう思う", "5：とてもそう思う", "該当しない（天草在住）"]
    sat_opts = ["選択してください", "1：とても不満", "2：やや不満", "3：どちらともいえない", "4：満足", "5：とても満足"]
    travel_spend = ["回答しない", "0円", "1〜999円", "1,000〜2,999円", "3,000〜4,999円", "5,000〜9,999円", "10,000〜19,999円", "20,000〜29,999円", "30,000〜49,999円", "50,000円以上", "わからない"]
    quest_spend = ["選択してください", "0円", "1〜999円", "1,000〜2,999円", "3,000〜4,999円", "5,000〜9,999円", "10,000〜19,999円", "20,000〜29,999円", "30,000円以上", "わからない"]
    trigger_opts = ["選択してください", "はい", "いいえ", "わからない・覚えていない", "該当しない（天草在住・日常利用など）"]
    counter_opts = ["選択してください", "利用していたと思う", "おそらく利用していた", "おそらく利用していなかった", "利用していなかったと思う", "わからない"]
    places = list(dict.fromkeys([q["linked_name"] for q in QUESTS + STORY_QUESTS]))
    with st.form("survey"):
        st.markdown("### ■ あなた自身について")
        age = st.selectbox("Q1. 年代", AGE_OPTIONS[1:], index=max(0, idx(AGE_OPTIONS[1:], st.session_state.profile_age or ans.get("age", ""))))
        gender = st.selectbox("Q2. 性別（任意）", gender_opts, index=idx(gender_opts, ans.get("gender", "")))
        region = st.selectbox("Q3. 居住地域（必須）", region_opts, index=idx(region_opts, ans.get("region", "")))
        region_other = st.text_input("Q3-2. その他の場合", value=ans.get("region_other", ""))
        companions = st.multiselect("Q4. 同行者（任意・複数可）", companion_opts, default=ans.get("companions", []))
        companion_other = st.text_input("Q4-2. その他の場合", value=ans.get("companion_other", ""))
        gaming = st.selectbox("Q5. 普段ゲームをしますか？（任意）", game_opts, index=idx(game_opts, ans.get("gaming", "")))
        visits = st.selectbox("Q6. 天草への訪問回数（必須）", visit_opts, index=idx(visit_opts, ans.get("visits", "")))
        st.markdown("### ■ 今回の旅での消費について")
        st.caption("おおよその1人あたりで構いません。Q7は任意です。")
        a, b = st.columns(2)
        with a:
            lodging = st.selectbox("Q7-1. 宿泊費", travel_spend, index=idx(travel_spend, ans.get("trip_spend_lodging", "回答しない")))
            food = st.selectbox("Q7-2. 飲食費", travel_spend, index=idx(travel_spend, ans.get("trip_spend_food", "回答しない")))
        with b:
            souvenir = st.selectbox("Q7-3. お土産・買い物代", travel_spend, index=idx(travel_spend, ans.get("trip_spend_souvenir", "回答しない")))
            experience = st.selectbox("Q7-4. 体験・施設入場料", travel_spend, index=idx(travel_spend, ans.get("trip_spend_experience", "回答しない")))
        st.markdown("### ■ クエスト掲載店・施設への送客効果")
        listing_spend = st.selectbox("Q8. クエスト掲載店・有料施設で使った金額合計（必須・1人あたり）", quest_spend, index=idx(quest_spend, ans.get("quest_listing_spend", "")))
        triggered = st.selectbox("Q9. アプリ・クエストがきっかけで実際に行ったスポットはありましたか？（必須）", trigger_opts, index=idx(trigger_opts, ans.get("app_triggered_visit", "")))
        triggered_places = st.multiselect("Q9-2. 『はい』の方：アプリがきっかけで訪れたスポット", places, default=[x for x in ans.get("app_triggered_places", []) if x in places])
        triggered_spend = st.selectbox("Q9-3. 『はい』の方：その掲載店・有料施設で使った金額合計", quest_spend, index=idx(quest_spend, ans.get("app_triggered_spend", "")))
        counter = st.selectbox("Q10. 『はい』の方：このアプリがなくても、そのスポットを訪問・利用していたと思いますか？", counter_opts, index=idx(counter_opts, ans.get("counterfactual_visit", "")))
        st.markdown("### ■ アプリ機能評価")
        ratings = {}; saved = ans.get("feature_ratings", {}) or {}
        for i, feature in enumerate(FEATURE_SURVEY_ITEMS, 11): ratings[feature] = st.radio(f"Q{i}. {feature}", FEATURE_RATING_OPTIONS, index=idx(FEATURE_RATING_OPTIONS, saved.get(feature, "使っていない")), horizontal=True, key=f"rate_{feature}")
        qn = 11 + len(FEATURE_SURVEY_ITEMS)
        st.markdown("### ■ 再訪意欲")
        revisit_change = st.selectbox(f"Q{qn}. アプリ利用で『また来たい』気持ちは高まりましたか？（必須）", change_opts, index=idx(change_opts, ans.get("revisit_change", "")))
        revisit_intent = st.selectbox(f"Q{qn+1}. 今後1年以内に天草を再訪したいですか？（必須）", intent_opts, index=idx(intent_opts, ans.get("revisit_intent", "")))
        reuse_intent = st.selectbox(f"Q{qn+2}. 次回もこのアプリを使いたいですか？（必須）", intent_opts, index=idx(intent_opts, ans.get("reuse_intent", "")))
        satisfaction = st.selectbox(f"Q{qn+3}. アプリ全体の満足度（必須）", sat_opts, index=idx(sat_opts, ans.get("overall_satisfaction", "")))
        good = st.text_area(f"Q{qn+4}. 良かった点（任意）", value=ans.get("good_points", ""))
        improve = st.text_area(f"Q{qn+5}. 改善点（任意）", value=ans.get("improvement_points", ""))
        request = st.text_area(f"Q{qn+6}. 追加してほしい機能（任意）", value=ans.get("requested_features", ""))
        submitted = st.form_submit_button("📨 アンケートを送信する", type="primary", use_container_width=True)
    if not submitted: return
    missing = []
    for cond, label in [(region == "選択してください", "居住地域"), (visits == "選択してください", "天草訪問回数"), (listing_spend == "選択してください", "掲載店・施設での消費額"), (triggered == "選択してください", "アプリによる来訪の有無"), (revisit_change == "選択してください", "再訪意欲の変化"), (revisit_intent == "選択してください", "再訪意向"), (reuse_intent == "選択してください", "再利用意向"), (satisfaction == "選択してください", "満足度")]:
        if cond: missing.append(label)
    if region == "その他" and not region_other.strip(): missing.append("その他の居住地域")
    if "一人旅" in companions and len(companions) > 1: missing.append("同行者（一人旅と他項目は併用不可）")
    if triggered == "はい":
        if not triggered_places: missing.append("アプリがきっかけで訪れたスポット")
        if triggered_spend == "選択してください": missing.append("アプリ起点の消費額")
        if counter == "選択してください": missing.append("アプリがなかった場合の訪問意向")
    if missing: st.error("未回答の必須項目があります：" + "、".join(missing)); return
    payload = {
        "age": age, "gender": gender, "region": region, "region_other": region_other.strip(), "companions": companions, "companion_other": companion_other.strip(), "gaming": gaming, "visits": visits,
        "trip_spend_lodging": lodging, "trip_spend_food": food, "trip_spend_souvenir": souvenir, "trip_spend_experience": experience, "quest_listing_spend": listing_spend,
        "app_triggered_visit": triggered, "app_triggered_places": triggered_places if triggered == "はい" else [], "app_triggered_spend": triggered_spend if triggered == "はい" else "該当なし", "counterfactual_visit": counter if triggered == "はい" else "該当なし",
        "feature_ratings": ratings, "revisit_change": revisit_change, "revisit_intent": revisit_intent, "reuse_intent": reuse_intent, "overall_satisfaction": satisfaction,
        "good_points": good.strip(), "improvement_points": improve.strip(), "requested_features": request.strip(), "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    st.session_state.profile_age = age; st.session_state.survey_answers = payload; st.session_state.survey_submitted = True; st.session_state.survey_submitted_at = payload["submitted_at"]
    saved_ok = False; err = None
    try: saved_ok = save_survey_to_quest_progress(payload)
    except Exception as e: err = e
    save_user_data()
    if saved_ok: st.success("ご回答ありがとうございました！Supabaseに保存しました。")
    elif err: st.error(f"Supabase保存エラー：{err}")
    else: st.warning("端末には保存しました。Supabase接続設定をご確認ください。")

# =====================================================================
# UI
# =====================================================================
def apply_theme():
    st.markdown('''<style>.stApp{background:linear-gradient(180deg,#f8fdff,#fff 45%,#f4fbff)}[data-testid="stMainBlockContainer"]{max-width:1180px;padding-top:1rem}.hero{padding:24px;border-radius:24px;background:linear-gradient(135deg,#1479d3,#55bde9);color:#fff;box-shadow:0 14px 32px rgba(0,80,150,.18);margin-bottom:14px}.hero b{font-size:32px}.stButton>button,.stLinkButton>a{border-radius:14px!important;min-height:46px;font-weight:700}[data-testid="stImage"] img{border-radius:16px}h1,h2,h3{color:#125f9d}@media(max-width:768px){[data-testid="stMainBlockContainer"]{padding:.6rem .7rem 4rem}.hero{padding:18px}.hero b{font-size:27px}[data-testid="stHorizontalBlock"]{flex-wrap:wrap}[data-testid="column"]{min-width:min(100%,250px);flex:1 1 250px!important}}
.name-onboarding{max-width:760px;margin:2.2rem auto 1rem;padding:34px 28px;border-radius:28px;background:linear-gradient(135deg,#1479d3,#55bde9);color:#fff;box-shadow:0 18px 46px rgba(0,80,150,.22);text-align:center}
.name-onboarding .title{font-size:34px;font-weight:900;line-height:1.25;margin-bottom:10px}
.name-onboarding .sub{font-size:16px;font-weight:600;line-height:1.7;opacity:.98}
.name-hint{max-width:760px;margin:0 auto 10px;text-align:center;color:#49677d;font-size:14px}
@media(max-width:768px){.name-onboarding{margin:1rem auto .7rem;padding:27px 18px;border-radius:22px}.name-onboarding .title{font-size:27px}.name-onboarding .sub{font-size:14px}}</style>''', unsafe_allow_html=True)

def usage_guide():
    with st.expander("📘 はじめての方へ｜アプリの使い方", expanded=not st.session_state.guide_seen):
        st.markdown("**① クエストを選ぶ** → **② 現地で写真を登録してCLEAR** → **③ キャラクター獲得** → **④ ストーリーにも挑戦** → **⑤ 旅日記は「🔒 プライベート / 🌍 全体公開」を選べる** → **⑥ 全体公開で保存すると写真・感想が「みんなの足跡」に表示** → **⑦ 最後に「🏁 クエスト終了」から旅を振り返る**")
        if not st.session_state.guide_seen and st.button("✅ 使い方を確認しました", use_container_width=True): st.session_state.guide_seen = True; save_user_data(); st.rerun()

def recommend(qs, purpose, area, season, kw):
    current = "春" if date.today().month in [3,4,5] else "夏" if date.today().month in [6,7,8] else "秋" if date.today().month in [9,10,11] else "冬"
    out = []
    for q in qs:
        if purpose != "すべて" and classified_purpose(q) != purpose: continue
        if area != "すべて" and classified_area(q) != area: continue
        target = current if season == "今日・今週" else season
        if target not in {"日程未定", "通年"} and q.get("season") not in {"通年", target}: continue
        text = " ".join([q["quest_name"], q["linked_name"], q.get("description", ""), " ".join(q.get("tags", []))])
        if kw and kw.lower().replace(" ", "") not in text.lower().replace(" ", ""): continue
        out.append(q)
    return out

st.set_page_config(page_title="天草つながりクエスト", page_icon="🌊", layout="wide", initial_sidebar_state="collapsed")
init_state(); apply_theme()

# URL ?pid=... を参加者IDに反映
try:
    pid_q = st.query_params.get("pid", "")
    if isinstance(pid_q, list):
        pid_q = pid_q[0] if pid_q else ""
    if pid_q and not st.session_state.participant_id:
        st.session_state.participant_id = str(pid_q).strip()
except Exception:
    pass

# URLに参加者IDがある再訪者は、Supabaseから名前・進捗を先に読み込む
if not st.session_state.data_loaded:
    load_user_data()
    st.session_state.data_loaded = True

# ---------------------------------------------------------------------
# ★ 初回大画面：参加者名の入力
# 名前が未登録のときは、メインアプリを表示する前にこの画面だけを表示する。
# ---------------------------------------------------------------------
if not str(st.session_state.get("nickname", "")).strip():
    st.markdown(
        """
        <div class="name-onboarding">
          <div class="title">🌊 天草つながりクエストへようこそ！</div>
          <div class="sub">
            まず、今回このアプリを体験する<br>
            <b>参加者のお名前</b>を教えてください。<br>
            ニックネームでも大丈夫です。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="name-hint">入力した名前は、あなたの旅の記録を管理するために使用します。</div>',
        unsafe_allow_html=True,
    )

    with st.form("initial_participant_name_form"):
        first_name = st.text_input(
            "参加者のお名前（ニックネームでも可）",
            placeholder="例：めい",
            max_chars=30,
        ).strip()

        start_button = st.form_submit_button(
            "この名前ではじめる 🚀",
            type="primary",
            use_container_width=True,
        )

    if start_button:
        if not first_name:
            st.error("参加者のお名前を入力してください。")
        else:
            # 同じニックネームがあれば「新規登録」ではなく前回データへログインする。
            existing = find_participant_by_nickname(first_name)

            if existing and existing.get("participant_id"):
                st.session_state.participant_id = existing["participant_id"]
                st.session_state.nickname = existing.get("nickname") or first_name

                # 既存参加者の進捗・図鑑・日記・アンケート等を読み直す
                load_user_data()
                st.session_state.data_loaded = True

                try:
                    st.query_params["pid"] = st.session_state.participant_id
                except Exception:
                    pass

                st.success("前回の旅のデータを読み込みました。")
                st.rerun()

            else:
                # 未登録の名前だけ新規参加者として作成する。
                new_pid = "AMK-" + uuid.uuid4().hex[:10].upper()

                ok, msg = register_participant(new_pid, first_name)
                if not ok:
                    st.error(msg)
                else:
                    st.session_state.participant_id = new_pid
                    st.session_state.nickname = first_name

                    try:
                        st.query_params["pid"] = st.session_state.participant_id
                    except Exception:
                        pass

                    # app_stateを含め、最初の状態をSupabaseへ保存
                    save_user_data()
                    st.rerun()

    # 名前入力が終わるまでは下のアプリ画面を表示しない。
    st.stop()

# ---------------------------------------------------------------------
# 名前登録後のメイン画面
# ---------------------------------------------------------------------
st.markdown(
    '<div class="hero"><b>🌊 天草つながりクエスト</b><br>'
    '天草をめぐって、見つけて、集める。あなたの旅をクエストにしよう。</div>',
    unsafe_allow_html=True,
)

st.success(
    f"👋 {st.session_state.nickname} さん、天草の旅を楽しみましょう！"
)

with st.expander("👤 参加者名を変更する"):
    new_nick = st.text_input(
        "参加者のお名前（ニックネームでも可）",
        value=st.session_state.nickname,
        max_chars=30,
        key="edit_participant_name",
    ).strip()

    st.caption(
        f"参加者ID：{st.session_state.participant_id}"
    )

    if st.button(
        "参加者名を保存",
        use_container_width=True,
        key="save_participant_name",
    ):
        if not new_nick:
            st.warning("参加者のお名前を入力してください。")
        else:
            ok, msg = update_participant_nickname(
                st.session_state.participant_id,
                new_nick,
            )
            if not ok:
                st.warning(msg)
            else:
                st.session_state.nickname = new_nick
                save_user_data()
                st.success("参加者名を変更しました。")
                st.rerun()

usage_guide(); render_clear_effect()

# -------------------------------------------------------------
# ★ わかりやすい「クエスト終了」ボタン
# 1件以上CLEARしたら押せる。押すと通常画面から終了画面へ切り替える。
# -------------------------------------------------------------
completed_for_end = [
    qid
    for qid in st.session_state.completed_order
    if qid in st.session_state.completed and get_quest(qid)
]

end_left, end_right = st.columns([2.2, 1])

with end_right:
    if st.button(
        "🏁 クエスト終了・旅を振り返る",
        type="primary",
        use_container_width=True,
        disabled=len(completed_for_end) == 0,
    ):
        st.session_state.quest_session_ended = True
        save_user_data()
        st.rerun()

# 終了後は通常のクエスト画面を隠して、
# 「旅のまとめ + クエスト別3問アンケート」に切り替える。
if st.session_state.quest_session_ended:
    render_quest_end_screen()
    st.divider()
    st.caption("天草つながりクエスト｜テストマーケティング版")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    today = date.today().isoformat()
    if st.session_state.last_login_date != today:
        if st.button("🎁 今日のログインボーナス：🍎3個", use_container_width=True): st.session_state.apples += 3; st.session_state.last_login_date = today; save_user_data(); st.rerun()
    else: st.success(f"🎁 本日受取済み｜所持リンゴ {st.session_state.apples}個")
with c2:
    done_normal = len([q for q in QUESTS if q["quest_id"] in st.session_state.completed]); st.progress(done_normal/len(QUESTS), text=f"参加した通常クエスト：{done_normal}/{len(QUESTS)}")

# ログインボーナス直下にも、長いアンケートへ移動できるボタンを設置
st.markdown("#### 📝 テストマーケティングアンケート")
if st.button(
    "📝 アンケートに回答する",
    key="open_main_survey_button",
    type="secondary",
    use_container_width=True,
):
    st.session_state.open_survey_from_top = True
    st.rerun()

if st.session_state.get("open_survey_from_top", False):
    with st.container(border=True):
        st.markdown("### 📝 テストマーケティング アンケート")
        if st.button(
            "閉じる",
            key="close_main_survey_button",
            use_container_width=True,
        ):
            st.session_state.open_survey_from_top = False
            st.rerun()
        render_survey()


# GPSによるCLEAR判定は廃止。
# クエスト場所の固定座標はマップ表示のみに使用します。

main_tab, list_tab, story_tab, diary_tab, char_tab, summary_tab, survey_tab = st.tabs(["🌟 おすすめ", "🗺️ 全クエスト", "📖 ストーリー", "👣 旅日記", "🎁 図鑑", "🎒 旅まとめ", "📝 アンケート"])
with main_tab:
    st.subheader("あなたにおすすめの地域つながりクエスト")
    cols = st.columns(3)
    for i, q in enumerate(QUESTS[:12]):
        with cols[i % 3]: quest_card(q, f"main_{i}")
with list_tab:
    f = st.columns(4); p = f[0].selectbox("目的", ["すべて"] + OBJECTIVES); a = f[1].selectbox("エリア", ["すべて", "上天草", "天草", "苓北"]); s = f[2].selectbox("行く時期", SEASONS, index=len(SEASONS)-1); kw = f[3].text_input("キーワード")
    qs = recommend(QUESTS + STORY_QUESTS, p, a, s, kw); render_map(qs); st.markdown(f"### クエスト一覧（{len(qs)}件）")
    for i, q in enumerate(qs): quest_card(display_quest(q), f"list_{i}")
with story_tab:
    st.subheader("📖 天草四郎ストーリーモード"); cover = find_local_image(STORY_ASSET_DIR, "story_cover")
    if cover: st.image(str(cover), use_container_width=True)
    st.progress(st.session_state.story_progress/len(STORY_QUESTS), text=f"進行：{st.session_state.story_progress}/{len(STORY_QUESTS)}章")
    for i, q in enumerate(STORY_QUESTS, 1): st.markdown(f"## 第{i}章"); quest_card(display_quest(q), f"story_{i}")
with diary_tab: render_diary()
with char_tab:
    st.subheader("🎁 キャラクター図鑑 & 育成"); st.metric("所持リンゴ", f"{st.session_state.apples} 🍎"); ids = list(dict.fromkeys(QUEST_CHARACTER_REWARDS.values())); cols = st.columns(3)
    for i, cid in enumerate(ids):
        with cols[i % 3]: render_character(get_character_stage(cid), locked=cid not in st.session_state.unlocked_character_ids)
with summary_tab: render_summary()
with survey_tab: render_survey()

st.divider(); st.caption("天草つながりクエスト｜テストマーケティング版")
