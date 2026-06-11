# Install swisstopo maps on your Garmin watch

A step-by-step guide written for non-developers. Works on **Epix 2** and
**Fenix 7 Pro**. Read the section at the bottom if you have a Fenix 6.

---

## Before you start

You need:

- A Garmin watch from the supported list (Epix 2, Fenix 7 Pro).
- A computer (Windows, Mac, or Linux).
- The cable that came with your watch.
- 10 minutes.

You will **not** need any special software. We just copy files.

---

## Step 1. Pick which maps you want

Two ways:

**A. "I know roughly where I'm going" → use the [GPX picker tool](../tools/gpx_pack_picker.html).**
Drop the GPX of your planned tour onto the page; it tells you which map zone(s)
cover the route and gives you direct download links.

**B. "I want to paint my own area" → use the [tile picker tool](../tools/tile_picker.html).**
Click 10 × 10 km cells on the swisstopo map until you've covered the terrain you
want. Hit **Build my custom pack**. Wait 5 to 15 minutes; the server builds a KMZ
for you and gives you a download link.

Either way you end up with one or more `.kmz` files to download.

> **Always also download `00_overview_ch.kmz`** (the GPX picker links to it
> automatically). This is the all-of-Switzerland background that stays enabled
> at all times.

---

## Step 2. Plug your watch into the computer

Use the USB cable that came with the watch. The watch will appear as a USB
drive named **GARMIN** (it may also show up as the watch's name).

- **Windows:** look for a new drive letter in *This PC*.
- **Mac:** look for a new drive on the desktop, or in Finder's sidebar.
- **Linux:** it auto-mounts under `/media/<your-user>/GARMIN` or similar.

If the watch doesn't appear, unplug and try a different USB port; many phone
charging cables don't carry data.

---

## Step 3. Open the `Garmin/CustomMaps/` folder

On the GARMIN drive, navigate to:

```
GARMIN/Garmin/CustomMaps/
```

(That's `Garmin` *inside* the GARMIN drive, yes, the same word twice. The
folder `CustomMaps` is inside that.)

If `CustomMaps/` doesn't exist yet, create it. The name must be exactly
`CustomMaps` (capital C, capital M, no space).

---

## Step 4. ⚠️ Delete any **old `.kmz` files**, but **leave `.img` files alone**

This is the most important step. Open `Garmin/CustomMaps/` and:

✅ **Delete every file inside `CustomMaps/` that ends in `.kmz`**: these are
old maps that would eat your tile budget and hide the new ones.

❌ **Do NOT delete any file ending in `.img`**, anywhere on the GARMIN drive.
The `.img` files are your watch's built-in maps (Garmin TopoActive, the basemap,
etc.). Deleting them will brick the map on your watch and you'll have to do a
factory reset.

In particular, do not touch these folders, even if they look empty or weird:

- `Garmin/` (the one one level above `CustomMaps`)
- `Garmin/Maps/`
- `Garmin/Maps/MapInstall/`
- anything that contains `.img`, `.gma`, `.unl`, or `.jnx`

When in doubt: **only delete files ending in `.kmz`**, and **only inside
`Garmin/CustomMaps/`**.

---

## Step 5. Copy the new `.kmz` files in

Drag every `.kmz` you downloaded in Step 1 into `Garmin/CustomMaps/`. The
overview pack and the regional pack(s) all go in the same folder.

A typical install ends up looking like this:

```
GARMIN/
└── Garmin/
    └── CustomMaps/
        ├── 00_overview_ch.kmz
        ├── 02_wallis_west_part_001.kmz
        ├── 02_wallis_west_part_002.kmz
        ├── 02_wallis_west_part_003.kmz
        └── 02_wallis_west_part_004.kmz
```

> **Don't mix zones.** The watch can render about 500 tiles total across all
> the KMZ files in `CustomMaps/`. One overview + one regional zone fills almost
> exactly that. Anything extra will be silently dropped by the watch.

---

## Step 6. Safely eject the watch

- **Windows:** right-click the GARMIN drive in *This PC* → *Eject*.
- **Mac:** drag the drive to the Trash (it becomes an Eject icon).
- **Linux:** right-click → *Eject* (or `udisksctl unmount`).

Then unplug the USB cable.

---

## Step 7. Reboot the watch and turn the Custom Maps layer on

**Reboot the watch:** hold the *Light* button (top-left) for ~15 seconds until
it powers off. Then press it again to power back on. (A reboot ensures the
watch re-scans `CustomMaps/`.)

**Turn the layer on (one-time setup):**

1. Press *Menu* (hold the back button on Epix 2 / Fenix 7 Pro).
2. Go to **Map → Map Settings → Map Layers** *(label varies slightly between
   firmware versions: also "Configure Map" or "Configure Maps")*.
3. Find **Custom Maps** in the list and make sure it's **On**.

That's it. The next time you open the map screen, the LK25 Winter raster with
slope shading and ski-tour routes is on the watch.

> ⚠ **You won't find your individual KMZs in Map Manager.** On Epix 2 and
> Fenix 7 Pro, Map Manager only lists built-in `.img` map families (e.g.
> *TopoActive Europe*). KMZ Custom Maps render as one combined layer with a
> single toggle. To switch to a different region, swap the files in
> `Garmin/CustomMaps/` via USB; there is no on-watch picker.

---

## Switching regions later

Same flow as the first install:

1. Plug the watch into the computer.
2. Open `Garmin/CustomMaps/`.
3. Delete the old regional `.kmz` files (keep `00_overview_ch.kmz`).
4. Copy the new region's `.kmz` files in.
5. Eject, reboot.

You can keep a folder on your PC with all the regional packs so you don't have
to re-download them each time.

---

## Troubleshooting

**The map looks blank / I only see the basemap.**
- Did you reboot the watch? (Hold *Light* for 15 s.)
- Did you enable **Map Layers → Custom Maps**?
- Are the `.kmz` files in `Garmin/CustomMaps/` (not `Garmin/Maps/`)?

**Only part of the region renders, edges are missing.**
- You're probably over the 500-tile cap. Count the `.kmz` files; if you have
  both `02_wallis_west_part_*.kmz` AND `03_wallis_zentral_part_*.kmz` in there,
  you're over. Keep just one regional pack at a time.

**The watch won't show maps at all anymore.**
- Did you delete any `.img` files? If yes, you'll need to reinstall the basemap
  via Garmin Express (Settings → Tools → Map Update). The KMZs alone are an
  overlay; they don't replace the built-in map.

**The watch hangs on the Garmin logo.**
- Unplug, hold *Light* for 30 seconds, then try again. If it persists, you may
  have a corrupt KMZ; remove the most recently added one.

---

## Fenix 6 / Fenix 6 Pro / Fenix 6X Pro

The current packs **don't fit** on the Fenix 6 family; those watches have a
**100-tile cap** (vs 500 on Epix 2 / Fenix 7 Pro), and a 3 MB-per-KMZ limit.

A coarser-resolution Fenix 6 build is planned but not yet available. Until then,
you can:

- Use the GPX picker for orientation (which zone covers your tour).
- For Fenix 6, fall back to Garmin's commercial TOPO Schweiz v2 PRO (vector,
  doesn't have LK25 cartography but does fit on the watch).

Track the progress on this in the project README.
