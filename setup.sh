#!/usr/bin/env bash
set -euo pipefail

# Raspberry Pi 5 NVMe HAT+ Automated Setup Script
# Configures EEPROM bootloader, sets NVMe boot order, and enables PCIe Gen 3.

echo "=========================================="
echo " Raspberry Pi 5 NVMe HAT+ Auto-Configurator"
echo "=========================================="

if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be run as root (use sudo)." >&2
  exit 1
fi

# 1. Check if running on a Raspberry Pi 5
if ! grep -q "Raspberry Pi 5" /proc/cpuinfo 2>/dev/null; then
  echo "Warning: This board does not identify as Raspberry Pi 5. Proceeding with caution..."
fi

# 2. Check for NVMe drive detection
echo "[1/4] Checking for NVMe SSD..."
if lsblk | grep -q "nvme0n1"; then
  echo "  NVMe SSD detected (/dev/nvme0n1)."
else
  echo "  Warning: /dev/nvme0n1 not currently detected."
  echo "  Verify the 16-pin FPC ribbon cable orientation and HAT+ seating."
fi

# 3. Update EEPROM to latest version
echo "[2/4] Updating bootloader EEPROM firmware..."
rpi-eeprom-update -a || true

# 4. Configure EEPROM bootloader for NVMe direct boot
echo "[3/4] Configuring EEPROM boot order (NVMe first, then SD/USB)..."
CURRENT_CONFIG=$(rpi-eeprom-config)

# Update or insert BOOT_ORDER and PCIE_PROBE
TMP_CONFIG=$(mktemp)
echo "$CURRENT_CONFIG" | grep -v -E '^(BOOT_ORDER|PCIE_PROBE)=' > "$TMP_CONFIG"
cat << 'EOF' >> "$TMP_CONFIG"
BOOT_ORDER=0xf416
PCIE_PROBE=1
EOF

rpi-eeprom-config --apply "$TMP_CONFIG"
rm -f "$TMP_CONFIG"
echo "  Bootloader configuration applied successfully."

# 5. Enable PCIe and PCIe Gen 3 in config.txt
echo "[4/4] Configuring PCIe Gen 3 in /boot/firmware/config.txt..."
CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
  CONFIG_FILE="/boot/config.txt"
fi

if [ -f "$CONFIG_FILE" ]; then
  # Remove existing pciex1 directives if present
  sed -i '/^dtparam=pciex1/d' "$CONFIG_FILE"
  sed -i '/^dtparam=pciex1_gen/d' "$CONFIG_FILE"

  # Append PCIe Gen 3 configuration under [all]
  if ! grep -q '^\[all\]' "$CONFIG_FILE"; then
    echo -e "\n[all]" >> "$CONFIG_FILE"
  fi
  cat << 'EOF' >> "$CONFIG_FILE"
dtparam=pciex1
dtparam=pciex1_gen=3
EOF
  echo "  PCIe Gen 3 enabled in $CONFIG_FILE."
else
  echo "  Warning: config.txt not found at /boot/firmware/config.txt or /boot/config.txt."
fi

echo "=========================================="
echo " Setup complete!"
echo " Next steps:"
echo " 1. If you haven't flashed Raspberry Pi OS onto /dev/nvme0n1 yet,"
echo "    run: sudo rpi-imager (or rpi-clone /dev/mmcblk0 /dev/nvme0n1)"
echo " 2. Power off (sudo poweroff), remove the SD card, and power back on."
echo "=========================================="
