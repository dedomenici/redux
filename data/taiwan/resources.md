# Taiwan film locations: sources and resources

Prepared 16 Nov 2026 for Richard DeDomenici's Kaohsiung Redux workshop (around 20–27 Nov 2026).

Files in this folder:
- `taiwan_film_locations.csv`: 352 film-to-place rows (101 titles), each with its source URL, where the coordinates came from, and confidence ratings.
- `spots.json`: the same data grouped into 289 map pins. This is what the app uses, in `src/lib/taiwan-locations.ts` on branch `taiwan-locations`.
- `kaohsiung_shortlist.md`: the strongest Kaohsiung Redux candidates.
- Harvest scripts: `fk_scrape.py` (filmkh productions), `mt_scrape.py` (Metatake), `build_kh.py`, `curated.py`, `combine.py` and `make_ts.py`. Raw pulls are in `fk/`, `mt/` and `wd_taiwan_locs.json`, and `geocache.json` holds the Nominatim lookups.

## What the app had before
- The app keeps no location data of its own. It asks the moviescenemap.com atlas (built from Wikidata) live.
- The atlas has **137 places in Taiwan, but only 28 of them have any film credited** (57 credits in total, mostly *Lucy*, *Zone Pro Site* and *Hotel Saltwater*).
- Within 30 km of central Kaohsiung there were **11 places, and 4 of them had a title**: *Hotel Saltwater* ×3 and *The Zoo* at Shoushan Zoo.

## Sources harvested
| Source | What it gives | Used for |
|---|---|---|
| **Kaohsiung Film Commission / 高雄市政府文化局影視發展暨拍片支援中心** “來過高雄拍” production list: https://www.filmkh.org/tc/teams | Every production it supported, with director, date and the **list of locations it used** (45 films, 49 TV, 88 shorts) | 156 Kaohsiung rows (feature films plus TV dramas) |
| **filmkh scene database 場景資料庫**: https://www.filmkh.org/tc/scene_list (EN: https://www.filmkh.org/en/scene_list) | 368 Kaohsiung locations with official GPS, addresses and access notes | Exact coordinates whenever a production's location matched a database entry |
| **Metatake** (Taiwan, 58 films): https://metatake.net/locations/taiwan | Locations for each film with a short scene description and coordinates | 133 rows across 22 classic films (Hou, Yang, Tsai, Life of Pi, Silence, The Assassin and others) |
| **TAKAO 樂高雄** (Kaohsiung government magazine): https://takao.kcg.gov.tw/article/2856 (EN), https://takao.kcg.gov.tw/article/1670, /198, /196 | History of Kaohsiung on film (Eight Hundred Heroes, Boys from Fengkuei, Three Times, Black & White, Detention, Fighting Fish…) | Curated Kaohsiung rows |
| UpToGo Kaohsiung film locations: https://uptogo.com.tw/娛樂/電影/電影-高雄取景？/ | Black & White, 18×2, 命中註定那頭鵝, BIG and more, with a table | Curated Kaohsiung rows |
| WalkerLand Kaohsiung: https://www.walkerland.com.tw/article/view/80448 | The Wayward Cloud, No Puedo Vivir Sin Ti, 帶我去遠方, Pulling a River and others | Curated rows |
| NOWnews / Kaohsiung Film Archive Yancheng walk: https://www.nownews.com/news/2447508 | Five-metal street, Qixian Building, hat shop | Curated rows |
| Stunning Asia (box-office hits): https://stunning-asia.com/smart-travel/the-filming-locations-of-top-mandarin-movies/ | Apple of My Eye, More Than Blue, Our Times | Curated rows |
| 電影朝聖 *Our Times* walk: https://film-pilgrimage.com/2017/05/22/《我的少女時代》場景遊/ | 13 *Our Times* locations with addresses | Curated rows |
| TripPlus: https://blog.tripplus.cc/zh/129164/audrina_newbie_taiwanese_drama_for_location | Monga, Secret, Little Big Women, The Bold the Corrupt and the Beautiful, Cape No. 7 | Curated rows |
| QEEQ: https://guides.qeeq.com/zh-TW/c/p/10000002/t/194/89/ | Secret, Eternal Summer, Island Etude, Life of Pi | Curated rows |
| Douban “40部电影带你走遍台湾”: https://site.douban.com/106545/widget/notes/4551795/note/170707721/ | 40 films around the island | Curated rows, with more left to mine |
| JustTaiwanTour: https://www.justaiwantour.com/filming-locations-in-taiwan/ | Life of Pi, Lucy, Silence, Left-Handed Girl | Curated rows |
| Wikidata SPARQL (P915/P840 with a P17=Taiwan location) | 90 film-place pairs, almost all city level and already in the atlas | Checked only; nothing new |
| OpenStreetMap Nominatim | Geocoding (1 request per second, cached) | Coordinates where no official GPS existed |

## More resources for the workshop (not harvested yet)
- **Taipei Film Commission 台北市電影委員會** scene database: https://www.filmcommission.taipei/scenes_list.aspx, plus the PDF *Taipei Cinema Location Guide 2019*: https://www.filmcommission.taipei/fckShared/images/taipeifilmcommission/files/出版品/TaipeiCinemaLocationGuide2019.pdf
- **Taipei 影劇地圖** (Taipei Pictorial, Nov 2019): https://www.travel.taipei/zh-tw/pictorial/article/22100
- **TFAI 國家電影及視聽文化中心** Edward Yang walking route (Jianguo HS, Botanical Garden, Guling St…): https://www.tfai.org.tw/zh/program/detail/2c95808288528e1601893da74aba0166. TFAI also hosts the Taiwan Cinema database: https://www.tfai.org.tw
- **Kaohsiung Film Archive 高雄市電影館**, on the Love River in Yancheng and an obvious partner and meeting point: https://kfa.kcg.gov.tw. It has run 鹽埕 film-location bike walks and a Kaohsiung-on-screen blind-box series (風櫃來的人, 少年吔安啦, 天邊一朵雲).
- **島國拾影．走電影的人 FILMWALKER** blog, with very detailed scene-by-scene location posts (A Brighter Summer Day in Pingtung, Dust of Angels and more): https://islandtapestry.blogspot.com/ and https://taiwantravelforever.blogspot.com/2016/08/blog-post_18.html
- Taiwan Scene on Hou and Yang locations: https://taiwan-scene.com/2024/02/05/the-taiwan-of-hou-hsiao-hsien-and-edward-yang/
- Chinese Wikipedia film articles, whose 「拍攝」/「取景」 sections are often more detailed than the English ones (e.g. 牯嶺街少年殺人事件).
- IMDb filming-locations pages (`/title/ttXXXX/locations/`). The app already links them for every film.
- The filmkh pages for TV productions and short films (another 137) are in `fk/teams.json` but not all are on the map.

## Caveats
- `link_conf` rates how sure we are the film was shot at that place. `coord_conf` rates the pin: **high** means official filmkh GPS, **medium** means a Metatake or Nominatim point for a named site, and **street-level** means the pin is somewhere on the named road. Street-level pins appear on film pages but not on the near-you list.
- Of the filmkh location strings, 158 could not be placed safely, such as private homes, shops with no map entry, or vague “鳳山區道路” entries. They are listed in `kh_misses.json` and were not guessed.
- Some English titles are left blank where I couldn't confirm the official one. The Chinese title is used instead (for example 鬥魚, 江湖無難事, 癡情男子漢).
- Two Metatake *Yi Yi* pins had coordinates in the wrong district, so I dropped them.
- 少年吔，安啦！ (Dust of Angels, 1992) is often linked with Kaohsiung, but its sources point to Ruifang, Beigang and Taipei. The filmkh production “少年吔” (2021) is a different film.
- 明德訓練班 is marked on filmkh as “修復中，暫不外借” (under restoration, not available for shoots).
