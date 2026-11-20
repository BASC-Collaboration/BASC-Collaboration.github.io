#!/usr/bin/env python3
"""
collaboration_map.py
--------------------
Generate a collaboration map spanning the US and Europe in one of two
styles:

  * "photos"  - circular headshot bubbles around the edges, one per
                person, each with a leader line to their location.
  * "labels"  - no photos. People are GROUPED BY INSTITUTION into tidy
                label boxes, each with a single leader line to the
                institution's location. This is the cleaner option when
                several members share an affiliation.

Pick the style at the bottom (STYLE = ...) or on the command line:

    python collaboration_map.py photos
    python collaboration_map.py labels

Requirements:
    pip install cartopy matplotlib pillow geopy

Using your own data:
    1. Edit the PEOPLE list below. People at the same institution should
       share the same `affil` text and `coords`; the "labels" style will
       merge them into one box automatically.
    2. (photos style only) Put headshots in IMAGE_DIR. A missing photo
       falls back to a colored disk with initials, so it always runs.
    3. Leave coords=None to auto-geocode by city name (needs internet).
"""

import os
import sys
from collections import OrderedDict

import numpy as np

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox, TextArea,
                                  VPacker)
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------
# 1. DATA
# ----------------------------------------------------------------------
# coords = (longitude, latitude). Set to None to auto-geocode the city.
# People at the same institution MUST share identical affil + coords so
# the "labels" style can group them.
PEOPLE = [
    dict(name="Amy Nicholson",        photo="nicholson.jpg",
         affil="University of North Carolina",
         city="Chapel Hill, NC, USA",
         coords=(-79.0558, 35.9132), country="US"),
    dict(name="Andrew Hanlon",        photo="hanlon.jpg",
         affil="Kent State University", city="Kent, OH, USA",
         coords=(-81.3412, 41.1467), country="US"),
    dict(name="John Bulava",          photo="bulava.jpg",
         affil="Ruhr-Universität Bochum", city="Bochum, Germany",
         coords=(7.2620, 51.4818), country="DE"),
    dict(name="Herzallah Alharazin",   photo="alharazin.jpg",
         affil="Ruhr-Universität Bochum", city="Bochum, Germany",
         coords=(7.2620, 51.4818), country="DE"),
    dict(name="André Baião Raposo",   photo="raposo.jpg",
         affil="Ruhr-Universität Bochum", city="Bochum, Germany",
         coords=(7.2620, 51.4818), country="DE"),
    dict(name="Colin Morningstar",    photo="morningstar.jpg",
         affil="Carnegie Mellon University", city="Pittsburgh, PA, USA",
         coords=(-79.9959, 40.4406), country="US"),
    dict(name="Joseph Delmar",    photo="delmar.jpg",
         affil="Carnegie Mellon University", city="Pittsburgh, PA, USA",
         coords=(-79.9959, 40.4406), country="US"),
    dict(name="John Meneghini",    photo="meneghini.jpg",
         affil="Carnegie Mellon University", city="Pittsburgh, PA, USA",
         coords=(-79.9959, 40.4406), country="US"),
    dict(name="Davide Laudicina",     photo="laudicina.jpg",
         affil="Ruhr-Universität Bochum", city="Bochum, Germany",
         coords=(7.2620, 51.4818), country="DE"),
    dict(name="Henry Monge-Camacho",  photo="mongecamacho.jpg",
         affil="Oak Ridge National Laboratory",
         city="Oak Ridge, TN, USA",
         coords=(-84.3137, 35.9310), country="US"),
    dict(name="Pavlos Vranas",        photo="vranas.jpg",
         affil="Lawrence Livermore National Laboratory",
         city="Livermore, CA, USA",
         coords=(-121.7680, 37.6819), country="US"),
    dict(name="Srijit Paul",          photo="paul.jpg",
         affil="University of Cyprus", city="Nicosia, Cyprus",
         coords=(33.3823, 35.1856), country="CY"),
    dict(name="Jeremy Green",         photo="green.jpg",
         affil="DESY Zeuthen/Humboldt-Universität",
         city="Zeuthen/Berlin, Germany",
         coords=(13.5100, 52.4300), country="DE"),
    dict(name="Jorge Baeza Ballesteros", photo="baeza.jpg",
         affil="DESY Zeuthen/Humboldt-Universität",
         city="Zeuthen/Berlin, Germany",
         coords=(13.5100, 52.4300), country="DE"),
    dict(name="Andres Stump",         photo="stump.jpg",
         affil="DESY Zeuthen/Humboldt-Universität",
         city="Zeuthen/Berlin, Germany",
         coords=(13.5100, 52.4300), country="DE"),
    dict(name="André Walker-Loud",    photo="walkerloud.jpg",
         affil="Lawrence Berkeley National Laboratory",
         city="Berkeley, CA, USA",
         coords=(-122.2547, 37.8760), country="US"),
    dict(name="Fernando Romero-López", photo="romerolopez.jpg",
         affil="University of Bern", city="Bern, Switzerland",
         coords=(7.4380, 46.9509), country="CH"),
    dict(name="Miguel Salg",          photo="salg.jpg",
         affil="University of Bern", city="Bern, Switzerland",
         coords=(7.4380, 46.9509), country="CH"),
    dict(name="Haobo Yan",          photo="haobo.jpg",
         affil="University of Bern", city="Bern, Switzerland",
         coords=(7.4380, 46.9509), country="CH"),
    dict(name="Hartmut Wittig",       photo="wittig.jpg",
         affil="Johannes Gutenberg Universität Mainz",
         city="Mainz, Germany",
         coords=(8.2330, 49.9929), country="DE"),
    dict(name="Daniel Mohler",       photo="mohler.jpg",
         affil="Technische Universität Darmstadt",
         city="Darmstadt, Germany",
         coords=(8.6512, 49.8728), country="DE"),
    dict(name="Joseph Moscoso",       photo="moscoso.jpg",
         affil="University of Maryland, College Park",
         city="College Park, MD, USA",
         coords=(-76.92750, 38.99667), country="US"),
    dict(name="Malcolm Lazarow",      photo="lazarow.jpg",
         affil="UC Berkeley",
         city="Berkeley, CA, USA",
         coords=(-122.2547, 37.8760), country="US"),
]

IMAGE_DIR = "photos"          # folder holding the headshot files

# Collaboration logo — placed in the top-left corner. Set to None to omit.
LOGO_FILE = "basc_logo.jpg"

# Collaboration name — appears in the figure title.
#COLLAB_NAME = "Baryon Scattering (BaSc) Collaboration"
COLLAB_NAME = ""

# Manual placement of the institution boxes in the "labels" style, in
# figure fraction (x, y) — x is 0 (left) .. 1 (right), y is 0 (bottom)
# .. 1 (top). A box is anchored by its LEFT edge when x < 0.5 and by
# its RIGHT edge otherwise, so leader lines leave from the inner side.
# This deliberately uses the empty top/bottom bands, not just two
# columns. Edit freely; keys must match the affiliation strings exactly.
MANUAL_LABEL_POS = {
    # left side, beside the North America panel
    "Kent State University":                 (0.3, 0.62),
    "Carnegie Mellon University":            (0.37, 0.72),
    "Lawrence Berkeley National Laboratory": (0.12, 0.61),
    "Lawrence Livermore National Laboratory": (0.12, 0.48),
    "Oak Ridge National Laboratory":        (0.17, 0.27),
    "University of North Carolina":         (0.35, 0.27),
    "Technische Universität Darmstadt":     (0.86, 0.60),
    "UC Berkeley":                          (0.07, 0.545),
    "University of Bern":                   (0.60, 0.28),
    "University of Cyprus":                 (0.86, 0.27),
    "University of Maryland, College Park": (0.55, 0.8),
    "DESY Zeuthen/Humboldt-Universität":    (0.87, 0.78),
    "Ruhr-Universität Bochum":              (0.67, 0.77),
    "Johannes Gutenberg Universität Mainz": (0.765, 0.27),
}

# Ring / accent color per country — extend as the collaboration grows.
COUNTRY_COLORS = {
    #"US": "#1f77b4",
    #"DE": "#d62728",
    #"CH": "#2ca02c",
    #"CY": "#ff7f0e",
    "default": "#555555",
}

# Two-panel ("broken Atlantic") extents. The empty mid-ocean carries no
# members, so instead of one very wide map we draw North America and
# Europe as separate panels and drop the ocean between them. Both panels
# share the SAME latitude window so they read as one continuous map with
# a slice removed. [lon_min, lon_max, lat_min, lat_max].
NA_EXTENT = [-125, -73, 27, 49]   # US-centered; little Canada at top
EU_EXTENT = [-11, 37, 33, 55]     # shifted west to show W. Europe
SPLIT_LON = -30        # members west of this go on the NA panel

BUBBLE_PX = 300               # rendered size of each circular headshot
RING_PX = 14                  # thickness of the colored ring


def color_for(country):
    return COUNTRY_COLORS.get(country, COUNTRY_COLORS["default"])


# ----------------------------------------------------------------------
# 2. IMAGE HELPERS (photos style)
# ----------------------------------------------------------------------
def circular_image(path, country, name="?", size=BUBBLE_PX, ring=RING_PX):
    """Return an RGBA PIL image cropped to a circle with a colored ring.

    Falls back to a colored disk with initials if the file is missing.
    """
    ring_color = color_for(country)

    if path and os.path.exists(path):
        img = Image.open(path).convert("RGB")
        w, h = img.size
        side = min(w, h)
        img = img.crop(((w - side) // 2, (h - side) // 2,
                        (w - side) // 2 + side, (h - side) // 2 + side))
        img = img.resize((size, size), Image.LANCZOS)
    else:
        img = Image.new("RGB", (size, size), ring_color)
        draw = ImageDraw.Draw(img)
        initials = "".join(w[0] for w in name.split()[:2]).upper() or "?"
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                size // 3)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), initials, font=font)
        draw.text(((size - (bbox[2] - bbox[0])) / 2,
                   (size - (bbox[3] - bbox[1])) / 2 - bbox[1]),
                  initials, fill="white", font=font)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)

    draw = ImageDraw.Draw(out)
    for i in range(ring):
        draw.ellipse((i, i, size - 1 - i, size - 1 - i),
                     outline=ring_color)
    return out


# ----------------------------------------------------------------------
# 3. GEOCODING (optional fallback)
# ----------------------------------------------------------------------
def ensure_coords(people):
    missing = [p for p in people if not p.get("coords")]
    if not missing:
        return
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    geocode = RateLimiter(
        Nominatim(user_agent="collab_map").geocode, min_delay_seconds=1)
    for p in missing:
        loc = geocode(p["city"])
        if loc is None:
            raise ValueError(f"Could not geocode: {p['city']}")
        p["coords"] = (loc.longitude, loc.latitude)
        print(f"  geocoded {p['city']} -> {p['coords']}")


# ----------------------------------------------------------------------
# 4. LAYOUT HELPERS
# ----------------------------------------------------------------------
def two_column_positions(items_lonlat, left_top=0.70, right_top=0.93,
                         bot=0.05):
    """Given a list of (lon, lat), return (x, y) figure-coord positions.

    Westernmost half goes in the left margin, eastern half in the right;
    within a column items are ordered north-to-south. The left column
    starts at `left_top` (kept below the logo); the right column can use
    the full height up to `right_top`.
    """
    n = len(items_lonlat)
    order = sorted(range(n), key=lambda i: items_lonlat[i][0])
    half = (n + 1) // 2
    left_idx, right_idx = order[:half], order[half:]
    left_idx.sort(key=lambda i: -items_lonlat[i][1])
    right_idx.sort(key=lambda i: -items_lonlat[i][1])

    pos = [None] * n

    def spread(k, top, bot):
        if k <= 1:
            return [0.5 * (top + bot)]
        return [top - j * (top - bot) / (k - 1) for j in range(k)]

    columns = (
        (0.105, left_idx, left_top, bot),
        (0.895, right_idx, right_top, bot),
    )
    for col_x, idx_list, top, bot_ in columns:
        for y, i in zip(spread(len(idx_list), top, bot_), idx_list):
            pos[i] = (col_x, y)
    return pos


def _style_geoaxes(ax, extent, proj):
    ax.set_extent(extent, crs=proj)
    # 'auto' lets each panel fill its axes box exactly; the boxes are
    # pre-sized (below) so the two panels share one consistent scale.
    ax.set_aspect("auto")
    ax.add_feature(cfeature.OCEAN.with_scale("110m"), facecolor="#eaf2f8")
    ax.add_feature(cfeature.LAND.with_scale("110m"), facecolor="#f4f1ec")
    ax.add_feature(cfeature.COASTLINE.with_scale("110m"),
                   linewidth=0.5, edgecolor="#888")
    ax.add_feature(cfeature.BORDERS.with_scale("110m"),
                   linewidth=0.4, edgecolor="#aaa")
    ax.add_feature(cfeature.LAKES.with_scale("110m"),
                   facecolor="#eaf2f8", linewidth=0)


LOGO_SIZE = 0.10       # logo width as a fraction of the figure width
#LOGO_PAD = 0.012
LOGO_PAD = 0.058
LOGO_GAP = 0.008       # gap between the logo bottom and the box below it
# The logo's bottom edge sits just above this institution box.
LOGO_ANCHOR_BOX = "Lawrence Berkeley National Laboratory"
CROP_PAD_PX = 10       # white margin (pixels) kept by the auto-crop


def _logo_geom(fig):
    """Return (x0, y0, w, h) of the logo box in figure fraction, or None."""
    if not LOGO_FILE or not os.path.exists(LOGO_FILE):
        return None
    img = Image.open(LOGO_FILE)
    iw, ih = img.size
    fig_w_in, fig_h_in = fig.get_size_inches()
    h = LOGO_SIZE * (ih / iw) * (fig_w_in / fig_h_in)
    # Anchor the logo's BOTTOM edge just above the box named by
    # LOGO_ANCHOR_BOX (boxes are centered at their y, so add ~0.03 to
    # reach the top of the box). This drops the logo down onto the map's
    # top-left corner with minimal white space. Falls back to the top of
    # the map panels if the anchor box is not found.
    anchor_pos = MANUAL_LABEL_POS.get(LOGO_ANCHOR_BOX)
    if anchor_pos is not None:
        y_bottom = anchor_pos[1] + 0.03 + LOGO_GAP
    else:
        axes = fig.get_axes()
        map_top = max(ax.get_position().y1 for ax in axes) if axes else 0.95
        y_bottom = map_top - 0.05
    return (LOGO_PAD, y_bottom, LOGO_SIZE, h)


def dual_map(fig_w, fig_h, stretch=1.2, band=(0.06, 0.93),
             x_left=0.13, x_right=0.87, gap=0.02):
    """Build a figure with two side-by-side map panels (NA | EU).

    `stretch` controls vertical proportion: 1.0 = true equirectangular
    aspect (no vertical stretch at all); values slightly above 1 add a
    barely-perceptible amount to use space better. The panel height is
    DERIVED from this (not forced to fill the figure), so the continents
    keep their shape. The map block is centered vertically within `band`
    so any leftover space is split evenly top and bottom rather than
    pooling in one place. Both panels share the height and have widths
    proportional to their longitude spans, so they stay at one scale.
    Returns (fig, ax_na, ax_eu, proj).
    """
    proj = ccrs.PlateCarree()
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=150)

    na_lon = NA_EXTENT[1] - NA_EXTENT[0]
    eu_lon = EU_EXTENT[1] - EU_EXTENT[0]
    lat_span = NA_EXTENT[3] - NA_EXTENT[2]

    usable = (x_right - x_left) - gap
    na_w = usable * na_lon / (na_lon + eu_lon)
    eu_w = usable * eu_lon / (na_lon + eu_lon)

    # Height for a true aspect-1 map, then * stretch. Clamp to the band.
    na_w_in = na_w * fig_w
    h_in = na_w_in * (lat_span / na_lon) * stretch
    h = min(h_in / fig_h, band[1] - band[0])
    y0 = band[0] + ((band[1] - band[0]) - h) / 2   # vertically centered

    ax_na = fig.add_axes([x_left, y0, na_w, h], projection=proj)
    ax_eu = fig.add_axes([x_left + na_w + gap, y0, eu_w, h],
                          projection=proj)
    _style_geoaxes(ax_na, NA_EXTENT, proj)
    _style_geoaxes(ax_eu, EU_EXTENT, proj)

    # Break marks in the gap to signal the omitted ocean.
    xb = x_left + na_w + gap / 2
    for yy in (y0, y0 + h):
        fig.add_artist(plt.Line2D(
            [xb - 0.007, xb + 0.007], [yy - 0.013, yy + 0.013],
            transform=fig.transFigure, color="#888",
            linewidth=1.4, zorder=10))
    return fig, ax_na, ax_eu, proj


def panel_for(lon, ax_na, ax_eu):
    return ax_na if lon < SPLIT_LON else ax_eu


def add_logo(fig):
    """Place the collaboration logo in the top-left corner."""
    geom = _logo_geom(fig)
    print('geom',geom)
    if geom is None:
        return
    logo_ax = fig.add_axes(geom)
    logo_ax.imshow(Image.open(LOGO_FILE))
    logo_ax.axis("off")


def finish(fig, outfile):
    """Title + tight save, then auto-crop residual white margins."""
    fig.suptitle(COLLAB_NAME, fontsize=30, fontweight="bold", y=0.99)
    add_logo(fig)
    fig.savefig(outfile, facecolor="white", bbox_inches="tight",
                pad_inches=0.15)
    # Trim the white margins left around the content on all four sides,
    # keeping a thin uniform CROP_PAD_PX border.
    img = Image.open(outfile).convert("RGB")
    gray = np.asarray(img.convert("L"))
    mask = gray < 245
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if len(rows) and len(cols):
        pad = CROP_PAD_PX
        box = (max(cols[0] - pad, 0), max(rows[0] - pad, 0),
               min(cols[-1] + 1 + pad, img.width),
               min(rows[-1] + 1 + pad, img.height))
        img.crop(box).save(outfile)
    print(f"Saved -> {outfile}")


# ----------------------------------------------------------------------
# 5a. PHOTOS STYLE
# ----------------------------------------------------------------------
def render_photos(outfile):
    fig, ax_na, ax_eu, proj = dual_map(15, 11, stretch=1.25)
    lg = _logo_geom(fig)
    left_top = (lg[1] - 0.04) if lg else 0.88
    pos = two_column_positions([p["coords"] for p in PEOPLE],
                               left_top=left_top, right_top=0.92)

    for person, (bx, by) in zip(PEOPLE, pos):
        lon, lat = person["coords"]
        c = color_for(person["country"])
        ax_p = panel_for(lon, ax_na, ax_eu)
        geo = ccrs.PlateCarree()._as_mpl_transform(ax_p)
        bubble = circular_image(os.path.join(IMAGE_DIR, person["photo"]),
                                person["country"], person["name"])

        ax_p.plot(lon, lat, "o", markersize=5, color=c,
                  transform=proj, zorder=5)
        ab = AnnotationBbox(
            OffsetImage(bubble, zoom=0.17),
            xy=(lon, lat), xycoords=geo,
            xybox=(bx, by), boxcoords=fig.transFigure,
            frameon=False, annotation_clip=False,
            arrowprops=dict(arrowstyle="-", color=c, linewidth=1.0,
                            shrinkA=1, shrinkB=1),
            zorder=6,
        )
        ax_p.add_artist(ab)
        fig.text(bx, by - 0.040,
                 f"{person['name']}\n{person['affil']}",
                 ha="center", va="top", fontsize=7.5, linespacing=1.3)

    finish(fig, outfile)


# ----------------------------------------------------------------------
# 5b. LABELS STYLE  (grouped by institution, no photos)
# ----------------------------------------------------------------------
def group_by_institution(people):
    """Return an ordered list of institution groups.

    Each group: dict(affil, city, coords, country, members=[names]).
    People are merged on (affil, coords).
    """
    groups = OrderedDict()
    for p in people:
        key = (p["affil"], p["coords"])
        if key not in groups:
            groups[key] = dict(affil=p["affil"], city=p["city"],
                               coords=p["coords"],
                               country=p["country"], members=[])
        groups[key]["members"].append(p["name"])
    return list(groups.values())


def render_labels(outfile):
    groups = group_by_institution(PEOPLE)
    fig, ax_na, ax_eu, proj = dual_map(15, 7, stretch=1.2,
                                       band=(0.20, 0.86))

    for grp in groups:
        if grp["affil"] not in MANUAL_LABEL_POS:
            print(f"  WARNING: no MANUAL_LABEL_POS for {grp['affil']!r}")
        bx, by = MANUAL_LABEL_POS.get(grp["affil"], (0.5, 0.5))
        lon, lat = grp["coords"]
        c = color_for(grp["country"])
        c_affil = '#570202'
        on_left = bx < 0.5
        ax_p = panel_for(lon, ax_na, ax_eu)
        geo = ccrs.PlateCarree()._as_mpl_transform(ax_p)

        header = TextArea(
            grp["affil"],
            textprops=dict(fontsize=9.5, fontweight="bold", color=c_affil))
        body = TextArea(
            "\n".join(grp["members"]),
            textprops=dict(fontsize=8.5, color="#222",
                           linespacing=1.35))
        box = VPacker(children=[header, body], pad=0, sep=3,
                      align="left")

        ax_p.plot(lon, lat, "o", markersize=5, color=c,
                  transform=proj, zorder=5)
        ab = AnnotationBbox(
            box, xy=(lon, lat), xycoords=geo,
            xybox=(bx, by), boxcoords=fig.transFigure,
            box_alignment=(0 if on_left else 1, 0.5),
            annotation_clip=False,
            bboxprops=dict(boxstyle="round,pad=0.5",
                           facecolor="white", edgecolor=c,
                           linewidth=1.3),
            arrowprops=dict(arrowstyle="-", color=c, linewidth=1.0,
                            shrinkA=4, shrinkB=2),
            zorder=6,
        )
        ax_p.add_artist(ab)

    finish(fig, outfile)


# ----------------------------------------------------------------------
# 6. ENTRY POINT
# ----------------------------------------------------------------------
STYLE = "labels"   # "photos" or "labels" (overridden by command line)


def main():
    style = sys.argv[1] if len(sys.argv) > 1 else STYLE
    if style not in ("photos", "labels"):
        sys.exit('Usage: python collaboration_map.py [photos|labels]')

    ensure_coords(PEOPLE)
    if style == "photos":
        render_photos("collaboration_map_photos.png")
    else:
        render_labels("collaboration_map_labels.png")


if __name__ == "__main__":
    main()
