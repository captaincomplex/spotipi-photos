# Hardware for a Spotipi Photos build

Researched 2 September 2026. Prices are what The Pi Hut was showing on the day,
inc VAT; check before ordering. Everything below is a UK shop that ships from the UK.

## The short answer

**Raspberry Pi 3 Model A+ (£24.00) + Adafruit RGB Matrix Bonnet (£14.40) + a
64×64 3mm-pitch panel (£28.80), on a single 5V 4A supply.** No soldering
required. About **£117** all in, and every part is in stock today.

The Pi Zero 2 W would be the obvious cheap board and it is **still out of stock**
at The Pi Hut — the same blocker the Ident build hit in August. The 3A+ is £24,
has the 40-pin header fitted, has dual-band Wi-Fi, and its known-good
`gpio_slowdown` is **2**, which is exactly what `config/rgb_options.ini` already
ships with.

Two things worth reading below rather than skimming: **one power supply is
right, not two** (and an earlier draft of this document got that wrong), and
**the 32×32 panel is not the cheap option** — it costs more than the 64×64 and is
nearly out of production.

## Bill of materials

| # | Part | Price | Stock | Notes |
|---|---|---|---|---|
| 1 | [Raspberry Pi 3 Model A+](https://thepihut.com/products/raspberry-pi-3-model-a-plus) | **£24.00** | in stock | 40-pin header fitted, dual-band Wi-Fi, 512 MB, 65 × 52.5 mm |
| 2 | [Adafruit RGB Matrix Bonnet](https://thepihut.com/products/adafruit-rgb-matrix-bonnet-for-raspberry-pi-ada3211) | **£14.40** | in stock | This is what `hardware_mapping = adafruit-hat` means |
| 3 | [RGB LED Matrix Panel — 3mm pitch, 64×64](https://thepihut.com/products/rgb-full-colour-led-matrix-panel-3mm-pitch-64x64-pixels) | **£28.80** | in stock | 192 × 192 × 14 mm, 5V/4A, 4096 LEDs |
| 4 | [Mean Well 5V 4A 20W (GST25A05-P1J)](https://thepihut.com/products/mean-well-5v-4a-20w-power-supply-gst25a05-p1j) | **£22.50** | in stock | 2.1mm barrel, centre positive. **IEC mains lead is extra.** Powers panel *and* Pi |
| 5 | [SanDisk microSD, 32GB A1](https://thepihut.com/products/sandisk-microsd-card-class-10-a1) | **£27.00** | in stock | See the note on card prices below |
| 6 | [Mini USB-C microSD reader](https://thepihut.com/products/mini-usb-c-microsd-card-reader) *(if needed)* | £4.00 | in stock | Only if the computer has no SD slot |
| | **Total** | **≈ £116.70** | | plus an IEC lead if you haven't got one |

**What comes in the box with the panel:** the panel, a **~16 cm HUB75 IDC ribbon
cable** and a **~50 cm power pigtail**. Both are the cables you need — you do not
buy them separately. It has **M3 mounting holes**; the magnetic feet Adafruit sell
are *not* included.

**On the SD card price.** £27 for 32GB is not a typo and not a good deal — it is
what memory costs in 2026, and the same distortion is noted in Ident's hardware
document. Any A1/A2 card of 16GB or more works. [Unverified] I have not
price-checked non-Pi-Hut retailers; a supermarket or Amazon card is likely to be
materially cheaper.

## Panel sizes: the software takes three, the market offers one

`load_matrix()` reads `rows` and `columns` straight from `rgb_options.ini`, so
**64×64, 32×32 and 64×32 are all equally supported** — and `sync_album.py` and
`tools/prepare_photos.py` both take a matching `--size`. Anyone who already owns
a panel, or picks one up secondhand, is catered for.

Buying new is a different question. Checked 2 September 2026:

| Panel | Physical | Price | Stock |
|---|---|---|---|
| **[64×64, 3mm](https://thepihut.com/products/rgb-full-colour-led-matrix-panel-3mm-pitch-64x64-pixels)** | 192 × 192 mm | **£28.80** | **in stock** |
| [32×32, 5mm](https://thepihut.com/products/32x32-rgb-led-matrix-panel-5mm-pitch) | 160 × 160 mm | £33.60 | 10 left |
| [32×32, 6mm](https://thepihut.com/products/32x32-rgb-led-matrix-panel-6mm-pitch) | 190 × 190 mm | £38.40 | **discontinued** |
| [64×32, 3mm](https://thepihut.com/products/rgb-full-colour-led-matrix-panel-3mm-pitch-64x32-pixels) | 192 × 96 mm | £22.10 | **sold out** |

**The 64×64 is the cheapest and the only one properly available.** A 32×32 costs
£5–£10 *more* for a quarter of the pixels, because the small panels are old
stock at coarse pitches and nobody is making them for this market any more. Note
also that a 32×32 at 6mm pitch is the *same physical size* as a 64×64 at 3mm —
the panels are the same board area, differing only in how finely they're
populated.

So: support all three in software, document all three, and recommend exactly one
for a new build. There is no version of this where recommending a 32×32 to a new
builder is doing them a favour.

## Power — one supply, and why

This is the section that matters most, and it is where an earlier draft of this
document was wrong. It recommended two supplies. It should have recommended one.

**A 64×64 panel is specified at 5V / 4A on its own** — up to 20 watts of LEDs.
Adafruit's rule of thumb is *width × 0.12 A*, which for 64 columns gives about
7.7 A at absolute full white; the 4A figure assumes you are never showing a
full-brightness white screen, which for photographs and album art is a safe
assumption. A 32×32 needs roughly half.

**The recommendation: one 5V 4A supply into the bonnet's barrel jack, powering
both the panel and the Pi.**

The bonnet is built for this. Adafruit's own documentation says it carries *"a
1A diode on board that will automatically power the Pi if/when the voltage
drops"*, and then, plainly: *"if you want, just plug in the 5V wall adapter into
the bonnet and it will automagically power up the Pi too!"*

The same page also says the Pi *"must be powered separately"*. Those two
statements sit a paragraph apart and are the reason this gets written up
inconsistently everywhere, including here. Reading it as a whole, the sensible
interpretation is that separate supplies are the belt-and-braces arrangement,
not a requirement — and the practical evidence agrees: this project's own
reference build has run on a single supply throughout.

**When you would add a second supply.** A Pi 3A+ draws up to about 1A under
load, which is the diode's rating. That headroom disappears only if you run a
64×64 panel at brightness 90–100 for sustained periods. The symptom is
unambiguous: the Pi's undervoltage warning, or it reboots on bright frames. If
you see that, add an [official 12.5W micro-USB supply](https://thepihut.com/products/raspberry-pi-zero-uk-power-supply)
(£7.70) for the Pi and leave the 4A one to the panel. A 32×32 build will never
need it.

**What is genuinely not negotiable:**

- The panel's power goes into **the bonnet's screw terminal**, never into the
  Pi's GPIO pins.
- **Red to `+`, black to `−`.**
- Not a phone charger. An under-fed Pi browns out mid-write, and that is how SD
  cards get corrupted.

## Which Pi

Checked 2 September 2026.

| Board | Price (Pi Hut, inc VAT) | Stock | Verdict for this build |
|---|---|---|---|
| Zero 2 W / WH | £14.40 / £17.30 | **out** | The cheap ideal. Unavailable, and marginal for a matrix anyway |
| **Pi 3 Model A+** | **£24.00** | in stock | **The recommendation.** `slowdown=2`, dual-band Wi-Fi, header fitted |
| Pi 4 Model B, 1GB | £33.60 | in stock | Works, but needs a higher `gpio_slowdown` and a USB-C supply |
| Pi 5 | from £43.20 | in stock | Supported upstream now — but see the caveat below |

**Why the 3A+ and not the Pi 4.** The rpi-rgb-led-matrix library bit-bangs GPIO
against a hard real-time deadline. On a Pi 2/3 the documented setting is
`--led-slowdown-gpio=2`; the Pi 4 is faster and *less* predictable here, and the
library's own documentation says it "may require higher values to avoid display
garbage". The `rgb_options.ini` comment in this repo already says as much. The
Pi 4 is not wrong, it is just a variable you don't need to introduce.

**Why not the Pi 5, yet.** The upstream library *does* now support the Pi 5, via
two new modes (`--led-rp1-pio=0` for speed at higher CPU cost, `--led-rp1-pio=1`
for minimal CPU), because the Pi 5's RP1 southbridge changed how GPIO works.
[Unverified] What I have **not** been able to confirm is whether Adafruit's
current `rgb-matrix.py` installer builds a version of the library new enough to
include that support. Until someone checks that on real hardware, a Pi 5 is a
research project rather than a build. Don't put it in a beginner's guide.

**On memory:** this is a Flask app drawing one 64×64 image. The 3A+'s 512 MB is
ample. Buying a 4GB or 8GB Pi 4 spends £60+ on nothing.

## The bonnet, and the PWM mod

The **Adafruit RGB Matrix Bonnet (£14.40)** is the right board. It arrives fully
assembled — terminal block and IDC socket already soldered — so a standard build
needs **no soldering at all**.

There is also an [Adafruit RGB Matrix HAT + RTC](https://thepihut.com/collections/raspberry-pi-hats/products/adafruit-rgb-matrix-hat-rtc-for-raspberry-pi-mini-kit)
at £24.00. It adds a battery-backed real-time clock this project does not need —
the schedule and the sunrise/sunset dimmer run off the system clock, and a
networked Pi gets that from NTP. It is also **down to 6 units**. Buy the bonnet.

### The PWM mod is worth doing

The panel is refreshed by toggling GPIO pins on a hard real-time deadline. The
Pi has one piece of hardware that does this properly — a PWM generator — and by
default it is wired to the audio output rather than the pin the bonnet uses.

Soldering a single wire between **GPIO 4 and GPIO 18** routes that hardware PWM
to the panel's clock pin. Then set `hardware_mapping = adafruit-hat-pwm` and the
timing moves from software (interruptible by anything else the Pi does) to
hardware (not interruptible). The panel goes visibly steadier.

**This is the single largest quality improvement available to the build, and it
costs a scrap of wire.** One joint between two adjacent pads; five minutes with
a basic iron; reversible.

The beginner's guide **documents both paths and defaults to no-soldering**, so
that nobody is blocked from finishing on the day the parts arrive. That is a
deliberate choice about not stranding people, not a judgement that the mod isn't
worth it — anyone who owns an iron should do it.

Setting `adafruit-hat-pwm` **without** the wire gives a blank or broken panel, so
the config comment in `rgb_options.ini` says so explicitly.

### CPU core isolation

The other optional tweak: `isolcpus=domain,managed_irq,3 nohz_full=3 rcu_nocbs=3
irqaffinity=0,1,2` in `/boot/cmdline.txt` reserves a core purely for panel
refresh. Adafruit's installer offers to do this for you, and on a Pi 3A+ that is
a quarter of a processor you are not otherwise using. Say yes.

## One thing that is not optional: turn the onboard sound off

The matrix library and the Pi's onboard audio **share a timing circuit**. The
library's documentation is unambiguous that `dtparam=audio=off` must be set —
in `/boot/firmware/config.txt` on Bookworm and later, or `/boot/config.txt` on
older releases. Without it you get flicker and glitching that no amount of
`gpio_slowdown` fiddling will fix.

**Adafruit's installer does not do this for you unless you pick "quality".**
Reading the installer source: it does not set `dtparam=audio=off` at all. What it
does, and *only* on the quality path, is blacklist the sound module by writing
`blacklist snd_bcm2835` to `/etc/modprobe.d/blacklist-rgb-matrix.conf`. The
quality path also requires the soldered PWM mod, so anyone who sensibly picks
**convenience** on a first build ends up with sound enabled — and that is
precisely where the installer's own warning about "slightly less steady" output
comes from.

Since this Pi is a headless photo frame with nothing connected to its audio
output, there is no reason not to turn sound off on the convenience path too. It
is a free improvement and it is the first thing to check when a panel flickers.

**Two things to fix in this repo:**

1. `install_pi.sh` and `README.md` both print
   `curl .../Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh`. **That URL now
   404s.** Adafruit converted their installers from shell to Python and renamed
   the default branch to `main`; the file is now `rgb-matrix.py` and is run via
   `sudo -E env PATH=$PATH python3 rgb-matrix.py` after installing
   `adafruit-python-shell` and `click`. Adafruit's own learn guide still shows the
   old command, so this is upstream drift rather than anything wrong here — but it
   means the printed instruction sends a new builder to a dead link.
2. Neither the installer nor the README mentions the sound setting at all. Worth
   adding, given the above.

## What this research changed in the code

Four things surfaced while checking the documentation against what the project
actually shipped. All four are now fixed in the repo; they are recorded here
because the reasoning is worth keeping.

**1. `generate-token.sh` was missing.** `README.md`, `SPOTIFY_TOKEN_RENEWAL.txt`
and `getSongInfo.py` all referred to it, but it was in neither the repo nor any
release zip — it had been left behind when this was forked from
[ryanwa18/spotipi](https://github.com/ryanwa18/spotipi). It has been restored
from the upstream `develop` branch and adapted in two ways: it writes
`.cache-<username>` rather than a bare `.cache` (so `install_pi.sh` can ask for a
predictable path), and its scope is pinned to the same `user-read-currently-playing`
that `getSongInfo.py` requests. **Those two must not drift apart** — spotipy
treats a cached token granted under a different scope as unusable, which
presents as "the token doesn't work" with no useful error.

**2. `sync_album.py` defaulted `--pi-dir` to `/home/pi/spotipi/photos`** —
missing the `-photos` that every other part of the project uses. It failed
silently in the worst way: `rsync` created the wrong directory, synced into it,
and reported success, so the panel showed nothing and nothing logged an error.
`--pi-host` was likewise a hardcoded IP from the original build. Both now
default sensibly (`/home/pi/spotipi-photos/photos`, `pi@spotipi.local`).

**3. The `rgb-matrix.sh` URL was dead.** `install_pi.sh` and `README.md` both
printed `curl .../Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh`. Adafruit
converted their installers from shell to Python and renamed the default branch,
so that 404s; it is `rgb-matrix.py` on `main` now, run via
`sudo -E env PATH=$PATH python3 rgb-matrix.py`. Adafruit's own learn guide still
shows the old command, so this is upstream drift rather than anything this
project did wrong — but it was the first instruction a new builder followed.
`install_pi.sh` now prints the working sequence, and only when `rgbmatrix` is
actually missing.

**4. The onboard sound was never dealt with.** Covered in the section above;
`install_pi.sh` now sets `dtparam=audio=off` itself and reports whether it
changed anything.

### Still open: the installer versus a modern Raspberry Pi OS

`install_pi.sh` was written against this build's existing Pi, which runs
**Raspbian Buster** — hence the `Flask==2.0.3` / `Werkzeug==2.0.3` pins for
Python 3.7, and the deliberate absence of `set -e`.

On **Bookworm or Trixie**, which is what a new build installs,
`python3 -m pip install spotipy pillow requests` doesn't fail for a missing
package — it refuses outright with `error: externally-managed-environment`,
because PEP 668 forbids pip writing into the system Python. The installer
swallows that (`2>/dev/null || true`), so the symptom is not an install failure
but the later `WARNING: some Python deps missing`, followed by a web UI that
never starts.

The guide works around it by installing via apt first:

```bash
sudo apt install -y python3-flask python3-pil python3-requests
sudo pip3 install --break-system-packages spotipy
```

A virtualenv is the tidier answer in general but awkward here: the display
daemon runs as **root** (it must, for GPIO, and `drop_privileges` is disabled
deliberately since v1.2) and needs the system-wide `rgbmatrix` module the
Adafruit installer builds. **`install_pi.sh` should adopt the apt-first
sequence** rather than leaving it to the guide.

## Mounting

The panel is **192 × 192 × 14 mm** and **235 g** — a solid, heavy object, not
something to hang on a picture pin. It has **M3 threaded holes** on the back.
Realistic options:

- A **deep box frame** with a 192 mm square aperture. The panel is 14 mm thick
  before you add the bonnet and Pi behind it, so a standard picture frame will
  not close.
- **M3 standoffs onto a backing board**, with the Pi and bonnet mounted beside
  rather than directly behind the panel — the bonnet's ribbon is only ~16 cm, so
  the Pi has to live close.
- Adafruit's **magnetic feet** (4-pack) if it is going on something steel. Not
  included with the panel.

[Speculation] A 3D-printed shell is the obvious better answer and the one that
would make this look like a product rather than a project, but I have not costed
or designed one.

## Recommendation

Buy the **Pi 3A+ / Bonnet / 64×64 / one 5V 4A supply** build above, at about
**£117**. Skip the RTC HAT. Buy the 64×64 even if a 32×32 sounds like the
sensible small option — it isn't, at today's prices.

**Do the PWM solder mod** if you have an iron. It is five minutes and it is the
best return on effort anywhere in this project.

Remaining work, in order:

1. **`install_pi.sh` should install Python dependencies apt-first**, so a fresh
   Bookworm build works without the guide's intervention.
2. **Revisit the Pi 5** only when someone has confirmed the current Adafruit
   installer builds Pi 5 support on real hardware.
3. **A 3D-printed or laser-cut shell.** The panel is a bare board with M3 holes;
   this is the gap between "project" and "object".

## Sources

- [The Pi Hut — Raspberry Pi 3 Model A+](https://thepihut.com/products/raspberry-pi-3-model-a-plus)
- [The Pi Hut — Raspberry Pi Zero 2 W](https://thepihut.com/products/raspberry-pi-zero-2-w)
- [The Pi Hut — Adafruit RGB Matrix Bonnet](https://thepihut.com/products/adafruit-rgb-matrix-bonnet-for-raspberry-pi-ada3211)
- [The Pi Hut — RGB LED Matrix Panel, 3mm pitch, 64×64](https://thepihut.com/products/rgb-full-colour-led-matrix-panel-3mm-pitch-64x64-pixels)
- [The Pi Hut — Adafruit RGB Matrix HAT + RTC](https://thepihut.com/collections/raspberry-pi-hats/products/adafruit-rgb-matrix-hat-rtc-for-raspberry-pi-mini-kit)
- [The Pi Hut — Mean Well 5V 4A 20W GST25A05-P1J](https://thepihut.com/products/mean-well-5v-4a-20w-power-supply-gst25a05-p1j)
- [The Pi Hut — Official 12.5W micro-USB supply](https://thepihut.com/products/raspberry-pi-zero-uk-power-supply)
- [The Pi Hut — SanDisk microSD Class 10 A1](https://thepihut.com/products/sandisk-microsd-card-class-10-a1)
- [Adafruit — 64x64 RGB LED Matrix, 3mm pitch (product 4732)](https://www.adafruit.com/product/4732)
- [Adafruit Learn — RGB Matrix Bonnet for Raspberry Pi](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi)
- [Adafruit Learn — RGB Matrix Bonnet pinouts](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/pinouts)
- [hzeller/rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix)
- [Adafruit Raspberry-Pi-Installer-Scripts](https://github.com/adafruit/Raspberry-Pi-Installer-Scripts) — `rgb-matrix.py`, and the README's invocation
- [ryanwa18/spotipi](https://github.com/ryanwa18/spotipi) — the upstream project; `generate-token.sh` restored from its `develop` branch
- [The Pi Hut — 32×32, 5mm pitch](https://thepihut.com/products/32x32-rgb-led-matrix-panel-5mm-pitch)
- [The Pi Hut — 32×32, 6mm pitch](https://thepihut.com/products/32x32-rgb-led-matrix-panel-6mm-pitch)
- [The Pi Hut — 64×32, 3mm pitch](https://thepihut.com/products/rgb-full-colour-led-matrix-panel-3mm-pitch-64x32-pixels)
- [The Pi Hut — Mini USB-C microSD card reader](https://thepihut.com/products/mini-usb-c-microsd-card-reader)
