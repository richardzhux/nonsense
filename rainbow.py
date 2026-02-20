import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

import pytz
import pysolar.solar
from astral import LocationInfo
from astral.sun import sun
from geopy.distance import geodesic
from geopy.point import Point

# Core optics constants
RAINBOW_ANGLE_DEG = 42.0

# Demo coordinates for six fountains (replace with your own points)
FOUNTAINS: Sequence[Tuple[float, float]] = [
    (40.00018, -100.00045),
    (39.99992, -100.00062),
    (40.00005, -100.00084),
    (40.00027, -100.00079),
    (40.00034, -100.00055),
    (40.00014, -100.00066),
]

CENTRAL_LAT, CENTRAL_LON = 40.00014, -100.00066


@dataclass
class VisualizationConfig:
    """Tunable parameters for the visualization."""

    sun_line_length_m: float = 700.0
    timezone: str = "America/Chicago"
    eye_height_m: float = 1.6
    droplet_heights_m: Sequence[float] = field(default_factory=lambda: (2.0, 3.5, 5.0))
    theta_min_deg: float = 40.0
    theta_max_deg: float = 42.0
    lateral_spread_deg: float = 18.0
    sector_samples: int = 24
    include_all_fountains: bool = True


MAP_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Rainbow Visibility Explorer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link href="https://unpkg.com/maplibre-gl@3.6.1/dist/maplibre-gl.css" rel="stylesheet" />
    <style>
        body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }}
        #map {{ position: absolute; inset: 0; }}
        .info-panel {{
            position: absolute;
            top: 12px;
            left: 12px;
            padding: 12px 14px;
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.85);
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(6px);
            max-width: 320px;
            font-size: 14px;
            line-height: 1.45;
        }}
        .info-panel h1 {{
            font-size: 16px;
            margin: 0 0 6px 0;
            color: #f472b6;
        }}
        .info-panel kbd {{
            font-size: 12px;
            background: rgba(148, 163, 184, 0.2);
            border-radius: 4px;
            padding: 2px 6px;
            margin-left: 4px;
        }}
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px 12px;
            margin-top: 8px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .swatch {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 1px solid rgba(15, 23, 42, 0.7);
        }}
        .swatch.sun {{ background: #facc15; }}
        .swatch.zone {{ background: linear-gradient(90deg, #34d399, #f472b6); border-radius: 2px; width: 28px; }}
        .swatch.edge {{ background: #0ea5e9; border-radius: 2px; width: 20px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel" id="info-panel"></div>
    <script src="https://unpkg.com/maplibre-gl@3.6.1/dist/maplibre-gl.js"></script>
    <script>
        const geojson = {geojson};
        const metadata = {metadata};

        const map = new maplibregl.Map({{
            container: 'map',
            style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
            center: [{center_lon}, {center_lat}],
            zoom: {zoom}
        }});

        map.addControl(new maplibregl.NavigationControl({{ visualizePitch: true }}));

        map.on('load', () => {{
            map.addSource('rainbow', {{
                type: 'geojson',
                data: geojson
            }});

            map.addLayer({{
                id: 'viewing-zone-fill',
                type: 'fill',
                source: 'rainbow',
                filter: ['==', ['get', 'kind'], 'view-zone'],
                paint: {{
                    'fill-color': [
                        'interpolate',
                        ['linear'],
                        ['get', 'height'],
                        1.0, '#34d399',
                        3.0, '#fbbf24',
                        5.0, '#f472b6'
                    ],
                    'fill-opacity': 0.35
                }}
            }});

            map.addLayer({{
                id: 'viewing-zone-outline',
                type: 'line',
                source: 'rainbow',
                filter: ['==', ['get', 'kind'], 'view-zone'],
                paint: {{
                    'line-color': '#0ea5e9',
                    'line-width': 1.5
                }}
            }});

            map.addLayer({{
                id: 'sun-direction',
                type: 'line',
                source: 'rainbow',
                filter: ['==', ['get', 'kind'], 'sun-line'],
                paint: {{
                    'line-color': '#facc15',
                    'line-width': 4
                }}
            }});

            map.addLayer({{
                id: 'fountains',
                type: 'circle',
                source: 'rainbow',
                filter: ['==', ['get', 'kind'], 'fountain'],
                paint: {{
                    'circle-radius': 5,
                    'circle-color': '#38bdf8',
                    'circle-stroke-color': '#0f172a',
                    'circle-stroke-width': 1.5
                }}
            }});

            map.addLayer({{
                id: 'fountain-labels',
                type: 'symbol',
                source: 'rainbow',
                filter: ['==', ['get', 'kind'], 'fountain'],
                layout: {{
                    'text-field': ['get', 'label'],
                    'text-size': 12,
                    'text-offset': [0, 1.2]
                }},
                paint: {{
                    'text-color': '#e2e8f0',
                    'text-halo-color': '#0f172a',
                    'text-halo-width': 1
                }}
            }});
        }});

        const infoPanel = document.getElementById('info-panel');
        const sunrise = new Date(metadata.sunrise).toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});
        const sunset = new Date(metadata.sunset).toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});
        const generated = new Date(metadata.generatedAt).toLocaleString();
        infoPanel.innerHTML = `
            <h1>${{metadata.title}}</h1>
            <div><strong>Sun altitude:</strong> ${{metadata.sunAltitude.toFixed(2)}}°</div>
            <div><strong>Sun azimuth:</strong> ${{metadata.sunAzimuth.toFixed(2)}}°</div>
            <div><strong>Eye height:</strong> ${{metadata.eyeHeight.toFixed(2)}} m</div>
            <div><strong>Droplet heights:</strong> ${{metadata.dropletHeights.join(', ')}} m</div>
            <div><strong>Sunrise / Sunset:</strong> ${{sunrise}} / ${{sunset}}</div>
            <div><strong>Generated:</strong> ${{generated}}</div>
            <div class="legend">
                <span class="legend-item"><span class="swatch sun"></span>Sun ray</span>
                <span class="legend-item"><span class="swatch zone"></span>Viewing band</span>
                <span class="legend-item"><span class="swatch edge"></span>Band outline</span>
            </div>
        `;
    </script>
</body>
</html>
"""


def project_point(lat: float, lon: float, bearing_deg: float, distance_m: float) -> Tuple[float, float]:
    """Geodesic projection that respects the Earth ellipsoid and azimuth."""
    origin = Point(lat, lon)
    destination = geodesic(meters=distance_m).destination(origin, bearing_deg)
    return destination.latitude, destination.longitude


def get_sun_position(lat: float, lon: float, date_time) -> Tuple[float, float]:
    """Return solar altitude and azimuth for the supplied moment."""
    altitude = pysolar.solar.get_altitude(lat, lon, date_time)
    azimuth = pysolar.solar.get_azimuth(lat, lon, date_time)
    return altitude, azimuth


def get_sunrise_sunset(lat: float, lon: float, date_time, timezone: str) -> Tuple[datetime, datetime]:
    location = LocationInfo(latitude=lat, longitude=lon)
    sun_info = sun(location.observer, date=date_time)
    tz = pytz.timezone(timezone)
    return sun_info["sunrise"].astimezone(tz), sun_info["sunset"].astimezone(tz)


def viewing_radius(delta_z: float, theta_deg: float, sun_altitude_deg: float) -> Optional[float]:
    """Solve for the horizontal range where observers can stand for a droplet/angle."""
    phi_deg = theta_deg - sun_altitude_deg
    tan_phi = math.tan(math.radians(phi_deg))
    if abs(tan_phi) < 1e-6:
        return None
    radius = delta_z / tan_phi
    if not math.isfinite(radius) or radius <= 0:
        return None
    return radius


def make_view_zone_feature(
    lat: float,
    lon: float,
    fountain_label: str,
    droplet_height_m: float,
    sun_azimuth: float,
    sun_altitude: float,
    config: VisualizationConfig,
) -> Optional[Dict]:
    """Build a GeoJSON polygon describing the ground viewing band for a droplet height."""
    delta_z = droplet_height_m - config.eye_height_m
    radius_far = viewing_radius(delta_z, config.theta_max_deg, sun_altitude)
    radius_near = viewing_radius(delta_z, config.theta_min_deg, sun_altitude)
    if radius_far is None or radius_near is None:
        return None

    inner = min(radius_far, radius_near)
    outer = max(radius_far, radius_near)
    if inner <= 0 or outer <= 0 or inner >= outer:
        return None

    bearing_center = (sun_azimuth + 180.0) % 360.0
    start_bearing = bearing_center - config.lateral_spread_deg
    end_bearing = bearing_center + config.lateral_spread_deg
    samples = max(2, int(config.sector_samples))
    step = (end_bearing - start_bearing) / (samples - 1)

    outer_points: List[Tuple[float, float]] = []
    for i in range(samples):
        bearing = start_bearing + step * i
        lat_o, lon_o = project_point(lat, lon, bearing, outer)
        outer_points.append((lon_o, lat_o))

    inner_points: List[Tuple[float, float]] = []
    for i in range(samples):
        bearing = end_bearing - step * i
        lat_i, lon_i = project_point(lat, lon, bearing, inner)
        inner_points.append((lon_i, lat_i))

    ring = outer_points + inner_points + [outer_points[0]]
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {
            "kind": "view-zone",
            "height": droplet_height_m,
            "label": fountain_label,
            "radiusMin": inner,
            "radiusMax": outer,
            "bearing": bearing_center,
        },
    }


def build_geojson(
    sun_azimuth: float,
    sun_altitude: float,
    config: VisualizationConfig,
) -> Dict:
    """Create the GeoJSON payload used by MapLibre."""
    features: List[Dict] = []

    def append_point(lat: float, lon: float, label: str) -> None:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {"kind": "fountain", "label": label},
            }
        )

    for idx, (lat, lon) in enumerate(FOUNTAINS, start=1):
        if idx == len(FOUNTAINS):
            label = "Centrale"
        else:
            label = f"Fountain {idx}"
        include_fountain = config.include_all_fountains or label == "Centrale"
        if include_fountain:
            append_point(lat, lon, label)
            for height in config.droplet_heights_m:
                feature = make_view_zone_feature(
                    lat,
                    lon,
                    label,
                    height,
                    sun_azimuth,
                    sun_altitude,
                    config,
                )
                if feature:
                    features.append(feature)

    sun_start = (CENTRAL_LON, CENTRAL_LAT)
    sun_end_lat, sun_end_lon = project_point(
        CENTRAL_LAT, CENTRAL_LON, sun_azimuth, config.sun_line_length_m
    )
    features.append(
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [list(sun_start), [sun_end_lon, sun_end_lat]],
            },
            "properties": {"kind": "sun-line"},
        }
    )

    return {"type": "FeatureCollection", "features": features}


def render_map_html(geojson: Dict, metadata: Dict) -> str:
    """Populate the HTML template with the current scene."""
    return MAP_TEMPLATE.format(
        geojson=json.dumps(geojson),
        metadata=json.dumps(metadata),
        center_lat=CENTRAL_LAT,
        center_lon=CENTRAL_LON,
        zoom=17,
    )


def create_map_for_time(date_time, filename: str, config: VisualizationConfig) -> str:
    """Generate the HTML file for the requested instant."""
    sun_altitude, sun_azimuth = get_sun_position(CENTRAL_LAT, CENTRAL_LON, date_time)
    sunrise, sunset = get_sunrise_sunset(CENTRAL_LAT, CENTRAL_LON, date_time, config.timezone)

    timestamp_str = date_time.strftime("%Y.%m.%d.%H%M")
    sunrise_str = sunrise.strftime("%Y.%m.%d.%H%M")
    sunset_str = sunset.strftime("%Y.%m.%d.%H%M")

    print(timestamp_str)
    print(f"Sunrise: {sunrise_str}, Sunset: {sunset_str}")
    print(f"Sun Altitude: {sun_altitude:.2f}°, Sun Azimuth: {sun_azimuth:.2f}°")

    if sun_altitude <= 0:
        print("Rainbow not visible, the Sun is below the horizon.")
        return ""
    if sun_altitude >= RAINBOW_ANGLE_DEG:
        print("Rainbow not visible, the Sun is too high.")
        return ""

    print("Calculating rainbow visibility… 🌈")
    geojson = build_geojson(sun_azimuth, sun_altitude, config)

    metadata = {
        "title": "Rainbow Visibility",
        "sunAltitude": sun_altitude,
        "sunAzimuth": sun_azimuth,
        "sunrise": sunrise.isoformat(),
        "sunset": sunset.isoformat(),
        "generatedAt": date_time.isoformat(),
        "eyeHeight": config.eye_height_m,
        "dropletHeights": list(config.droplet_heights_m),
        "thetaRange": [config.theta_min_deg, config.theta_max_deg],
    }

    html = render_map_html(geojson, metadata)

    output_folder = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_folder, f"{filename}.html")
    with open(output_path, "w", encoding="utf-8") as fp:
        fp.write(html)

    print(f"Map saved to {output_path}")
    return output_path


def validate_time_input(time_input: str) -> Optional[datetime]:
    """
    Validate and parse time in yyyy.mm.dd.hhmm format.
    Automatically adjusts for input format and forbids dates before October 15, 1582.
    """
    try:
        parts = time_input.split(".")
        if len(parts) != 4:
            print("Invalid time format. Please use 'yyyy.mm.dd.hhmm'.")
            return None

        year, month, day, time_part = parts

        if not (1582 <= int(year) <= 9999):
            print("Invalid year. The year must be between 1582 and 9999.")
            return None

        if not (1 <= int(month) <= 12):
            print("Invalid month. The month must be between 1 and 12.")
            return None
        month = month.zfill(2)

        if not (1 <= int(day) <= 31):
            print("Invalid day. The day must be between 1 and 31.")
            return None
        day = day.zfill(2)

        if len(time_part) != 4 or not time_part.isdigit():
            print("Invalid time format. The time must be exactly 4 digits in hhmm format.")
            return None
        hour = int(time_part[:2])
        minute = int(time_part[2:])

        if not (0 <= hour < 24):
            print("Invalid hour. Hours should be between 0 and 23.")
            return None
        if not (0 <= minute < 60):
            print("Invalid minutes. Minutes should be between 0 and 59.")
            return None

        formatted_input = f"{year.zfill(4)}-{month}-{day} {time_part[:2]}:{time_part[2:]}"
        time_obj = datetime.strptime(formatted_input, "%Y-%m-%d %H:%M")
        cutoff_date = datetime(1582, 10, 15)
        if time_obj < cutoff_date:
            print("Invalid date. The date must be after October 15, 1582.")
            return None

        return time_obj
    except ValueError:
        print("Invalid date or time. Please check your input.")
        return None


def main() -> None:
    config = VisualizationConfig()
    tz = pytz.timezone(config.timezone)

    while True:
        choice = input(
            "Enter 'current' for current time, 'custom' for yyyy.mm.dd.hhmm, or 'q' to quit: "
        ).strip().lower()

        if choice in {"q", "esc"}:
            print("Exiting program.")
            break

        if choice == "current":
            current_time = datetime.now(tz)
            create_map_for_time(current_time, f"rainbow_viewline_{current_time:%Y%m%d_%H%M}", config)
            continue

        if choice == "custom":
            custom_date_time_str = input("Enter the date and time (yyyy.mm.dd.hhmm): ").strip()
            custom_date_time = validate_time_input(custom_date_time_str)
            if not custom_date_time:
                print("Invalid date/time input. Please try again.")
                continue
            custom_date_time = tz.localize(custom_date_time)
            create_map_for_time(custom_date_time, f"rainbow_visibility_{custom_date_time_str}", config)
            continue

        print("Invalid input. Please enter 'current', 'custom', or 'q'.")


if __name__ == "__main__":
    main()
