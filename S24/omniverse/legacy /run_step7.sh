#!/usr/bin/env bash
set -e

echo "Launching Omniverse Kit (USD Viewer)..."

# Allow Docker access to X11
xhost +local:docker >/dev/null

docker run --rm -it \
  --gpus all \
  --ipc=host \
  --net=host \
  -e DISPLAY=$DISPLAY \
  -e XAUTHORITY=$XAUTHORITY \
  -e QT_QPA_PLATFORM=xcb \
  -e __GLX_VENDOR_LIBRARY_NAME=nvidia \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -e OMNI_KIT_ALLOW_ROOT=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $XAUTHORITY:$XAUTHORITY \
  -v "$(pwd)":/workspace \
  nvcr.io/nvidia/omniverse/kit:105.1.2 \
  /kit/kit \
    /kit/apps/omni.usd.viewer.kit \
    --allow-root \
    --/app/quitAfter=0
