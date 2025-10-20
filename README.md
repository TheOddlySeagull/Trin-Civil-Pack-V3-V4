<div align="center">

# Trin Civil Pack V3 — The Trims Of Freedom

Immersive Vehicles (MTS/IV) content pack adding 34+ vehicle models with 10+ skins each—drivable, functional, and customizable.

![Trin Banner](https://raw.githubusercontent.com/TheOddlySeagull/Trin-Civil-Pack-V3/master/.github/banner.png)

[![Discord](https://img.shields.io/badge/Discord-join-7289DA?logo=discord&logoColor=white)](https://discord.gg/ujQR3wf)
[![Build Status](https://github.com/TheOddlySeagull/Trin-Civil-Pack-V3/actions/workflows/build.yml/badge.svg)](https://github.com/TheOddlySeagull/Trin-Civil-Pack-V3/actions/workflows/build.yml)

</div>

## Overview

Trin is a fictional brand for the Immersive Vehicles mod. This pack brings a wide range of cars, utility vehicles, trucks, and more to Minecraft. It is compatible with Trin & UNU parts. This is the V3/V4 generation of the pack.

Note: This pack does not add parts. You need the Trin Part Pack for engines, wheels, seats, etc. Without it, vehicles will not spawn.

- Trin Part Pack (required): https://www.curseforge.com/minecraft/mc-mods/trin-part-pack

## Download

- GitHub Actions Artifacts: Each build uploads ready-to-use JARs for 1.12.2 and 1.16.5 under the Actions run artifacts.
- Releases: Push a tag (e.g., `v4.3.2`) to trigger a release with attached JARs.

## Requirements

- Minecraft with Immersive Vehicles (MTS/IV)
- Trin Part Pack (required for parts)
- Supported MC versions targeted by this repo: 1.12.2 and 1.16.5

## Installation (Players)

1. Install Immersive Vehicles (MTS/IV) in your Minecraft mod setup.
2. Download the Trin Part Pack and this pack’s JAR.
3. Place both JARs into your `mods` folder.
4. Launch the game.

## Building (Developers)

This repository includes a Gradle multi-module build that produces versioned JARs into the `out/` directory.

Prereqs:
- JDK 8
- Git and Gradle wrapper (included)

Quick build:
- Windows: `gradlew.bat buildForge1122 && gradlew.bat buildForge1165`
- Linux/macOS: `./gradlew buildForge1122 && ./gradlew buildForge1165`

Artifacts appear under `out/` as `Trin Civil Pack-<mcversion>-<packversion>.jar`.

CI:
- The GitHub Actions workflow builds on push/PR, uploads artifacts, and publishes releases on tags.

## Other Trin Packs

- Trin Emergency Pack: https://www.curseforge.com/minecraft/mc-mods/immersive-vehicles-trin-emergency-pack
- Trin Civil Pack V2: https://www.curseforge.com/minecraft/mc-mods/immersive-vehicles-trin-civil-pack-v2
- Trin Decor Pack: https://www.curseforge.com/minecraft/mc-mods/immersive-vehicles-trin-decor-pack

## Online Configurator

Configure and visualize your dream Trin model with the Trin online configurator. (Link placeholder—add when available.)

## Feedback & Community

- Discord (official): https://discord.gg/ujQR3wf
- Issues: Use this repo’s Issues to report bugs or request features.

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history and changes.

## License & Credits

- Content and branding are © TheOddlySeagull and contributors. All rights reserved unless otherwise stated.
- Immersive Vehicles by its respective authors.
- Thanks to contributors like cowboycosmic for physics and tweaks.
