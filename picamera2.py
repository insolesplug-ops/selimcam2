class Picamera2:
    """Minimal stub of Picamera2 to avoid import errors on non-Pi systems.
    Methods raise RuntimeError if used; prefer `hardware.simulator.CameraSimulator`.
    """
    def __init__(self):
        raise RuntimeError("Picamera2 stub used on non-Pi system. Use CameraSimulator instead.")

    def create_preview_configuration(self, *args, **kwargs):
        raise RuntimeError("Picamera2 stub")

    def configure(self, *args, **kwargs):
        raise RuntimeError("Picamera2 stub")

    def create_still_configuration(self, *args, **kwargs):
        raise RuntimeError("Picamera2 stub")

    def start(self):
        raise RuntimeError("Picamera2 stub")

    def stop(self):
        raise RuntimeError("Picamera2 stub")

    def capture_array(self, *args, **kwargs):
        raise RuntimeError("Picamera2 stub")

    def capture_file(self, *args, **kwargs):
        raise RuntimeError("Picamera2 stub")

    def close(self):
        pass
