# Spotipi Photos — Complete Beginner's Guide

This guide builds a small bright LED panel that shows your photos as a slideshow,
and swaps automatically to the album cover of whatever you're playing on Spotify.
It assumes you have **never written code or used a Raspberry Pi before**. If you
can follow a recipe and copy-and-paste, you can do this.

**Works from a Windows PC or a Mac.** Where the two differ, both are given.

Set aside about **three hours** for the first build. Most of that is waiting, and
one step in Part 7 compiles for 10–20 minutes on its own. Nothing here can break
your computer.

> **Correct as of version 2.4**, written 2 September 2026.
> Prices checked that day at The Pi Hut and will drift — check before ordering.

### How photos will reach it

Three routes. All of them work with the same build, so this doesn't change what
you buy — but it's worth knowing which one is yours.

- **From an iPhone, on its own.** Make a Shared Album in Photos, turn on its
  *Public Website* switch, and paste the link into the control panel. The Pi
  checks the album every few minutes: add a photo on the phone and it appears;
  delete it and it goes. **No computer of any kind is involved.**
- **From any device, by hand.** Open the control panel in a browser and upload
  photos. On an iPhone that opens your camera roll directly. Works from a
  Windows PC, a Mac, an iPad, anything with a browser.
- **From Apple Photos on a Mac, automatically.** A job on the Mac mirrors a
  named album every five minutes. This is the original route and remains the
  best one if you already keep photos organised on a Mac.

Everything else in this guide — the build, Spotify, the control panel — is the
same whichever you use. Part 13 covers all three.

## Part 1 — What you're building, in plain English

A **Raspberry Pi** is a tiny, cheap computer about the size of a credit card. It
has no screen or keyboard of its own; you give it instructions from your normal
computer.

An **LED matrix panel** is a grid of small coloured lights — the sort of thing
bus destination boards are made of. It shows a very small picture, and that is
the point: photographs reduced to a few thousand pixels look like little glowing
paintings.

The panel can't plug into the Pi directly, so a **bonnet** sits between them — a
small circuit board that clips onto the Pi's pins and has the right sockets for
the panel's ribbon cable and its power.

The Pi runs the Spotipi software. It watches Spotify to see if you're playing
anything; if you are it shows the album art, and if you aren't it shows your
photos. You control it from a **web page** on your phone.

That's the whole thing: **a tiny computer + a bonnet + an LED panel.**

---

## Part 2 — Shopping list

Prices checked 2 September 2026 at The Pi Hut, inc VAT, shipping from the UK.
`HARDWARE.md` discusses every choice here in more detail.

### Panel size — supported sizes, and what to actually buy

The software supports **64×64**, **32×32** and **64×32** panels equally: you set
`rows` and `columns` in `config/rgb_options.ini` and everything else adapts. If
you already own one of these, or find one secondhand, it will work.

**For a new build, buy the 64×64.** Not because the others are worse, but
because of what the shops currently hold. Checked at The Pi Hut on 2 September
2026:

| Panel | Size | Price | Stock |
|---|---|---|---|
| **[64×64, 3mm pitch](https://thepihut.com/products/rgb-full-colour-led-matrix-panel-3mm-pitch-64x64-pixels)** | 192 × 192 mm | **£28.80** | **in stock** |
| [32×32, 5mm pitch](https://thepihut.com/products/32x32-rgb-led-matrix-panel-5mm-pitch) | 160 × 160 mm | £33.60 | only 10 left |
| [32×32, 6mm pitch](https://thepihut.com/products/32x32-rgb-led-matrix-panel-6mm-pitch) | 190 × 190 mm | £38.40 | discontinued |
| [64×32, 3mm pitch](https://thepihut.com/products/rgb-full-colour-led-matrix-panel-3mm-pitch-64x32-pixels) | 192 × 96 mm | £22.10 | sold out |

The 64×64 is **the cheapest of the four and the only one reliably in stock**,
while giving four times the picture of a 32×32. There is no trade-off to weigh
here at the moment — the intuition that fewer pixels ought to cost less does not
survive contact with what these actually sell for.

**What a 32×32 is like, if you have one.** 1,024 pixels is genuinely
impressionistic for photographs — colour and shape rather than faces — but album
art holds up surprisingly well, because most covers are bold and simple. It also
draws about half the current. Set `rows = 32` and `columns = 32` (Part 11) and
pass `--size 32` when you prepare photos (Part 13).

### The rest

| # | What | Why | Price |
|---|------|-----|-------|
| 1 | [Raspberry Pi 3 Model A+](https://thepihut.com/products/raspberry-pi-3-model-a-plus) | The computer. Pins already fitted, so **no soldering**. | £24.00 |
| 2 | [Adafruit RGB Matrix Bonnet](https://thepihut.com/products/adafruit-rgb-matrix-bonnet-for-raspberry-pi-ada3211) | Panel-to-Pi adapter. Arrives fully assembled. | £14.40 |
| 3 | [64×64 panel, 3mm pitch](https://thepihut.com/products/rgb-full-colour-led-matrix-panel-3mm-pitch-64x64-pixels) | The screen. **Comes with both cables you need.** | £28.80 |
| 4 | [Mean Well 5V 4A supply](https://thepihut.com/products/mean-well-5v-4a-20w-power-supply-gst25a05-p1j) | Powers the panel **and the Pi**. Needs a separate IEC kettle lead. | £22.50 |
| 5 | [microSD card, 16–32GB (A1/A2)](https://thepihut.com/products/sandisk-microsd-card-class-10-a1) | The Pi's hard drive. | ~£27 |
| 6 | [microSD-to-USB reader](https://thepihut.com/products/mini-usb-c-microsd-card-reader) *(if your computer has no SD slot)* | To set the card up. | £4.00 |

**About £117** all in. SD card prices are absurd at the moment —
any A1/A2 card of 16GB or more works, so shop around rather than paying £27.

### One power supply, not two

**You need one 5V 4A supply, and it powers both the panel and the Pi.** Plug it
into the bonnet's barrel jack; the bonnet feeds the Pi through an onboard diode.
Adafruit describe exactly this: *"just plug in the 5V wall adapter into the
bonnet and it will automagically power up the Pi too."*

Their documentation also suggests giving the Pi its own supply, and you will see
that repeated elsewhere. In practice, for a single panel at the brightness
anyone actually uses, one adequately-sized supply is correct and is what this
guide builds. Buy a second micro-USB supply only if you hit both of these:

- you run a **64×64 panel at brightness 90–100 for long periods**, and
- you see the Pi's low-voltage warning, or it reboots on bright frames.

If that happens, add an [official 12.5W micro-USB supply](https://thepihut.com/products/raspberry-pi-zero-uk-power-supply)
(£7.70) for the Pi and leave the 4A one on the panel alone. It is a £7.70 fix
for a problem most builds never have — and a 32×32 panel, drawing about half the current, will never have it.

> **What you must not do** is power the panel from the Pi's GPIO pins, or run
> either from a random phone charger. That is what causes dim panels, colour
> shifts and corrupted SD cards.

> **Two other buying notes:**
> 1. **Get the Bonnet, not the HAT.** The £24 "HAT + RTC" adds a battery clock
>    this project doesn't use, and stock is in single figures.
> 2. **Don't buy a Pi Zero 2 W** (out of stock everywhere, and marginal for a
>    matrix) **or a Pi 5** — see `HARDWARE.md`.

---

## Part 3 — Get your Spotify API credentials

**Do this first**, at a proper computer. You'll need three values later, and
it's the one part of the build that has nothing to do with hardware. It is free,
takes about five minutes, and does **not** require Spotify Premium.

### What this actually is, and why it's needed

Spotify won't tell an anonymous program what you're listening to. To ask, a
program needs its own identity — an "app" — registered with Spotify, plus your
permission to look at your playback. That's what you're creating: a private app
that exists only for your panel. You are not publishing anything, and no one
else ever sees it.

It produces three values:

- **Client ID** — the public name of your app. Not secret.
- **Client Secret** — the password for your app. **Keep this private.**
- **Redirect URI** — where Spotify sends your browser after you approve access.
  For a device with no browser, this is a deliberate dead end (see Part 10).

### Step by step

1. Go to <https://developer.spotify.com/dashboard> and log in with your ordinary
   Spotify account.
2. First time only, accept the Developer Terms of Service.
3. Click **Create app**.
4. Fill in:
   - **App name:** `Spotipi` (anything you like)
   - **App description:** `LED matrix album art` (anything you like)
   - **Redirect URI:** type exactly
     ```
     http://127.0.0.1/callback
     ```
     then click **Add**. It must appear as a listed entry, not just typed in
     the box. **This has to match later character for character — it is the
     single most common cause of failure.**
   - **Which API/SDKs are you planning to use?** tick **Web API**.
5. Accept the terms and click **Save**.
6. You land on the app's page. Click **Settings**.
7. Copy down:
   - **Client ID** — shown directly.
   - **Client secret** — click **View client secret**.
   - Your **Redirect URI** — confirm it reads `http://127.0.0.1/callback`.
8. You also need your **Spotify username**. Open
   <https://www.spotify.com/account/overview/> — it's the "Username" field,
   which may be an email address or a string of characters rather than your
   display name.

Keep those four things to hand. You'll type them once in Part 10.

> **What the panel can and can't see.** The software asks Spotify for one
> permission only — `user-read-currently-playing`. It cannot change your
> playback, read your playlists, or post anything. If you ever want to revoke
> it, remove the app at <https://www.spotify.com/account/apps/>.

---

## Part 4 — Put the operating system on the memory card

1. On your computer, install **Raspberry Pi Imager** from the official site:
   <https://www.raspberrypi.com/software/>. Free, official, Windows and macOS.
2. Put the microSD card in (using the USB reader if needed).
3. Open Imager and set the three buttons:
   - **Choose Device** → *Raspberry Pi 3*
   - **Choose OS** → *Raspberry Pi OS (other)* → **Raspberry Pi OS Lite (64-bit)**
     ("Lite" means no desktop — we don't need one.)
   - **Choose Storage** → your SD card. **Double-check** you've picked the card
     and not your computer's own drive.
4. Click **Next**. It asks *"Would you like to apply OS customisation settings?"*
   Click **Edit Settings**. This screen is what lets the Pi work with no keyboard
   or monitor ever attached:
   - **Set hostname:** `spotipi`
   - **Set username and password:** username `pi`, and a password you'll
     remember. **Write it down.**
   - **Configure wireless LAN:** your Wi-Fi **name** and **password** exactly
     (capitals matter), **Wireless LAN country** `GB`
   - **Set locale / time zone:** `Europe/London`
   - **Services** tab → tick **Enable SSH** → *Use password authentication*
5. **Save**, then **Yes** to write. It erases the card and takes a few minutes.

> **Why the time zone matters here.** Two features read the Pi's local clock:
> the **daily off-schedule** in the control panel (a recurring "off" window, for
> example 23:00 → 07:00) and the **sunrise/sunset dimmer**, which works out
> local sunrise and sunset from your latitude and longitude and drops the
> brightness at night. Set the wrong zone and both fire at the wrong times.

---

## Part 5 — Assemble it

Everything is plugs and one screw terminal. **Do this with the power supply
unplugged from the wall.**

1. **Push the bonnet onto the Pi.** Line up the 40 pins with the 40 holes and
   press down evenly. It only fits one way. Hold the boards by their edges.
2. **Plug the ribbon cable into the bonnet.** The panel came with a short grey
   ribbon with a black plug at each end. One end goes into the bonnet's socket.
   It is **keyed** — a notch on one side — so it only goes in one way.
3. **Plug the other end into the panel's INPUT socket.** On the back of the
   panel are two similar sockets, usually marked **INPUT** and **OUTPUT**, with
   arrows pointing away from INPUT. Use INPUT. Getting this wrong damages
   nothing — the panel just stays dark — so if it does, try the other one.
4. **Connect the panel's power cable.** The panel also came with a longer cable
   with a four-hole plug at one end and a red and a black wire at the other:
   - The **four-hole plug** pushes onto the **power pins on the back of the
     panel**.
   - The **red wire** goes into the bonnet's screw terminal marked **`+`**.
   - The **black wire** goes into the terminal marked **`−`**.

   Loosen each screw, insert the wire, tighten, then tug gently — neither should
   pull out.

   > **Red is `+`. Black is `−`.** Get this right before applying mains.

5. **Plug the 5V 4A supply's barrel jack into the bonnet's round socket.**
6. **Put the microSD card into the Pi's card slot.**
7. **Switch the supply on at the wall.** The panel may flicker or show random
   noise, and a green light on the Pi will flicker irregularly. All normal.
8. **Wait 2–3 minutes** for the first boot.

---

## Part 6 — Talk to the Pi from your computer

We'll use **SSH**, which is just a way of typing instructions to another
computer.

**On Windows:** click Start, type `PowerShell`, press Enter.
**On a Mac:** press `Cmd + Space`, type `Terminal`, press Enter.

In that window type:

```
ssh pi@spotipi.local
```

- The first time it asks *"Are you sure you want to continue connecting?"* —
  type `yes` and Enter.
- Then it asks for the password from Part 4. **Nothing appears as you type it —
  no dots, no stars. That is normal.** Press Enter.
- When the line ends in `spotipi:~ $`, **you're in.**

> **If it can't connect** ("could not resolve hostname", or it hangs): wait a
> few more minutes, check your computer is on the **same Wi-Fi**, and that the
> Wi-Fi details in Part 4 were right. If `spotipi.local` never works, log into
> your router's admin page, find the device called `spotipi`, note its IP
> address (like `192.168.1.81`) and use `ssh pi@192.168.1.81` instead.
>
> On older Windows 10 builds `.local` names sometimes don't resolve at all. The
> IP address always works.

---

## Part 7 — Install the panel driver

This is the long step. It builds the software that drives the LEDs.

```
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3-pip python3-venv git
```

Then fetch and run Adafruit's installer:

```
cd ~
python3 -m venv env --system-site-packages
source env/bin/activate
pip3 install --upgrade setuptools adafruit-python-shell click
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts
sudo -E env PATH=$PATH python3 rgb-matrix.py
```

> **If you've seen a different command:** older instructions (including
> Adafruit's own learn guide, and earlier versions of this project's README)
> tell you to `curl` a file called `rgb-matrix.sh`. Adafruit converted their
> installers from shell to Python and renamed the default branch, so that URL
> now returns a 404. The commands above are the current ones.

The installer asks a few questions:

- **Continue?** → `y`
- **Which adapter?** → **Adafruit RGB Matrix Bonnet**
- **Quality or convenience?** → **see the next section — this one matters**
- It may offer to **reserve a CPU core** for the display. Say yes; it gives a
  steadier picture and costs you a quarter of a Pi you aren't otherwise using.

It then compiles for **10–20 minutes**. Say **yes** when it offers to reboot,
then reconnect with `ssh pi@spotipi.local`.

### Quality or convenience — the one real decision in this build

The panel is refreshed by the Pi flicking its output pins on and off very fast.
The Pi has one piece of hardware that can do that with proper timing — a
**PWM** (pulse-width modulation) generator — and by default it is wired to the
**audio** output, not to the pin the bonnet uses.

That gives two ways to run the panel:

**Convenience — no soldering.** The Pi drives the pins from software. It works,
and it is what `config/rgb_options.ini` ships set up for. Because software
timing can be interrupted by anything else the Pi is doing, you get occasional
flicker: usually a faint shimmer, most visible on large areas of one colour.

**Quality — one soldered wire.** You solder a short wire between **GPIO 4** and
**GPIO 18** on the bonnet, which routes that hardware PWM to the panel's clock
pin. The timing then happens in hardware and cannot be interrupted. The
difference is clearly visible: the panel goes rock steady. This is a single
joint between two adjacent pads, perhaps five minutes' work with a basic iron —
by soldering standards it is about as easy as it gets. The installer also
disables the Pi's onboard sound on this path, because the sound hardware and
the matrix both want that same PWM.

**This guide's default is Convenience**, so that nobody is blocked from
finishing. But if you own a soldering iron, or know someone who does, **the
quality mod is worth doing** — it is the single biggest improvement available
to this build, it costs nothing but a scrap of wire, and it is reversible.

**If you chose Quality**, after the installer finishes tell the software to use
the hardware path:

```
nano ~/spotipi-photos/config/rgb_options.ini
```

Change `hardware_mapping = adafruit-hat` to `hardware_mapping = adafruit-hat-pwm`,
then `Ctrl+O`, Enter, `Ctrl+X`. (You'll do this after Part 9 has put the files
there.) Setting this **without** the soldered wire gives a blank or broken
panel, so only change it if you actually soldered.

### If you chose Convenience: turn the sound off anyway

On the convenience path the installer leaves the Pi's onboard audio enabled. The
audio hardware and the matrix share that same timing circuit, so leaving it on
makes the flicker worse than it needs to be. This Pi is a headless photo frame
with nothing plugged into its audio socket, so there is nothing to lose:

```
sudo sed -i 's/^dtparam=audio=on/dtparam=audio=off/' /boot/firmware/config.txt
grep audio /boot/firmware/config.txt
sudo reboot
```

That `grep` should print `dtparam=audio=off`. If it prints nothing, add the line
instead:

```
echo "dtparam=audio=off" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

This does **not** replace the solder mod — it removes one source of interference,
where the mod removes the cause. Doing both is better than either.

*(`install_pi.sh` in Part 11 also does this for you, and will tell you if it
made the change. Doing it here just gets the benefit a few steps sooner.)*

> **On older Raspberry Pi OS** (Bullseye and earlier) the file is `/boot/config.txt`,
> without the `firmware` part.

---

## Part 8 — Install the software's other bits

```
sudo apt install -y python3-flask python3-pil python3-requests rsync unzip
sudo pip3 install --break-system-packages spotipy
```

> **Why `--break-system-packages` — and why it isn't as alarming as it sounds.**
> Modern Raspberry Pi OS stops `pip` from installing into the system Python, to
> protect packages that `apt` manages. `spotipy` isn't one of those, so the flag
> just says "yes, I mean it". The display program runs as the administrator user
> and needs the panel driver installed system-wide, so putting things in a
> separate sandbox would cause more problems than it solves.
>
> If that fails on older Pi OS with *"no such option"*, drop the flag:
> `sudo pip3 install spotipy`.

---

## Part 9 — Copy the Spotipi software onto the Pi

The software comes as `spotipi-photos-latest.zip`.

1. Open a **second** terminal window **on your own computer** (leave the Pi one
   open). Don't type `ssh` in this one.
2. Send the zip across. Assuming it's in your Downloads folder:

   **Windows (PowerShell):**
   ```
   scp $HOME\Downloads\spotipi-photos-latest.zip pi@spotipi.local:~/
   ```
   **Mac (Terminal):**
   ```
   scp ~/Downloads/spotipi-photos-latest.zip pi@spotipi.local:~/
   ```
   Enter your Pi password when asked.
3. Back in the **Pi** window, unpack it:
   ```
   cd ~
   unzip -o spotipi-photos-latest.zip
   cd spotipi-photos
   ```

---

## Part 10 — Log in to Spotify once

The Pi needs a saved Spotify login — a "token". This is a one-off, and it uses
the credentials from Part 3.

On the **Pi**, in `~/spotipi-photos`:

```
bash generate-token.sh
```

It asks for four things, in this order:

- **Spotify Client ID** — from Part 3
- **Spotify Client Secret** — from Part 3
- **Spotify Redirect URI** — `http://127.0.0.1/callback`, exactly as registered
- **Spotify username** — from Part 3

It then prints a long `https://accounts.spotify.com/...` URL.

1. Copy that whole URL into a browser on **any** device and log in / click
   **Agree**.
2. Your browser jumps to your redirect address, and **the page will fail to
   load** — something like `http://127.0.0.1/callback?code=AQD...`. **That
   failure is expected and correct.** `127.0.0.1` means "this computer", and
   there's no web server there to answer. All we want is the address.
3. Copy that **entire** address from the browser's address bar, paste it back
   into the Pi terminal, press Enter.

It confirms with the full path of the token file it wrote — something like
`/home/pi/spotipi-photos/.cache-yourusername`. **Note that path down**; the next
part asks for it.

> **If it says the redirect URI doesn't match**, the value in the Spotify
> dashboard and the value you typed differ somewhere — a trailing slash, `http`
> vs `https`, or `localhost` vs `127.0.0.1`. They must be identical.
>
> **Roughly every six months** Spotify invalidates the authorisation and album
> art stops appearing. Re-run `bash generate-token.sh` and restart the service.
> `SPOTIFY_TOKEN_RENEWAL.txt` covers this.

---

## Part 11 — Run the installer

Still on the Pi, in `~/spotipi-photos`:

```
sudo bash install_pi.sh
```

It asks five questions:

- **Spotify username** — the same one again
- **Full path to your Spotify token** — the path Part 10 printed, in full
- **Spotify Client ID / Client Secret / Redirect URI** — from Part 3

It sets up two services that start themselves whenever the Pi is powered on:

- `spotipi` — the display program
- `spotipi-client` — the web control panel

It also switches the onboard sound off if that hasn't been done, and will say so.
If it does, reboot: `sudo reboot`.

### Set your panel size

If you bought a **32×32** panel, tell the software:

```
nano ~/spotipi-photos/config/rgb_options.ini
```

Set both `rows = 32` and `columns = 32`, then `Ctrl+O`, Enter, `Ctrl+X`, then:

```
sudo systemctl restart spotipi
```

64×64 is the shipped default and needs no change.

Check both services are running:

```
systemctl status spotipi spotipi-client
```

Press `q` to exit. You want **active (running)** for both. Within a few seconds
the panel should show the Spotipi logo — a sun over two hills.

---

## Part 12 — The control panel

On your **phone or computer**, on the same Wi-Fi, open a browser and go to:

```
http://spotipi.local
```

(No port number — this one runs on the normal web port. If the name doesn't
resolve, use the Pi's IP address.)

You get:

- **Now on the panel** — a live view of what's on the matrix, the current song
  and artist, a health dot, and stats: photo count, brightness, last sync, timer
  remaining, CPU temperature and uptime.
- **On (auto)** — Spotify art while music plays, photos otherwise. The normal
  setting.
- **Off** — blank panel.
- **Photos only** / **Spotify only** — force one source.
- **Brightness** — a live slider, 1–100, instant.
- **Photo slideshow** — seconds per photo, and **Change photo** to skip.
- **Screen timer** — switch off after N minutes.
- **Daily schedule** — a recurring off window, handling overnight correctly.
- **Sunrise/sunset dimmer** — a lower brightness at night, worked out from your
  latitude and longitude. No internet service and no API key.
- **Add photos** — upload straight from the device you're holding. On an iPhone
  this opens the camera roll.
- **iCloud Shared Album** — paste a public shared-album link and the Pi keeps
  itself in step with it. See Part 13.
- **Logo** — pick the splash the panel shows when there's nothing else to show:
  **Orange sunset** (the default) or **Pink dusk**. The choice also sets this
  page's icon, including the one an iPhone uses if you "Add to Home Screen".

The panel is **bright**. Most people settle around 40–60 in a living room, and
much lower at night.

---

## Part 13 — Getting your photos onto it

Three routes. Pick whichever matches what you own; they can be combined, and
each leaves the others' photos alone.

### Route A — an iPhone and nothing else (automatic)

This needs no computer at all. It uses an ordinary iCloud Shared Album.

1. On the iPhone, open **Photos** → **Albums** → **+** → **New Shared Album**.
   Name it (say `Spotipi`) and create it. You don't need to invite anyone.
2. Add the photos you want to that album.
3. Open the album → the **people icon** (Shared Album Details) → turn on
   **Public Website**. Tap **Share Link** and copy it. It looks like
   `https://www.icloud.com/sharedalbum/#B0Abc...`
4. On the same phone, open **`http://spotipi.local`**, find the **iCloud Shared
   Album** card, paste the link, set how often to check, and **Save**.
5. Tap **Sync now** for the first run. Photos appear on the panel within a
   minute or so.

From then on it looks after itself. Add a photo to the album on your phone and
it reaches the panel at the next check; remove one and it disappears from the
panel too.

> **What "Public Website" means.** Apple publishes the album at a long,
> unguessable web address. There is no password: **anyone you give that link to
> can see the album**, so use a dedicated album rather than sharing your camera
> roll, and don't post the link anywhere public. Nothing else about your iCloud
> account is exposed — Spotipi never asks for your Apple ID, and there is no
> password anywhere in this to give away.
>
> **A caveat worth knowing.** Apple doesn't publish or support this interface;
> Spotipi uses the same one the shared-album web page itself uses. It works, but
> Apple could change it without notice. If that ever happens, syncing stops and
> the control panel says so — the photos already on your panel stay exactly
> where they are, and Routes B and C still work.

### Route B — upload from any device (manual, any OS)

Open **`http://spotipi.local`** in a browser and use the **Add photos** card.

On an iPhone or iPad this opens your camera roll, so it's a perfectly good
iPhone-only option if you'd rather not make a shared album. On Windows, macOS or
Android it opens the normal file picker. Select as many as you like and tap
**Upload**.

Photos are cropped square and resized on the Pi, so you don't have to prepare
anything first. **Remove uploaded photos** clears the ones added this way and
deliberately leaves album-synced photos alone.

### Route C — Apple Photos on a Mac (automatic)

The original route. A job on the Mac mirrors a named album every five minutes.
Photos taken on an iPhone arrive automatically once iCloud has synced them to
that Mac. **A Mac is required** — the sync reads a macOS Photos library directly.

1. In **Apple Photos**, create an album named exactly **`Spotipi`** and add
   photos to it.
2. On the Mac, unpack your own copy of the software and install what it needs:
   ```
   cd ~/Downloads
   unzip -o spotipi-photos-latest.zip
   cd spotipi-photos/mac
   bash install_mac.sh
   ```
   If pip refuses with *"externally-managed-environment"*, use:
   `python3 -m pip install --break-system-packages --upgrade osxphotos pillow pillow-heif`
3. Set up passwordless login so the sync can run unattended:
   ```
   ssh-copy-id pi@spotipi.local
   ```
4. Test it, then run it for real:
   ```
   python3 sync_album.py --dry-run
   python3 sync_album.py
   ```
   **For a 32×32 panel add `--size 32`.**
5. Automate it every five minutes. Edit `com.spotipi.albumsync.plist` to set the
   `python3` path, the full path to `sync_album.py`, and your album and host
   values. Then:
   ```
   cp com.spotipi.albumsync.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.spotipi.albumsync.plist
   ```

**How deletion works:** the sync rebuilds the whole album as square PNGs and
mirrors it with `rsync --delete`. Remove a photo from the album and it leaves
the panel at the next sync. Photos that live only in iCloud and aren't
downloaded to the Mac are skipped with a warning — open them once in Photos to
pull them down.

### Or from a computer's command line

`tools/prepare_photos.py` crops, resizes and copies a folder of pictures from
Windows, macOS or Linux — useful for a large batch, or for scripting.

```
python3 tools/prepare_photos.py ~/Pictures/forpanel --push pi@spotipi.local
python3 tools/prepare_photos.py ~/Pictures/forpanel --size 32
```

Needs `pillow` (and `pillow-heif` for `.HEIC`). Leave `--push` off and it
prepares the files and prints the `scp` command to run yourself.

> **Which pictures work.** At 64×64, and especially at 32×32, one clear subject
> wins. Faces, pets, a building, a strong sunset. Group shots and wide
> landscapes turn to mush. Picking for that is most of what makes it look good.

---

## If something goes wrong

- **Panel completely dark.** Check the supply is on at the wall and the barrel
  plug is fully home. Check the ribbon is in the panel's **INPUT** socket — try
  the other socket if unsure. Then `systemctl status spotipi`.
- **Panel shows garbage, or flickers badly.** Confirm the sound is off:
  `grep audio /boot/firmware/config.txt` should show `dtparam=audio=off`. Then
  raise `gpio_slowdown` to 3 (then 4) in `config/rgb_options.ini` and
  `sudo systemctl restart spotipi`. If it still bothers you, the remaining fix
  is the solder mod in Part 7.
- **Panel blank right after changing the config.** If you set
  `hardware_mapping = adafruit-hat-pwm` without soldering the wire, set it back
  to `adafruit-hat`.
- **Panel dim, or colours wrong at one edge.** Almost always power — a supply
  that can't hold its current sags on bright frames.
- **Only part of the panel lights up.** `rows`/`columns` in `rgb_options.ini`
  don't match your panel. See Part 11.
- **Web page won't load.** Try the Pi's IP address instead of `spotipi.local`,
  with no port number. Then `systemctl status spotipi-client`.
- **Web page loads but the panel ignores it.** `journalctl -u spotipi -n 50`,
  and confirm the panel driver from Part 7 built.
- **`No module named flask`.** Part 8 didn't complete. Re-run it.
- **No album art, but music is playing.** The token expired. Re-run
  `bash generate-token.sh`, then `sudo systemctl restart spotipi`.
- **`INVALID_CLIENT: Invalid redirect URI`.** The redirect URI in the Spotify
  dashboard and the one you typed differ. They must match exactly.
- **Photos never arrive (Route A).** On the Mac check
  `/tmp/spotipi-albumsync.log`, and that `ssh pi@spotipi.local` works without a
  password.
- **Scheduled Mac sync finds 0 photos but running it by hand works.** macOS is
  blocking access to the Photos library. Give your `python3` **Full Disk Access**
  in System Settings → Privacy & Security.
- **Photos look letterboxed.** They were copied across without being cropped
  square. Upload them through the control panel instead, or use
  `tools/prepare_photos.py`.
- **iCloud album never syncs.** Check the album's **Public Website** switch is
  still on — turning it off invalidates the link. The control panel shows the
  last error. Then `journalctl -u spotipi-icloud -n 30` on the Pi.
- **iCloud sync says "doesn't look like a shared-album link".** You've probably
  copied the invite link rather than the public one. It must come from **Share
  Link** under Public Website, and contain `#`.
- **Uploaded photos don't appear.** The panel rescans every ten seconds. If the
  count at the top of the control panel didn't go up, the file wasn't a picture
  it could read.

---

## A few honest notes

- **It is bright.** At full brightness in a dark room it lights the whole room.
  The night dimmer exists for a reason.
- **The picture is genuinely small.** 64×64 is four thousand pixels; a phone
  screen has about three million. Accepting that is the whole trick.
- **It is always on and always drawing power** — roughly 10–20 W depending on
  brightness and size, so a few pounds a year.
- **The panel is a bare circuit board.** There's no case in this build; see the
  mounting section of `HARDWARE.md`.
- **Almost nothing leaves your house.** Your photos go from your computer to your
  Pi over your own network. The only outbound traffic is asking Spotify what's
  playing. There is no account with us and no server in the middle.
- **Your Spotify token is a login.** Anyone with the `.cache-` file can see what
  you're playing. Keep the Pi on your own network.

---

## Keeping it up to date

`mac/auto_update.sh` runs on a **Mac** every 6 hours (via
`com.spotipi.autoupdate.plist`) and watches for a newer
`spotipi-photos-latest.zip`. When one appears it pushes the code to the Pi,
restarts the services, health-checks them, and **rolls back automatically if they
fail to start**. It never touches your config, photos or token.

One-time setup on the Pi, so the Mac can restart services without a password:

```
sudo cp spotipi-update.sudoers /etc/sudoers.d/spotipi-update
sudo chmod 440 /etc/sudoers.d/spotipi-update
```

Then on the Mac:

```
cp mac/com.spotipi.autoupdate.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.spotipi.autoupdate.plist
```

The log is at `/tmp/spotipi-update.log`.

**On Windows** there is no equivalent automatic updater. Update by repeating
Part 9 with the new zip, then:

```
cd ~ && unzip -o spotipi-photos-latest.zip
sudo systemctl restart spotipi spotipi-client
```

---

*Correct as of version 2.4 — guide written 2 September 2026.*
*When Spotipi Photos is updated, this guide is reviewed and this line updated with it.*
