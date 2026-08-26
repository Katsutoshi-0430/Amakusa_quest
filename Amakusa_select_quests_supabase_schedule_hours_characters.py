# -*- coding: utf-8 -*-
"""天草つながりクエスト / Streamlit テストマーケティング版"""
from __future__ import annotations

import base64
import html
import json
import math
import re
import urllib.parse
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
    defaults = dict(completed=set(), completed_order=[], completed_at={}, favorites=set(), notes={}, photos={}, photo_data={}, photo_mime={}, sns_texts={}, diary={}, unlocked_character_ids=set(), unlocked_character_order=[], quest_character_rewards={}, user_lat=None, user_lon=None, user_accuracy=None, user_location_source="未取得", gps_required=True, gps_radius_m=300, manual_location_enabled=False, apples=0, character_apples={}, last_login_date=None, story_progress=0, participant_id="", data_loaded=False, clear_effect=None, clear_effect_counter=0, profile_age="", guide_seen=False, survey_answers={}, survey_submitted=False, survey_submitted_at=None, map_selected_qid="", nickname="")
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def state_dict():
    return {
        "completed": list(st.session_state.completed), "completed_order": st.session_state.completed_order, "completed_at": st.session_state.completed_at,
        "favorites": list(st.session_state.favorites), "notes": st.session_state.notes, "photos": st.session_state.photos, "sns_texts": st.session_state.sns_texts,
        "diary": st.session_state.diary, "unlocked_character_ids": list(st.session_state.unlocked_character_ids), "unlocked_character_order": st.session_state.unlocked_character_order,
        "quest_character_rewards": st.session_state.quest_character_rewards, "apples": st.session_state.apples, "character_apples": st.session_state.character_apples,
        "last_login_date": st.session_state.last_login_date, "story_progress": st.session_state.story_progress, "profile_age": st.session_state.profile_age,
        "guide_seen": st.session_state.guide_seen, "survey_answers": st.session_state.survey_answers, "survey_submitted": st.session_state.survey_submitted,
        "survey_submitted_at": st.session_state.survey_submitted_at, "nickname": st.session_state.nickname,
    }

def apply_state(d):
    if not isinstance(d, dict): return
    for k, v in d.items():
        if k not in st.session_state: continue
        if k in {"completed", "favorites", "unlocked_character_ids"}: v = set(v or [])
        st.session_state[k] = v

def supabase_configured():
    return create_client is not None and bool(safe_secret("SUPABASE_URL")) and bool(safe_secret("SUPABASE_SERVICE_ROLE_KEY") or safe_secret("SUPABASE_SECRET_KEY"))

@st.cache_resource
def get_supabase_client() -> Optional["Client"]:
    if not supabase_configured(): return None
    return create_client(safe_secret("SUPABASE_URL"), safe_secret("SUPABASE_SERVICE_ROLE_KEY") or safe_secret("SUPABASE_SECRET_KEY"))

def upsert_progress(row):
    sb = get_supabase_client()
    if sb is None: return False
    pid, qid = row["participant_id"], row["quest_id"]
    found = sb.table("quest_progress").select("*").eq("participant_id", pid).eq("quest_id", qid).limit(1).execute().data or []
    if found: sb.table("quest_progress").update(row).eq("participant_id", pid).eq("quest_id", qid).execute()
    else: sb.table("quest_progress").insert(row).execute()
    return True

def save_app_state_supabase():
    pid = st.session_state.participant_id.strip()
    if not pid or not supabase_configured(): return False
    return upsert_progress({"participant_id": pid, "quest_id": APP_STATE_QUEST_ID, "completed": False, "completed_at": None, "favorite": False, "note": json.dumps(state_dict(), ensure_ascii=False), "photo_uploaded": False, "sns_text": "", "x_post_url": "", "character_id": ""})

def save_quest_supabase(qid):
    pid = st.session_state.participant_id.strip()
    if not pid or not supabase_configured(): return False
    return upsert_progress({"participant_id": pid, "quest_id": qid, "completed": qid in st.session_state.completed, "completed_at": st.session_state.completed_at.get(qid), "favorite": qid in st.session_state.favorites, "note": st.session_state.notes.get(qid, ""), "photo_uploaded": bool(st.session_state.photos.get(qid)), "sns_text": st.session_state.sns_texts.get(qid, ""), "x_post_url": "", "character_id": st.session_state.quest_character_rewards.get(qid, "")})

def save_survey_to_quest_progress(payload):
    pid = st.session_state.participant_id.strip()
    if not pid or not supabase_configured(): return False
    return upsert_progress({"participant_id": pid, "quest_id": SURVEY_QUEST_ID, "completed": True, "completed_at": payload["submitted_at"], "favorite": False, "note": json.dumps(payload, ensure_ascii=False), "photo_uploaded": False, "sns_text": "", "x_post_url": "", "character_id": ""})

def save_user_data():
    try: SAVE_FILE.write_text(json.dumps(state_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass
    try: save_app_state_supabase()
    except Exception: pass

def load_user_data():
    pid = st.session_state.participant_id.strip()
    if pid and supabase_configured():
        try:
            rows = get_supabase_client().table("quest_progress").select("*").eq("participant_id", pid).execute().data or []
            app = next((r for r in rows if r.get("quest_id") == APP_STATE_QUEST_ID), None)
            if app and app.get("note"): apply_state(json.loads(app["note"]))
            survey = next((r for r in rows if r.get("quest_id") == SURVEY_QUEST_ID), None)
            if survey and survey.get("note"):
                st.session_state.survey_answers = json.loads(survey["note"]); st.session_state.survey_submitted = True
            for r in rows:
                qid = r.get("quest_id")
                if not qid or qid in {APP_STATE_QUEST_ID, SURVEY_QUEST_ID} or not get_quest(qid): continue
                if r.get("completed"):
                    st.session_state.completed.add(qid)
                    if qid not in st.session_state.completed_order: st.session_state.completed_order.append(qid)
                    if r.get("completed_at"): st.session_state.completed_at[qid] = r["completed_at"]
                if r.get("note") is not None: st.session_state.notes[qid] = r.get("note") or ""
                if r.get("photo_uploaded"): st.session_state.photos[qid] = "写真添付済み"
                if r.get("character_id"):
                    cid = r["character_id"]; st.session_state.quest_character_rewards[qid] = cid; st.session_state.unlocked_character_ids.add(cid)
                    if cid not in st.session_state.unlocked_character_order: st.session_state.unlocked_character_order.append(cid)
            return
        except Exception: pass
    if SAVE_FILE.exists():
        try: apply_state(json.loads(SAVE_FILE.read_text(encoding="utf-8")))
        except Exception: pass

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
    try: save_quest_supabase(qid)
    except Exception: pass

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
        d = distance(original); st.markdown(f"**現在地から：** {fmt_dist(d)}")
        c1, c2 = st.columns(2)
        if q.get("official_url"): c1.link_button("公式情報", q["official_url"], use_container_width=True)
        c2.link_button("Googleマップ", google_maps_url(original), use_container_width=True)
        note = st.text_area("旅のメモ・感想", value=st.session_state.notes.get(qid, ""), key=f"{scope}_note_{qid}")
        st.session_state.notes[qid] = note
        upload = st.file_uploader("クエスト達成用の写真を添付", type=["jpg", "jpeg", "png", "webp"], key=f"{scope}_photo_{qid}")
        if upload:
            st.session_state.photos[qid] = upload.name; st.session_state.photo_data[qid] = upload.getvalue(); st.session_state.photo_mime[qid] = upload.type or "image/jpeg"; st.image(upload.getvalue(), use_container_width=True)
        elif st.session_state.photos.get(qid): st.success("📷 写真添付済み")
        gps_ok = True
        if st.session_state.gps_required:
            gps_ok = d is not None and d <= st.session_state.gps_radius_m
            if gps_ok: st.success(f"📍 GPS判定OK：{fmt_dist(d)}")
            elif d is None: st.warning("現在地を取得してください。")
            else: st.warning(f"達成範囲外です。現在：{fmt_dist(d)} / 判定半径：{st.session_state.gps_radius_m}m")
        photo_ok = bool(st.session_state.photos.get(qid))
        if not photo_ok: st.info("クリアには写真添付が必要です。")
        if st.button("もう一度クリア演出を見る" if done else "🎉 クエストをクリアする", key=f"{scope}_clear_{qid}", type="primary", disabled=not(gps_ok and photo_ok), use_container_width=True): complete_quest(original); st.rerun()
        if done:
            text = st.text_area("SNS投稿用文章", value=st.session_state.sns_texts.get(qid, make_sns_text(original)), key=f"{scope}_sns_{qid}"); st.session_state.sns_texts[qid] = text
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

def render_diary():
    st.subheader("👣 足跡マップ・旅日記")
    done = [qid for qid in st.session_state.completed_order if qid in st.session_state.completed]
    if folium is not None and st_folium is not None:
        m = folium.Map(location=[32.43, 130.19], zoom_start=9)
        for i, qid in enumerate(done, 1):
            q, c = get_quest(qid), QUEST_COORDS.get(qid)
            if c: folium.Marker(c, tooltip=f"{i}. {q['linked_name']}", icon=folium.Icon(color="green", icon="check")).add_to(m)
        st_folium(m, width=None, height=450, key="diary_map")
    if not done: st.info("まだ足跡はありません。クエストをクリアすると表示されます。"); return
    for qid in reversed(done):
        q = get_quest(qid)
        with st.container(border=True):
            st.markdown(f"**{q['linked_name']}**"); st.caption(st.session_state.completed_at.get(qid, "")[:10]); n = st.text_area("感想", value=st.session_state.notes.get(qid, ""), key=f"diary_{qid}")
            if st.button("日記を保存", key=f"diary_save_{qid}", use_container_width=True): st.session_state.notes[qid] = n; save_user_data(); st.success("保存しました。")

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
        rows = [{"日付": st.session_state.completed_at.get(qid, "")[:10], "場所": get_quest(qid)["linked_name"], "エリア": classified_area(get_quest(qid))} for qid in done]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

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
    st.markdown('''<style>.stApp{background:linear-gradient(180deg,#f8fdff,#fff 45%,#f4fbff)}[data-testid="stMainBlockContainer"]{max-width:1180px;padding-top:1rem}.hero{padding:24px;border-radius:24px;background:linear-gradient(135deg,#1479d3,#55bde9);color:#fff;box-shadow:0 14px 32px rgba(0,80,150,.18);margin-bottom:14px}.hero b{font-size:32px}.stButton>button,.stLinkButton>a{border-radius:14px!important;min-height:46px;font-weight:700}[data-testid="stImage"] img{border-radius:16px}h1,h2,h3{color:#125f9d}@media(max-width:768px){[data-testid="stMainBlockContainer"]{padding:.6rem .7rem 4rem}.hero{padding:18px}.hero b{font-size:27px}[data-testid="stHorizontalBlock"]{flex-wrap:wrap}[data-testid="column"]{min-width:min(100%,250px);flex:1 1 250px!important}}</style>''', unsafe_allow_html=True)

def usage_guide():
    with st.expander("📘 はじめての方へ｜アプリの使い方", expanded=not st.session_state.guide_seen):
        st.markdown("**① クエストを選ぶ** → **② 現地でGPS・写真判定** → **③ キャラクター獲得** → **④ ストーリーにも挑戦** → **⑤ 旅日記を残す** → **⑥ 最後にアンケート回答**")
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
st.markdown('<div class="hero"><b>🌊 天草つながりクエスト</b><br>天草をめぐって、見つけて、集める。あなたの旅をクエストにしよう。</div>', unsafe_allow_html=True)

# URL ?pid=... を参加者IDに反映
try:
    pid_q = st.query_params.get("pid", "")
    if isinstance(pid_q, list): pid_q = pid_q[0] if pid_q else ""
    if pid_q and not st.session_state.participant_id: st.session_state.participant_id = str(pid_q).strip()
except Exception: pass

if not st.session_state.data_loaded: load_user_data(); st.session_state.data_loaded = True

with st.expander("👤 ニックネーム・参加者情報"):
    pid = st.text_input("参加者ID", value=st.session_state.participant_id); nick = st.text_input("ニックネーム", value=st.session_state.nickname)
    if st.button("参加者情報を保存", use_container_width=True): st.session_state.participant_id = pid.strip(); st.session_state.nickname = nick.strip(); save_user_data(); st.success("保存しました。"); st.rerun()

usage_guide(); render_clear_effect()

c1, c2 = st.columns(2)
with c1:
    today = date.today().isoformat()
    if st.session_state.last_login_date != today:
        if st.button("🎁 今日のログインボーナス：🍎3個", use_container_width=True): st.session_state.apples += 3; st.session_state.last_login_date = today; save_user_data(); st.rerun()
    else: st.success(f"🎁 本日受取済み｜所持リンゴ {st.session_state.apples}個")
with c2:
    done_normal = len([q for q in QUESTS if q["quest_id"] in st.session_state.completed]); st.progress(done_normal/len(QUESTS), text=f"参加した通常クエスト：{done_normal}/{len(QUESTS)}")

with st.expander("⚙️ GPS・デモ用現在地設定"):
    st.session_state.gps_required = st.checkbox("GPSで訪問判定する", value=st.session_state.gps_required); st.session_state.gps_radius_m = st.slider("達成判定半径", 50, 1000, int(st.session_state.gps_radius_m), 50)
    if get_geolocation is not None and st.button("📍 ブラウザGPSで現在地を取得", use_container_width=True):
        p = get_geolocation(); coords = p.get("coords", p) if isinstance(p, dict) else {}
        try: set_location(float(coords["latitude"]), float(coords["longitude"]), coords.get("accuracy"), "ブラウザGPS"); st.rerun()
        except Exception: st.warning("位置情報を取得できませんでした。ブラウザの位置情報許可を確認してください。")
    demo = st.selectbox("デモ用：クエスト地点を現在地にする", ["選択しない"] + [q["quest_id"] for q in QUESTS + STORY_QUESTS], format_func=lambda x: x if x == "選択しない" else get_quest(x)["linked_name"])
    if demo != "選択しない" and st.button("この地点に設定", use_container_width=True): c = QUEST_COORDS[demo]; set_location(c[0], c[1], 5, "デモ"); st.rerun()
    if current_location(): st.success(f"現在地：{current_location()[0]:.6f}, {current_location()[1]:.6f}")

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
