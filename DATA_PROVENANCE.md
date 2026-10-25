# Data provenance

Every file in `data/` is a frozen snapshot. The analysis reads nothing else and
needs no network access. `data/SHA256SUMS` lists the checksum of each file;
`reproduce.py` verifies them before it runs. All times are Japan Standard Time
(UTC+9), and every hourly or 5-minute timestamp `t0` is the start of its interval.

## Summary

| Files | Source | Licence | Version | Built or fetched |
|---|---|---|---|---|
| `5min_<site>_<class>.parquet` (8 files) | Code for FUKUI, [fukui-kanko-people-flow-data](https://github.com/code4fukui/fukui-kanko-people-flow-data) (Fukui Prefecture tourism AI-camera open data) | MIT | commit `b89bc2ce26743f08e54468cbf33081dd30a3965f` (also in `data/COMMIT`), data 2024-12-20 to 2026-10-10 | built 2026-10-11 |
| `jma_<site>.parquet` (3 files) | Japan Meteorological Agency (JMA), past weather data search (ETRN), hourly station observations | Public data; source: Japan Meteorological Agency | hourly, 2024-12-01 to 2026-10-11 | built 2026-10-12 |
| `weather_<site>.parquet` (3 files) | [Open-Meteo](https://open-meteo.com/) historical weather API (`archive-api.open-meteo.com/v1/archive`) | CC BY 4.0 | hourly, 2024-12-20 to 2026-10-10 | fetched 2026-10-11 (21:13 to 21:16) |
| `fcst7_<site>.parquet` (3 files) | Open-Meteo previous model runs API (`previous-runs-api.open-meteo.com/v1/forecast`) | CC BY 4.0 | hourly, 2025-09-01 to 2026-10-10, forecasts issued 1 to 7 days earlier | fetched 2026-10-12 (12:51) |

Fetch and build dates are the file modification times of the original snapshots
on the analysis machine and the shared compute server; both copies have the
checksums in `data/SHA256SUMS`. The same files are committed with the same
checksums in [amilkh/icaisc-camera-scans](https://github.com/amilkh/icaisc-camera-scans),
whose scripts `build_data.py`, `get_jma.py`, `get_weather.py` and `get_forecasts.py`
produced them. Those scripts are not included here because they download or
rebuild the inputs; re-running them against the live services would change the
inputs (Open-Meteo revises its archive after the fact).

## Camera counts

Fukui Prefecture publishes counts from edge AI cameras that run object
detection on the device, so only counts leave the camera. The data are
released by Code for FUKUI under the MIT licence. We used commit
`b89bc2ce26743f08e54468cbf33081dd30a3965f` (data through 2026-10-10).

`build_data.py` in the full repository read the repository's 5-minute CSV files
at that commit with `git archive`, concatenated them per camera and object
class, renamed `aggregate from`, `aggregate to` and `total count` to `t0`, `t1`
and `count`, dropped the `placement` and `object class` columns (the site and
class are in the file name), sorted
by `t0` and kept the last row of any duplicated `t0`. Nothing else was changed.

| File | Site | Object class | Used for |
|---|---|---|---|
| `5min_fukui-station-east-entrance_Person.parquet` | Fukui Station, east entrance | people | all analyses |
| `5min_tojinbo-shotaro_Person.parquet` | Tojinbo shopping street | people | all analyses |
| `5min_rainbow-line-parking-lot-1-gate_LicensePlate.parquet` | Rainbow Line car park 1 gate | vehicles (plates) | all analyses; plate-origin columns in scan01 |
| `5min_rainbow-line-parking-lot-2-gate_LicensePlate.parquet` | Rainbow Line car park 2 (overflow) gate | vehicles (plates) | overflow warning, Table I |
| `5min_rainbow-line-parking-lot-1-gate_Face.parquet`, `..._lot-2-gate_Face.parquet` | Rainbow Line gates | faces | faces vs plates check |
| `5min_fukui-station-east-entrance_Face.parquet`, `5min_tojinbo-shotaro_Face.parquet` | station, Tojinbo | faces | face share and age mix (Data section) |

The plate files hold aggregate counts by registration prefecture and vehicle
kind; the face files hold aggregate counts by estimated sex and age band. No
plate numbers, images or other personal data are included.

## JMA observations

Hourly observations from the nearest JMA stations, matched to sites as follows:
Fukui City (Fukui Station), Mikuni AMeDAS (Tojinbo) and Mihama AMeDAS (Rainbow
Line). Source: Japan Meteorological Agency, ETRN past weather data search,
https://www.data.jma.go.jp/stats/etrn/ (accessed 12 October 2026).

`get_jma.py` in the full repository merged the cleaned hourly files from the
authors' earlier DHDE study (to early March 2026) with monthly pages fetched
from ETRN afterwards, shifted JMA's hour-ending timestamps to hour starting,
and renamed the columns to the Open-Meteo names so the same code reads both
sources. Two conventions to note: the export has no gust column, so
`wind_gusts_10m` holds the hourly mean wind (the paper's "highest hourly mean
wind"); and wherever temperature is present, missing rainfall is set to zero
(JMA main stations print "--" when no precipitation was observed). Sunshine is stored in seconds
per hour.

## Open-Meteo

Open-Meteo weather data, https://open-meteo.com/, licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Cite as
P. Zippenfenig, "Open-Meteo.com Weather API," Zenodo, 2024,
doi:10.5281/ZENODO.7970649.

Requests used `timezone=Asia/Tokyo` and `wind_speed_unit=ms` at these
approximate camera locations:

| Site key | Latitude | Longitude |
|---|---|---|
| `station` | 36.062 | 136.223 |
| `tojinbo` | 36.238 | 136.125 |
| `rainbow` | 35.597 | 135.885 |

- `weather_<site>.parquet`: historical weather API, 2024-12-20 to 2026-10-10,
  variables `temperature_2m, precipitation, snowfall, wind_speed_10m,
  wind_gusts_10m, sunshine_duration, cloud_cover`. Used for the Open-Meteo
  check of Table II and as observed training weather for the forecast models.
- `fcst7_<site>.parquet`: previous model runs API, 2025-09-01 to 2026-10-10,
  variables `precipitation, temperature_2m, wind_gusts_10m,
  sunshine_duration`, each as `<variable>_previous_day<h>` for h = 1 to 7, the
  forecast for that hour issued h days earlier. Used at test time in Tables III
  and IV, Fig. 3 and the forecast-weather cold-start check.

## Verifying the files

```sh
cd data && sha256sum -c SHA256SUMS      # Linux
cd data && shasum -a 256 -c SHA256SUMS  # macOS
```
