# Taiwan film locations: sources and resources

Prepared 16 Nov 2026 for Richard DeDomenici's Kaohsiung Redux workshop (around 20–27 Nov 2026), then expanded the same day after the first batch went live.

Files in this folder (and in the app repo under `data/taiwan/`):
- `taiwan_film_locations.csv`: 578 film-to-place rows (137 titles), each with its source URL, where the coordinates came from, and confidence ratings.
- `spots.json`: the same data grouped into 494 map pins, which the app loads from `src/lib/taiwan-locations.ts`.
- `kaohsiung_shortlist.md`: the strongest Kaohsiung Redux candidates.
- Harvest scripts from the first pass (`fk_scrape.py`, `mt_scrape.py`, `build_kh.py`, `curated.py`, `combine.py`, `geo.py`, `make_ts.py`) plus the 16 Nov evening follow-up (`fw_fetch.py`, `round2_harvest.py`, `round2_resume.py`, `regeo_and_merge.py`). Raw pulls live in `/workspace/taiwan-film-locations/` (`fk/`, `mt/`, `fw/`, `wd_taiwan_locs.json`); `geocache.json` holds Nominatim lookups.

## What was live after pull request #1 (morning of 16 Nov 2026)
- **289 pins** (138 Kaohsiung, of which 104 were precise enough for near-you). The moviescenemap atlas on its own still has only a handful of titled Kaohsiung places.
- On the GitHub Pages near-you page, a 10-mile search from Nominatim's "Kaohsiung" point showed **91** of those non-street pins in range (the UI still caps the card list at 40 and says how many are in range).

## Sources harvested

| Source | What it gives | Used for |
|---|---|---|
| **Kaohsiung Film Commission** “來過高雄拍”: https://www.filmkh.org/tc/teams | Productions it supported, with the list of locations used | 156 original rows, plus 33 more in the second pass after retrying official addresses and scene names |
| **filmkh scene database**: https://www.filmkh.org/tc/scene_list | 368 Kaohsiung locations; 329 already had official GPS, and 13 more were placed from the official name or address via Nominatim | Exact coordinates whenever a production's location matched |
| **Metatake** (Taiwan, 58 films): https://metatake.net/locations/taiwan | Scene description and coordinates for each film | 133 rows across classic films (Hou, Yang, Tsai, Life of Pi, Silence, The Assassin and others) |
| **FILMWALKER / 島國拾影** location guide: https://islandtapestry.blogspot.com/p/taiwan-film-location-guide.html | Scene-by-scene posts with a `場景地址` line, covering Hou, Yang, Tsai, Ang Lee, King Hu, Wang Toon and others (72 posts fetched) | 187 rows: named places geocoded as sites, plus honestly marked street/lane pins. House numbers often cannot be resolved in OpenStreetMap, so a numbered address was kept only when Nominatim returned the alley or a named place, not the midpoint of a long main road |
| **Wayward Cloud location survey** (16 Nov 2026): `/workspace/wayward-cloud/wayward_cloud_locations.csv` | Seven high/medium Kaohsiung pins with sources | Lotus Pond pagodas and Spring & Autumn Pavilions; three Light Bridges including the ring/loop bridge; Riverside / Heti Park; the approximate lakeside steps. The Riverside Community apartment interiors were **not** pinned — the exact building is unidentified and the app has no area-level precision. The Taipei Linsen North Road wrap notice and an unmapped rental shop were also omitted |
| TAKAO, UpToGo, WalkerLand, NOWnews, Stunning Asia, film-pilgrimage, TripPlus, QEEQ, Douban, JustTaiwanTour | Curated Kaohsiung and island-wide rows from the first pass | Still in the file |
| TFAI Edward Yang walking route: https://www.tfai.org.tw/zh/program/detail/2c95808288528e1601893da74aba0166 | Jianguo HS, Botanical Garden, Guling St Small Theatre, etc. | Used as a lead; several of those places already appear via FILMWALKER / zh Wikipedia for *A Brighter Summer Day* |
| Wikidata SPARQL and the moviescenemap atlas | Mostly city-level, already in the live atlas | Checked only |
| OpenStreetMap Nominatim (1 request/s, cached, `countrycodes=tw`) | Geocoding | Coordinates where no official GPS existed. Taiwan house numbers are sparsely mapped, so queries used place names and official filmkh addresses, not guessed points |

## Official commission databases checked but not imported as film pins
These are **locations available to hire**, not a film-to-place credit list (unlike filmkh's “來過高雄拍”). Nothing was added from them without a credited production:

- **Taipei Film Commission** scene list: https://www.filmcommission.taipei/scenes_list.aspx and the 2019 *Taipei Cinema Location Guide* PDF. There is also a 協拍紀錄 of productions shot in Taipei, but it does not list the places used.
- **Taichung** scene database: https://www.filmtaichung.org.tw/scenesList
- **New Taipei Film Assist** scene search: https://www.filmassist.ntpc.gov.tw/scene
- **Tainan** production-support place pages: https://asc.tainan.gov.tw/index.php?category=68&modify=place

Worth a later pass if a production list with locations appears, or if a guide names a film at a specific commission site.

## Road-only pins
The first batch had **40** street-level pins (a point somewhere on a named road). A few were tightened (the Jingmei *Cafe. Waiting. Love* shop to 一壽街44巷; some Kaohsiung misses placed on the correct district road). Most remain street-level: filmkh often listed only the road, and Nominatim rarely has the house number. Street-level pins appear on film pages but not on the near-you list.

## Caveats
- `link_conf` rates how sure we are the film was shot at that place. `coord_conf` rates the pin: **high** means official filmkh GPS or a tightly identified landmark, **medium** means a named site from Nominatim, Metatake or a cited survey, and **street-level** means the pin is somewhere on the named road or lane.
- Of the original 158 unlocated filmkh strings, 33 could be placed in the second pass; **118** remain unplaced (private homes, unidentified shops, vague “道路” entries). They stay in `kh_misses.json` and were not guessed. A few retries that snapped to the wrong place (for example 高雄海關 → 湖內國中, or a whole district) were discarded.
- Some English titles are still the Chinese title where the official English name was not confirmed.
- *Dust of Angels* (少年吔，安啦！, 1992) is often linked with Kaohsiung, but sources point to Ruifang, Beigang and Taipei. The filmkh production “少年吔” (2021) is a different film.
- 明德訓練班 is still listed by filmkh as under restoration and not available for shoots.

## The Wayward Cloud — where to watch (checked 16 Nov 2026, Europe/London)
Licences change; confirm on the provider's page before paying. Fuller notes: `/workspace/wayward-cloud/wayward_cloud_viewing.md`.

- **UK streaming, confirmed today:** BFI Player (subscription), Mandarin with English subtitles, certificate 18: https://player.bfi.org.uk/subscription/film/watch-the-wayward-cloud-2004-online
- **Not currently on** MUBI UK, Netflix UK or Disney+ UK. A Prime Video title page exists but JustWatch UK did not list a live UK offer on 16 Nov 2026.
- **UK disc:** Axiom Films Region 2 DVD (2008, AXM557), out of print; second-hand copies circulate. No UK Blu-ray found.
- **Taiwan streaming** was not confirmed (JustWatch Taiwan has no title page). The Kaohsiung Film Archive November 2026 calendar does not list a public screening in the workshop week, though the archive has a real link to the film (volunteers as red-umbrella dancers; 15th-anniversary and 4K-restoration screenings). TFAI made the 4K restoration; on-site or educational access may be possible by enquiry.
