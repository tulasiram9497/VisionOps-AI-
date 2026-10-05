# Troubleshooting

## Camera unavailable

- Ensure the webcam is connected and available to the host OS.
- Check permissions in the OS settings.
- Use a valid video file path if testing without hardware.

## Python version

Use Python 3.11 or newer. This project was validated on Python 3.14 in the provided environment.

## Node version

Use Node 18+ for Vite and React tooling.

## Model download

YOLO models may download on first use. Ensure internet access is available and the model license is compatible with your deployment environment.

## Port conflicts

- Backend default: 8000
- Frontend default: 3000

## Docker webcam limitations

Containers often cannot directly access host webcams without special Linux configuration or device mounting. Prefer native/local execution for live webcam capture when the OS blocks container access.
