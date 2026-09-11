# Raspberry Pi 5 NVMe HAT+ Setup & Direct Boot Guide

A complete, practical guide to assembling, configuring, and booting the Raspberry Pi 5 directly from an NVMe SSD using the official Raspberry Pi M.2 HAT+ (M Key) and an M.2 2242 NVMe SSD (such as the Corsair MP600 Micro).

---

## Table of Contents
1. [Hardware Overview & Prerequisites](#hardware-overview--prerequisites)
2. [Step 1: Hardware Inspection & Assembly](#step-1-hardware-inspection--assembly)
3. [Step 2: Bootloader & EEPROM Configuration](#step-2-bootloader--eeprom-configuration)
4. [Step 3: Flashing Raspberry Pi OS to NVMe SSD](#step-3-flashing-raspberry-pi-os-to-nvme-ssd)
5. [Step 4: Direct NVMe Boot & Enabling PCIe Gen 3](#step-4-direct-nvme-boot--enabling-pcie-gen-3)
6. [Troubleshooting & Verification](#troubleshooting--verification)

---

## Hardware Overview & Prerequisites

### Required Hardware
- **Raspberry Pi 5** (4GB, 8GB, or 16GB)
- **Official Raspberry Pi M.2 HAT+** (M Key)
- **PCIe NVMe SSD**: M.2 2230 or 2242 form factor (e.g., Corsair MP600 Micro 1TB PCIe Gen4 x4)
- **Cooling**: Raspberry Pi Active Cooler (heatsink + fan) or official case fan
- **Power Supply**: Official Raspberry Pi 27W USB-C Power Supply (5.1V / 5A) to ensure reliable power delivery to PCIe peripherals
- **MicroSD Card**: 8GB+ temporary card for initial firmware/EEPROM update
- **Standoffs & Connectors**: Included with HAT+ (16mm standoffs, GPIO stacking header extender, and 16-pin FPC ribbon cable)

---

## Step 1: Hardware Inspection & Assembly

Carefully verify each physical connection before applying power.

```
       +------------------------------------+
       |   Official Raspberry Pi M.2 HAT+   |
       |  [ M.2 2242 SSD: MP600 Micro ]     |
       +-----------------+------------------+
                         | (16-pin FPC Ribbon Cable)
       +-----------------v------------------+
       |   Raspberry Pi Active Cooler       |
       |   (Thermal pads on SoC, RP1, PMIC) |
       +-----------------+------------------+
                         | (16mm Standoffs & GPIO Extender)
       +-----------------v------------------+
       |         Raspberry Pi 5             |
       +------------------------------------+
```

### 1.1 Active Cooler Installation
1. If the Active Cooler is not yet mounted, remove the plastic protective films from the thermal pads on the underside of the heatsink.
2. Align the heatsink with the Raspberry Pi 5 SoC, RP1 I/O controller, and power management IC (PMIC).
3. Press down the two spring-loaded push-pins until they click securely through the mounting holes in the Pi 5 PCB.
4. Plug the 4-pin JST fan cable into the dedicated fan connector located between the USB ports and the 40-pin GPIO header.

### 1.2 PCIe FPC Ribbon Cable Connection
The 16-pin flexible flat cable (FFC) links the Pi 5 PCIe port to the M.2 HAT+.

1. **Pi 5 Board Side**:
   - Gently pull up the locking collar of the PCIe FPC connector on the Pi 5.
   - Insert the ribbon cable with **metal contacts facing inward** (towards the USB/Ethernet ports) and the white label facing outward.
   - Push the locking collar down squarely until it locks the cable firmly in place.
2. **M.2 HAT+ Side**:
   - Unlock the connector latch on the HAT+.
   - Insert the opposite end of the ribbon cable fully into the socket.
   - Lock the latch down flat. Check that the ribbon cable is not skewed or partially dislodged.

### 1.3 Standoffs and GPIO Header Extender
1. Screw the four 16mm brass standoffs into the corner mounting holes of the Pi 5 board.
2. Place the GPIO header extender onto the Raspberry Pi 5 GPIO pins, ensuring full pin alignment without bending.
3. Lower the M.2 HAT+ onto the standoffs and press it onto the GPIO extender.
4. Secure the HAT+ with the four mounting screws into the standoffs.

### 1.4 M.2 NVMe SSD Seating
1. Slide the Corsair MP600 Micro SSD into the M-key slot at an approximate 30-degree angle until fully seated.
2. Press the SSD down flat against the 2242 mounting standoff.
3. Secure it using the retention screw (do not overtighten).

---

## Step 2: Bootloader & EEPROM Configuration

By default, the Raspberry Pi 5 bootloader searches for boot media in this order: SD card, USB storage. To enable standalone NVMe boot without a microSD card present, configure the EEPROM boot order.

### 2.1 Prepare a Temporary MicroSD Card
1. Insert a microSD card into your PC/Mac.
2. Open **Raspberry Pi Imager**.
3. Choose device: **Raspberry Pi 5**.
4. Choose OS: **Raspberry Pi OS (64-bit)**.
5. Choose storage: Your microSD card.
6. Click **Next**, apply customization settings (username, password, Wi-Fi, SSH), and flash the card.

### 2.2 Boot & Update Firmware
1. Insert the microSD card into the Pi 5 and power it on using the official 27W power supply.
2. Open a terminal or SSH into the Pi.
3. Update package repositories and system packages:
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   ```
4. Update the bootloader EEPROM firmware to the latest stable release:
   ```bash
   sudo rpi-eeprom-update -a
   ```

### 2.3 Set Boot Order for NVMe
1. Edit the EEPROM configuration:
   ```bash
   sudo rpi-eeprom-config --edit
   ```
2. Locate the `BOOT_ORDER` entry (or add it if missing) and set it to try NVMe first, then fallback to SD and USB:
   ```ini
   BOOT_ORDER=0xf416
   ```
   *Explanation of boot codes (processed right-to-left):*
   - `6` = NVMe PCIe
   - `1` = SD card
   - `4` = USB mass storage
   - `f` = Loop back and retry

3. Ensure PCIe probe is enabled in EEPROM:
   ```ini
   PCIE_PROBE=1
   ```
4. Save and exit (in `nano`: press `Ctrl+O`, hit `Enter`, then press `Ctrl+X`).
5. Reboot to apply the new EEPROM settings:
   ```bash
   sudo reboot
   ```

---

## Step 3: Flashing Raspberry Pi OS to NVMe SSD

### 3.1 Verify NVMe Detection
After rebooting back into the microSD card OS, verify that the Corsair MP600 Micro is recognized by the kernel:

```bash
# Check block devices
lsblk
```
You should see `/dev/nvme0n1` listed alongside `mmcblk0`.

```bash
# Check PCIe bus devices
lspci
```
Expected output includes an entry like:
```text
00:00.0 PCI bridge: Broadcom Inc. and subsidiaries Device 2712 ...
01:00.0 Non-Volatile memory controller: Silicon Motion, Inc. ... (or Corsair / Phison controller)
```

### 3.2 Flash the OS

#### Method A: Using Raspberry Pi Imager directly on the Pi (Recommended)
1. Install Raspberry Pi Imager if not present:
   ```bash
   sudo apt update && sudo apt install -y rpi-imager
   ```
2. Run Raspberry Pi Imager:
   - On the desktop: Launch **Raspberry Pi Imager** from the Application Menu.
   - Or run headless / CLI:
     ```bash
     sudo rpi-imager
     ```
3. In the Imager:
   - **Device**: Select `Raspberry Pi 5`.
   - **Operating System**: Select `Raspberry Pi OS (64-bit)`.
   - **Storage**: Select `Corsair MP600 Micro (/dev/nvme0n1)`.
   - Edit OS customization settings (set user account, hostname, SSH keys, Wi-Fi).
4. Click **Write** and wait for write and verification to finish.

#### Method B: Flashing via an External PC/Mac
1. If preferred, install the MP600 Micro into an external USB M.2 NVMe enclosure.
2. Connect it to your PC/Mac and use Raspberry Pi Imager to write Raspberry Pi OS (64-bit).
3. Reinsert the SSD into the M.2 HAT+ slot and fasten the retention screw.

---

## Step 4: Direct NVMe Boot & Enabling PCIe Gen 3

### 4.1 First Direct Boot
1. Safely shut down the Raspberry Pi 5:
   ```bash
   sudo poweroff
   ```
2. Disconnect the power supply.
3. **Remove the microSD card** from the slot.
4. Reconnect the 27W USB-C power supply.
5. The Raspberry Pi 5 will boot directly from `/dev/nvme0n1` in a few seconds.

### 4.2 Enable PCIe Gen 3 Speed
The Raspberry Pi 5 defaults to PCIe Gen 2 speeds (~450 MB/s). The Corsair MP600 Micro PCIe Gen4 drive easily handles PCIe Gen 3 speeds (~850–900 MB/s) reliably over the short FPC trace.

1. Once booted into the NVMe OS, edit `/boot/firmware/config.txt`:
   ```bash
   sudo nano /boot/firmware/config.txt
   ```
2. Navigate to the `[all]` section at the bottom of the file and add:
   ```ini
   # Enable PCIe connector
   dtparam=pciex1

   # Enable PCIe Gen 3 speed (non-certified, high speed)
   dtparam=pciex1_gen=3
   ```
3. Save the file (`Ctrl+O`, `Enter`, `Ctrl+X`) and reboot:
   ```bash
   sudo reboot
   ```

---

## Troubleshooting & Verification

### 1. Verify PCIe Link Speed
Run `lspci` with verbose output to confirm the link speed:
```bash
sudo lspci -s 01:00.0 -vv | grep -i lnksta
```
- **PCIe Gen 2**: Reports `Speed 5GT/s`
- **PCIe Gen 3**: Reports `Speed 8GT/s`

### 2. Drive Read Performance Benchmark
Test read speeds using `hdparm` and `fio`:
```bash
sudo apt install -y hdparm fio
sudo hdparm -tT /dev/nvme0n1
```
Expected sequential read benchmark:
- Gen 2: ~420 – 460 MB/s
- Gen 3: ~800 – 890 MB/s

### 3. Common Issues & Solutions
- **SSD not detected in `lsblk`**:
  - Recheck the FPC ribbon cable orientation. The contacts must face inward toward the board on the Pi 5 side.
  - Verify that the connector lock is pressed completely flat.
  - Ensure the SSD is pushed all the way into the M-key connector.
- **Pi will not boot without SD card**:
  - Verify `BOOT_ORDER` in EEPROM: run `vcgencmd bootloader_config` and check that `BOOT_ORDER` contains `6` (e.g. `0xf416`).
  - Ensure the NVMe partition table includes a valid FAT32 `/boot/firmware` partition and an `ext4` root partition.
- **Instability or reboots under load**:
  - Ensure you are using the official 27W (5.1V / 5A) power supply. NVMe drives can draw instantaneous current spikes during heavy writes.
  - Check Active Cooler clearance and ensure it is properly plugged into the fan header.
