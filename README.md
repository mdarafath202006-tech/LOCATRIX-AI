# LOCATRIX-AI

A runnable, offline-first software prototype for GNSS-independent pedestrian dead reckoning. It estimates movement from step events, stride length, and heading observations, then encodes a compact integrity-checked location packet suitable for testing a future Bluetooth/LoRa transport.

## Requirements
Python 3.10+. No third-party packages or internet required.

## Quick start
```bash
python locatrix.py simulate --start-lat 13.0827 --start-lon 80.2707 --steps 10 --heading 90 --stride 0.72
python locatrix.py encode --lat 13.0830 --lon 80.2710 --steps 10
python locatrix.py decode '{"payload":"...","crc32":"..."}'
python -m unittest discover -s tests -v
```

## Prototype model
- Each detected step advances the estimate by the supplied stride length.
- Heading is fused circularly from compass heading and gyro-predicted heading (previous heading + gyro delta).
- Latitude/longitude are updated using a local spherical-Earth approximation.
- A simple uncertainty estimate grows with each step to make drift visible.
- Relay packets include coordinates, step count, uncertainty and CRC32 integrity check.

## Important scope
This repository is a **software simulation**, not a ready-to-install Android application. It does not read real phone sensors, guarantee indoor accuracy, or transmit over LoRa by itself. Real deployment needs Android sensor integration, calibration, map/ground-truth testing, and compatible radio hardware at both sending and receiving ends. No GPS is used by the estimator after the initial coordinate is supplied.

## Next engineering steps
1. Feed timestamped accelerometer/gyroscope/magnetometer events from Android.
2. Implement adaptive step detection and user-specific stride calibration.
3. Add map constraints or visual-inertial odometry to reduce drift.
4. Connect the packet format to a Bluetooth or LoRa transport adapter and measure packet loss/latency.