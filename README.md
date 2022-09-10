# Home Assistant Greenchoice Sensor
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

This is a Home Assistant custom component (sensor) that connects to the Greenchoice API to retrieve current usage data (daily meter data) and tariffs.

The sensor will check in a configurable interval if a new reading can be retrieved but Greenchoice practically only gives us one reading a day over this API. The reading is also delayed by 1 or 2 days (this seems to vary).

### Install:

[//]: # (1. Search for 'greenchoice' in [HACS]&#40;https://hacs.xyz/&#41;. )

[//]: # (    *OR*)
1. Place the 'greenchoice' folder in your 'custom_compontents' directory if it exists or create a new one under your config directory.
2. Add the integration through Settings -> Devices &amp; Services -> Add Integration, and follow the steps there. 
