"""Camera backend with support for both picamera2 (Pi 4+) and picamera (Pi 3).
Auto-detects available camera library and uses appropriate backend.
"""

import time
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import threading
import os

# Try to detect Raspberry Pi version and available libraries
def _detect_camera_library():
    """Detect and return available camera library."""
    # Check for Pi OS camera enable flag
    if os.path.exists('/boot/firmware/config.txt') or os.path.exists('/boot/config.txt'):
        try:
            boot_file = '/boot/firmware/config.txt' if os.path.exists('/boot/firmware/config.txt') else '/boot/config.txt'
            with open(boot_file, 'r') as f:
                content = f.read()
                if 'camera_enabled=0' in content or '#camera' in content:
                    print("[Camera] ⚠️  Camera appears disabled in /boot/config.txt")
                    print("[Camera] Enable with: raspi-config → Interface → Camera")
        except:
            pass
    
    # Try picamera2 first (Pi 4, Pi 5, newer systems)
    try:
        from picamera2 import Picamera2
        from libcamera import controls
        print("[Camera] Using picamera2 (modern)")
        return 'picamera2', Picamera2, controls
    except ImportError:
        pass
    
    # Fall back to legacy picamera (Pi 3, Pi 2, Zero)
    try:
        import picamera
        print("[Camera] Using picamera (legacy) - for Pi 3/3A+/Zero/Zero W")
        return 'picamera', picamera.PiCamera, None
    except ImportError:
        pass
    
    # No camera library available
    return None, None, None

CAMERA_LIB, CameraLib, controls_module = _detect_camera_library()

# If no camera library available, use simulator
if CAMERA_LIB is None:
    print("[Camera] No camera library found (picamera2 or picamera) - using simulator")
    try:
        from hardware.simulator import CameraSimulator
        CameraBackend = CameraSimulator
    except Exception:
        pass
else:
    # Create appropriate backend based on detected library
    if CAMERA_LIB == 'picamera2':
        class CameraBackend:
            """
            PiCamera2 backend for Raspberry Pi 4/5+.
            Handles preview stream and high-resolution capture.
            """
            
            def __init__(self, 
                         preview_size: Tuple[int, int] = (640, 480),
                         capture_size: Tuple[int, int] = (2592, 1944),
                         preview_fps: int = 24):
                """
                Initialize camera using picamera2.
                """
                self.camera = CameraLib()
                
                self.preview_size = preview_size
                self.capture_size = capture_size
                self.preview_fps = preview_fps
                self.camera_lib = 'picamera2'
                
                # Frame buffer
                self._current_frame: Optional[np.ndarray] = None
                self._frame_lock = threading.Lock()
                
                # Configure camera
                self._configure_picamera2()
                
                self.is_running = False
                
                print(f"[Camera] Initialized (picamera2): preview {preview_size[0]}x{preview_size[1]} @ {preview_fps}fps, "
                      f"capture {capture_size[0]}x{capture_size[1]}")
            
            def _configure_picamera2(self) -> None:
                """Configure camera for low-latency preview."""
                preview_config = self.camera.create_preview_configuration(
                    main={"size": self.preview_size, "format": "RGB888"},
                    buffer_count=2,
                    queue=False,
                    controls={
                        "FrameRate": self.preview_fps,
                        "NoiseReductionMode": controls_module.draft.NoiseReductionModeEnum.Fast
                    }
                )
                
                self.camera.configure(preview_config)
                
                self.capture_config = self.camera.create_still_configuration(
                    main={"size": self.capture_size, "format": "RGB888"},
                    controls={
                        "NoiseReductionMode": controls_module.draft.NoiseReductionModeEnum.HighQuality
                    }
                )
            
            def start_preview(self) -> None:
                """Start preview stream."""
                if self.is_running:
                    return
                
                try:
                    self.camera.start()
                    self.is_running = True
                    time.sleep(0.1)
                    print("[Camera] Preview started")
                except Exception as e:
                    print(f"[Camera] Start preview failed: {e}")
            
            def stop_preview(self) -> None:
                """Stop preview stream."""
                if not self.is_running:
                    return
                
                try:
                    self.camera.stop()
                    self.is_running = False
                    print("[Camera] Preview stopped")
                except Exception as e:
                    print(f"[Camera] Stop preview failed: {e}")
            
            def get_preview_frame(self) -> Optional[np.ndarray]:
                """Get latest preview frame."""
                if not self.is_running:
                    return None
                
                try:
                    frame = self.camera.capture_array("main")
                    with self._frame_lock:
                        self._current_frame = frame
                    return frame
                except Exception as e:
                    return None
            
            def capture_photo(self, filepath: str, quality: int = 92) -> bool:
                """Capture high-resolution photo."""
                try:
                    was_running = self.is_running
                    if was_running:
                        self.camera.stop()
                    
                    self.camera.configure(self.capture_config)
                    self.camera.start()
                    time.sleep(0.2)
                    self.camera.capture_file(filepath, quality=quality)
                    
                    self.camera.stop()
                    preview_config = self.camera.create_preview_configuration(
                        main={"size": self.preview_size, "format": "RGB888"},
                        buffer_count=2,
                        queue=False,
                        controls={"FrameRate": self.preview_fps}
                    )
                    self.camera.configure(preview_config)
                    
                    if was_running:
                        self.camera.start()
                        self.is_running = True
                    
                    print(f"[Camera] Captured: {filepath}")
                    return True
                    
                except Exception as e:
                    print(f"[Camera] Capture failed: {e}")
                    return False
            
            def capture_array(self) -> Optional[np.ndarray]:
                """Capture high-resolution photo as numpy array."""
                try:
                    if self.is_running:
                        array = self.camera.capture_array("main")
                        return array.copy()
                    return None
                except Exception as e:
                    print(f"[Camera] Capture array failed: {e}")
                    return None
            
            def set_controls(self, **controls) -> None:
                """Set camera controls dynamically."""
                try:
                    self.camera.set_controls(controls)
                except Exception as e:
                    print(f"[Camera] Set controls failed: {e}")
            
            def cleanup(self) -> None:
                """Cleanup camera resources."""
                try:
                    if self.is_running:
                        self.camera.stop()
                    self.camera.close()
                    print("[Camera] Cleanup complete")
                except:
                    pass
    
    elif CAMERA_LIB == 'picamera':
        class CameraBackend:
            """
            Legacy PiCamera backend for Raspberry Pi 3/3A+/Zero.
            Optimized for lower RAM and CPU constraints.
            """
            
            def __init__(self, 
                         preview_size: Tuple[int, int] = (640, 480),
                         capture_size: Tuple[int, int] = (2592, 1944),
                         preview_fps: int = 24):
                """
                Initialize camera using legacy picamera.
                Automatically adjusts for Pi 3 A+ constraints.
                """
                self.camera = CameraLib()
                self.preview_size = preview_size
                self.capture_size = capture_size
                self.preview_fps = preview_fps
                self.camera_lib = 'picamera'
                
                # Frame buffer
                self._current_frame: Optional[np.ndarray] = None
                self._frame_lock = threading.Lock()
                self._frame_event = threading.Event()
                
                # Configure for Pi 3 A+ (limited RAM: 512MB)
                self._configure_picamera()
                
                self.is_running = False
                
                print(f"[Camera] Initialized (picamera/legacy): preview {preview_size[0]}x{preview_size[1]} @ {preview_fps}fps")
                print("[Camera] ℹ️  Pi 3/3A+ detected - optimized for 512MB RAM")
            
            def _configure_picamera(self) -> None:
                """
                Configure camera for Pi 3 A+ (512MB RAM, 1GHz CPU).
                Uses lower preview resolution for better frame rate.
                """
                try:
                    # Disable camera preview on display (we use pygame)
                    self.camera.led = False  # Turn off camera LED
                    
                    # Reduce preview resolution for better performance on Pi 3 A+
                    self.camera.resolution = self.preview_size
                    self.camera.framerate = min(self.preview_fps, 24)  # Cap at 24fps
                    self.camera.rotation = 0  # Adjust if needed
                    self.camera.vflip = False
                    self.camera.hflip = False
                    
                    # AWB and exposure settings
                    self.camera.exposure_mode = 'auto'
                    self.camera.awb_mode = 'auto'
                    
                    # Flatten after configuration
                    time.sleep(0.1)
                    
                    print(f"[Camera] Config: {self.camera.resolution}, {self.camera.framerate}fps")
                    
                except Exception as e:
                    print(f"[Camera] Configuration error: {e}")
            
            def start_preview(self) -> None:
                """Start preview capture thread."""
                if self.is_running:
                    return
                
                try:
                    # Use RGB capture (BGR would require conversion)
                    self._preview_thread = threading.Thread(target=self._capture_preview_thread, daemon=True)
                    self._stop_preview = False
                    self._preview_thread.start()
                    self.is_running = True
                    time.sleep(0.2)  # Warmup
                    print("[Camera] Preview started (legacy)")
                except Exception as e:
                    print(f"[Camera] Start preview failed: {e}")
            
            def _capture_preview_thread(self) -> None:
                """Background thread for capturing preview frames."""
                import io
                try:
                    while not self._stop_preview:
                        try:
                            # Capture frame to buffer
                            stream = io.BytesIO()
                            self.camera.capture(stream, format='rgb', use_video_port=True)
                            stream.seek(0)
                            
                            # Reshape into numpy array
                            frame_data = np.frombuffer(stream.getvalue(), dtype=np.uint8)
                            h, w = self.preview_size[1], self.preview_size[0]
                            frame = frame_data.reshape((h, w, 3))
                            
                            with self._frame_lock:
                                self._current_frame = frame.copy()
                            
                            self._frame_event.set()
                        except:
                            pass
                        
                        time.sleep(1.0 / self.preview_fps)
                except Exception as e:
                    print(f"[Camera] Preview thread error: {e}")
            
            def stop_preview(self) -> None:
                """Stop preview capture thread."""
                if not self.is_running:
                    return
                
                try:
                    self._stop_preview = True
                    if hasattr(self, '_preview_thread'):
                        self._preview_thread.join(timeout=1.0)
                    self.is_running = False
                    print("[Camera] Preview stopped")
                except Exception as e:
                    print(f"[Camera] Stop preview failed: {e}")
            
            def get_preview_frame(self) -> Optional[np.ndarray]:
                """Get latest preview frame (non-blocking)."""
                if not self.is_running:
                    return None
                
                try:
                    with self._frame_lock:
                        if self._current_frame is not None:
                            return self._current_frame.copy()
                    return None
                except:
                    return None
            
            def capture_photo(self, filepath: str, quality: int = 92) -> bool:
                """
                Capture high-resolution photo to file.
                For Pi 3 A+, uses streaming capture for better reliability.
                """
                try:
                    was_running = self.is_running
                    if was_running:
                        self.stop_preview()
                    
                    time.sleep(0.3)
                    
                    # Use higher resolution for capture
                    self.camera.resolution = self.capture_size
                    time.sleep(0.5)  # Warmup for high-res
                    
                    # Capture with quality setting
                    self.camera.capture(filepath, quality=quality)
                    
                    # Restore preview resolution
                    self.camera.resolution = self.preview_size
                    
                    if was_running:
                        self.start_preview()
                    
                    print(f"[Camera] Captured: {filepath}")
                    return True
                    
                except Exception as e:
                    print(f"[Camera] Capture failed: {e}")
                    return False
            
            def capture_array(self) -> Optional[np.ndarray]:
                """Capture frame as numpy array."""
                try:
                    import io
                    stream = io.BytesIO()
                    self.camera.capture(stream, format='rgb')
                    stream.seek(0)
                    
                    frame_data = np.frombuffer(stream.getvalue(), dtype=np.uint8)
                    h, w = self.preview_size[1], self.preview_size[0]
                    return frame_data.reshape((h, w, 3))
                except Exception as e:
                    print(f"[Camera] Capture array failed: {e}")
                    return None
            
            def set_controls(self, **control_dict) -> None:
                """Set camera controls dynamically."""
                try:
                    # Map common control names to picamera properties
                    mapping = {
                        'Brightness': 'brightness',
                        'Contrast': 'contrast',
                        'Saturation': 'saturation',
                        'ExposureMode': 'exposure_mode',
                        'AWBMode': 'awb_mode',
                    }
                    
                    for key, value in control_dict.items():
                        if key in mapping:
                            setattr(self.camera, mapping[key], value)
                except Exception as e:
                    print(f"[Camera] Set controls failed: {e}")
            
            def cleanup(self) -> None:
                """Cleanup camera resources."""
                try:
                    if self.is_running:
                        self.stop_preview()
                    self.camera.close()
                    print("[Camera] Cleanup complete")
                except:
                    pass