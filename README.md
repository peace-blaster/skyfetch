# skyfetch

A small, neofetch-style weather CLI for Linux. One portable Python file, no pip dependencies, no API key. Requires Python 3.8+ and internet access for fresh weather. Runs on any CPU architecture supported by Python; includes a POSIX shell installer.

## Install

Extract the release archive, then run:

```sh
cd skyfetch
sh install.sh
export PATH="$HOME/.local/bin:$PATH"
skyfetch
```

Add the PATH line to your shell profile for future sessions (Bash: `~/.bashrc`; Zsh: `~/.zshrc`). Fish users can run `fish_add_path ~/.local/bin` instead.

The default install copies one executable to `~/.local/bin/skyfetch`, without sudo. You can also run `python3 skyfetch "London, UK"` directly, or copy the file to any directory on your PATH. Use `PREFIX=/some/path sh install.sh` for a custom prefix. Python and system CA certificates must be installed using your distro's package manager if absent.

On first run, a short setup asks for city, state/province, country, and units. It shows matching locations with coordinates and asks you to choose one before saving. For example, enter `Lexington`, `KY`, and `US`, choose the Kentucky result, then select `imperial`. Future runs use those saved coordinates. Run `skyfetch --setup` to change them. Existing saved locations continue working; use `--setup` to review or replace an old default.

Setup needs an interactive terminal. Scripts can use explicit coordinates or a fully qualified city with `--save`; they never receive interactive prompts. A failed weather request after setup does not discard the saved location.

## Usage

```sh
skyfetch --setup
skyfetch "Lexington, Kentucky, US" --units imperial --save
skyfetch Lexington --state KY --country US
skyfetch --forecast
skyfetch Tokyo --country JP
skyfetch Springfield --search
skyfetch --lat 39.78 --lon -89.65 --save
skyfetch --refresh
skyfetch --json
skyfetch --no-color
skyfetch --demo sunny
skyfetch --demo night
skyfetch --demo partly-cloudy-night
skyfetch --demo rain
skyfetch --demo snow
skyfetch --demo storm
```

Use `City, State/Province, Country`, `City, Country`, or separate `--state` / `--province` and `--country` options. US state and Canadian province abbreviations are accepted when the country is US or Canada; otherwise use full region names. Country names and two-letter codes are accepted, including UK as an alias for GB. A two-part query such as `Lexington, US` specifies city and country; use three parts to include a state.

When multiple matches remain, interactive runs ask you to choose. Noninteractive runs report ambiguity instead of selecting a city silently. Use `--search` to list matches and their coordinates. The provider returns at most 100 candidates; if a small locality is absent, use exact coordinates. A city supplied on the command line is temporary unless you use `--save`. With no location argument, saved coordinates are used. There is no IP geolocation.

Current details include temperature, feels-like temperature, dew point, humidity, wind, and precipitation. Dew point comes from Open-Meteo and uses your selected Celsius/Fahrenheit units; unavailable values appear as `--`.

Artwork covers sun, clear night, partial cloud, overcast, rain/drizzle, snow, thunderstorms and fog. Colors follow the condition and are disabled for redirected output, `NO_COLOR`, `TERM=dumb`, or `--no-color`. Narrow terminals stack the artwork above the details. All artwork is ASCII. Clear nights use a large crescent and stars; partly cloudy nights use a moon behind a cloud. The crescent represents nighttime, not the actual lunar phase.

`--forecast` adds today's and the next two days' low/high temperatures, maximum precipitation probability, and conditions. Times are local to the selected location. Demo mode uses clearly labeled sample data and needs no network; it does not include a forecast.

## Updating

Extract the new release and run `sh install.sh` from its `skyfetch` directory again. Your saved location and units are preserved. Version 1.2.3 makes the partly cloudy nighttime crescent smaller. Version 1.2.2 gives the sun a larger rounded outline and moves the nighttime cloud to the lower right of a visible crescent. Version 1.2.1 refines the sunny, partly cloudy, storm, and unknown artwork. Version 1.2.0 added dew point and redesigned artwork. The additional requested field gives weather responses a new cache key, so the first weather lookup after updating needs internet access.

## Cache and configuration

- Defaults: `${XDG_CONFIG_HOME:-~/.config}/skyfetch/config.json`.
- Cache: `${XDG_CACHE_HOME:-~/.cache}/skyfetch/`.
- Results are cached for ten minutes per coordinate/unit combination.
- If a refresh fails, a cache under 24 hours old is displayed with **stale (offline)** and its age. Older data is not used.
- Cache age means time since download; the `Updated` field is the provider's weather timestamp.
- To use the cache offline, run with saved defaults or the same coordinates. A city-name argument requires an online geocoding lookup.
- Network requests time out after 12 seconds each. City lookup and forecast are separate requests.
- JSON output includes location, live/cached/stale status, cache age, and provider weather data. Errors go to stderr; exit codes: 0 success, 1 service/file error, 2 invalid arguments, 130 interrupted.

## Data and terms

Weather: [Open-Meteo](https://open-meteo.com/), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Location data: [GeoNames](https://www.geonames.org/). Weather labels and terminal presentation are derived from the provider's data. Open-Meteo's public API is intended for non-commercial use; commercial deployments must review its [terms and plans](https://open-meteo.com/en/terms).

API references: [forecast](https://open-meteo.com/en/docs) and [geocoding](https://open-meteo.com/en/docs/geocoding-api). Requests send the search term or coordinates to these services. Current weather is model-derived data.

## Uninstall

From the extracted folder, run `sh uninstall.sh` (use the same `PREFIX` if you installed elsewhere). Or, for the default installation:

```sh
rm "$HOME/.local/bin/skyfetch"
```

To also delete saved settings and cached weather:

```sh
rm -rf -- "${XDG_CONFIG_HOME:-$HOME/.config}/skyfetch" "${XDG_CACHE_HOME:-$HOME/.cache}/skyfetch"
```

These commands target only skyfetch's data directories. Custom-prefix installations should remove the executable from that prefix instead.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Tests cover dew point in both units and JSON, missing dew point, narrow layouts, nighttime cloud selection, first-run setup, saved defaults, cancelled setup, ambiguous cities, state/country filtering, noninteractive behavior, every artwork demo, WMO code mapping, cache reuse and expiry, offline fallback, corrupt caches, unit separation, saved coordinates, JSON output, location search, invalid arguments, and network failures. The installer can be tested without changing your home directory with `PREFIX=/tmp/skyfetch-test sh install.sh`.

MIT-licensed application code; see LICENSE. Weather data has its own attribution requirements above.
# skyfetch
# skyfetch
