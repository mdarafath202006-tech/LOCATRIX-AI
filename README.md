# LOCATRIX — AI-Powered Multi-Modal GNSS-Independent Positioning & Tracking Platform

LOCATRIX is a proposed end-to-end location assistance system for situations where GNSS/GPS signals and ordinary internet connectivity are unavailable or unreliable, such as indoor environments, underground facilities, dense urban areas, remote terrain, and emergency search-and-rescue operations.

**This repository currently contains the software prototype, a browser-based admin dashboard, and a command-line positioning simulation. It is not yet a complete, hardware-connected tracking product.** The dashboard uses illustrative data; it does not locate real people or receive live radio packets.

## Live dashboard preview

Try the browser-based dashboard: **[locatrix-ai.vercel.app](https://locatrix-ai.vercel.app/)**. This is a UI demonstration with illustrative data, not live location tracking or a hardware-connected deployment.

## Project at a glance

The intended system combines:

1. **Mobile positioning** — estimate pedestrian movement using smartphone inertial sensors and motion estimation without depending on a continuous GNSS fix.
2. **AI-assisted sensor processing** — planned algorithms can help detect steps, estimate stride length, classify motion, fuse heading observations, and characterize uncertainty.
3. **Bluetooth link** — transfer the mobile position estimate and metadata to a paired LOCATRIX field device.
4. **LoRa relay** — the field device forwards compact packets to a reachable LOCATRIX gateway over a long-range, low-power radio link.
5. **Internet-connected gateway** — a hub uploads received packets to a cloud service when internet connectivity is available.
6. **Cloud and web dashboard** — authorized operators inspect reported positions, timestamps, estimated uncertainty, movement trails, device state, and gateway/relay health.

## How the end-to-end system is intended to work

```text
Smartphone sensors
(accelerometer, gyroscope, magnetometer; optional camera)
          |
          v
Step / motion estimation + heading fusion
          |
          v
Estimated position + timestamp + uncertainty
          |
          | Bluetooth
          v
LOCATRIX field device
(Bluetooth receiver + LoRa transmitter)
          |
          | LoRa radio
          v
LOCATRIX gateway / common hub
(LoRa receiver + internet backhaul)
          |
          | HTTPS / authenticated API when internet is available
          v
Cloud ingestion + storage + access control
          |
          v
LOCATRIX admin web dashboard
(last reported position, trail, confidence, status)
```

### Important connectivity distinction

- **GNSS-independent positioning** means the estimator does not require ongoing GPS/GNSS fixes to advance the position estimate after a starting reference is supplied.
- **Internet-independent field operation** means the phone and field device can estimate and relay location locally without mobile data or Wi-Fi.
- **Cloud visibility still requires a path to a connected gateway.** If no gateway is reachable, the field device must buffer packets and forward them later when a gateway becomes available.
- Bluetooth and LoRa are communication links; they do not calculate the user's position.
- The initial geographic reference must come from a known starting point or another available positioning method. Inertial dead reckoning accumulates error over time, so uncertainty reporting and correction methods are essential.

## What is implemented in this repository now

### 1. Browser-based web dashboard — `index.html`

The dashboard is the software-side operator interface and currently demonstrates:

- Tracking overview and example person/device records.
- Last reported latitude/longitude and illustrative uncertainty.
- A schematic movement trail (not a real map or live basemap).
- Gateway and relay-chain status cards.
- A sample packet preview.
- Export of an illustrative status snapshot as JSON.
- Responsive desktop/mobile layout.

**The displayed coordinates, people, packet counts, timestamps, confidence values, and connection statuses are demo data.** The refresh action refreshes the demonstration view only. The page has no live API integration and does not connect to a phone, Bluetooth peripheral, LoRa radio, gateway, or cloud database.

### 2. Python positioning simulation — `locatrix.py`

The command-line simulation provides a reproducible starting point for the algorithmic prototype:

- Step-based pedestrian dead reckoning from a supplied initial coordinate.
- Stride-length-based distance updates.
- Circular blending of a predicted heading and compass heading.
- Approximate spherical-Earth coordinate updates.
- A simple uncertainty-growth model to illustrate drift.
- Compact relay-packet encoding/decoding with CRC32 integrity checking.

This is a teaching and development model, not a validated navigation engine. Its uncertainty values are illustrative and must not be interpreted as real-world accuracy guarantees.

## Requirements

- Python 3.10 or later for the command-line simulation.
- A modern browser for the dashboard.
- No third-party Python packages are required by the basic simulation.

## Run locally

Clone the repository and open the web dashboard:

```bash
git clone https://github.com/mdarafath202006-tech/LOCATRIX-AI.git
cd LOCATRIX-AI
```

Open `index.html` directly in a browser, or serve the folder locally:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000`.

Run the Python simulation:

```bash
python locatrix.py simulate --start-lat 13.0827 --start-lon 80.2707 --steps 10 --heading 90 --stride 0.72
python locatrix.py encode --lat 13.0830 --lon 80.2710 --steps 10
python locatrix.py decode '{"payload":"...","crc32":"..."}'
python -m unittest discover -s tests -v
```

Replace the placeholder packet in the decode example with an actual encoded packet generated by the CLI.

## Positioning approach and AI plan

A realistic implementation should separate deterministic navigation logic from learned models:

1. **Sensor acquisition:** collect timestamped accelerometer, gyroscope, and magnetometer readings from Android sensor APIs; optionally evaluate camera-based visual-inertial features where supported.
2. **Preprocessing and calibration:** account for sensor sampling rates, device orientation, bias, noise, and magnetic interference.
3. **Step detection:** detect pedestrian steps from accelerometer windows using a threshold baseline and compare it with a trained classifier if sufficient labelled data can be collected.
4. **Stride estimation:** estimate distance per step from calibrated rules or a regression model trained on measured walking sequences.
5. **Heading estimation:** combine gyroscope integration with magnetometer observations using circular-angle fusion; investigate adaptive filtering to reduce magnetic disturbance.
6. **Position update:** apply pedestrian dead reckoning from the starting reference and estimated stride/heading.
7. **Uncertainty tracking:** report the estimated error bounds and allow confidence to degrade as drift grows. A future implementation may use map constraints, landmarks, or visual-inertial odometry to correct drift.
8. **Evaluation:** compare estimates with surveyed or otherwise trusted ground truth across indoor, outdoor, corridor, turning, and GNSS-denied routes. Report median/mean position error, 95th-percentile error, drift per distance or time, step-detection F1 score, heading error, packet-delivery ratio, latency, and energy use.

**No trained AI model is currently claimed by this repository.** Model choice and performance should be justified by collected, labelled data and repeatable evaluation, not by generic claims that AI automatically improves accuracy.

## Communication and cloud plan

The proposed hardware/software interfaces are:

- **Phone app → field device:** Bluetooth Low Energy (BLE) GATT service carrying versioned, compact location packets.
- **Field device → gateway:** LoRa packet with device ID, sequence number, timestamp, coordinates/relative estimate as appropriate, uncertainty, status flags, and integrity check. LoRa coverage and payload limits depend on the radio, region, spreading factor, antenna, and deployment conditions.
- **Gateway → cloud:** authenticated HTTPS/MQTT connection when backhaul is available. Queue packets locally during outages and retry with sequence numbers to reduce duplicate or missing records.
- **Cloud → dashboard:** authenticated API and a database for user/device registration, latest locations, historical reports, gateway status, and audit events.

The CRC32 used in the simulation can detect accidental corruption; it is **not encryption or authentication**. A real deployment needs authenticated devices, encrypted network transport, authorization, retention controls, and careful handling of sensitive location data.

## Safety, privacy, and operational limitations

- The web dashboard is a prototype, not an emergency service. Do not rely on it for life-safety decisions.
- Dead reckoning error accumulates without correction; an estimated coordinate must be shown with timestamp and uncertainty.
- A location only reaches the cloud if a gateway can receive the LoRa packet and has internet access, either immediately or later after buffering.
- The system should disclose stale positions and avoid presenting old coordinates as live.
- Only authorized users should be able to view a person's location; provide consent, access logging, secure transport, and retention limits.
- LoRa does not mean unlimited range or guaranteed delivery. Field surveys and packet-loss tests are required.

## Development roadmap

- [x] Build a deterministic Python dead-reckoning and packet-integrity simulation.
- [x] Add a browser-based operator dashboard using clearly labelled demonstration data.
- [ ] Design and document a versioned location-packet schema.
- [ ] Build an Android app for timestamped sensor capture and BLE communication.
- [ ] Collect labelled sensor data with ground-truth paths and train/evaluate step or stride models.
- [ ] Implement device pairing and the BLE-to-LoRa hardware bridge.
- [ ] Implement LoRa gateway reception, buffering, and internet backhaul.
- [ ] Add authenticated cloud ingestion, storage, user/device management, and dashboard APIs.
- [ ] Run field trials and publish accuracy, drift, latency, packet-delivery, and power measurements.

## Repository structure

```text
LOCATRIX-AI/
├── index.html       # Browser-based operator dashboard (demo data)
├── locatrix.py      # Python positioning / packet simulation
├── tests/           # Unit tests for the software prototype
└── README.md        # Project concept, architecture, status, and roadmap
```

## License

Add a license file before redistributing or accepting external contributions. Until a license is specified, assume standard copyright applies.

---

**Project status:** early software prototype. The dashboard is for the software-side interface; Android sensor integration, trained models, physical Bluetooth/LoRa hardware, gateway service, cloud backend, and live tracking are future implementation work.
