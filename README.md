# Poracle Middleman

I wasn't satisfied with the way Static Maps and reverse 
geocoding works in Poracle, so I made this. 
Everything here is very opiniated. If you agree with my 
opinion, feel free to use this.

# Features

## Tileserver Middleman

- Host Static Maps on the Discord CDN
- Replace hardcoded template names with your own names

## Reverse Geocoding Middleman

- Use Mapbox with public Nominatim as a fallback
- Produces a hardcoded format: `Suburb: Streetname 10, City` 
or if there's no suburb: `City: Streetname 10`
- Provide your own GeoJSON to overwrite suburb data
- Provide your own GeoJSON with POIs. 
Format if a POI exists: `Suburb POI: Streetname 10, City`

# Setup

- `cp config.example.toml config.toml`
- [Install Poetry](https://python-poetry.org/docs/#installation)
- `poetry install` once and then `poetry run middleman` to start
- You can get the Python executable with `poetry env info`

## Tileserver

- Config should be self-explainatory. `tileserver.replace` can look something like this:

```toml
[tileserver.replace]
"poracle-multi-monster" = "your-template-name"
"poracle-areaoverview" = "your-areoverview"
```

- In your Poracle config, set this:

```json
{
    "staticProvider": "tileservercache",
    "staticProviderURL": "http://127.0.0.1:3031/tileserver"
}
```

## Geocoding

- `suburb_geojson` and `poi_geojson` have to be paths to valid GeoJSON files. 
You can use the provided `files/` directory. Make sure that these GeoJSONs 
only consist of Polygons that have a `name` property. 
If you provide invalid GeoJSONs you'll get an error on start.
- In your Poracle config, set this:
```json
{
    "geocoding": {
        "provider": "nominatim",
        "providerURL": "http://127.0.0.1:3031/geocoder/"
    },
    "locale": {
        "addressFormat": "{{formattedAddress}}"
    }
}
```
- In your Poracle DTS, you can use `{{{addr}}}` to get the correct address
