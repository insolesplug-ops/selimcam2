"""Application state machine with strict transitions."""

from enum import Enum, auto
from typing import Callable, Dict, Optional, Set


class AppState(Enum):
    """Application states."""
    BOOT = auto()
    CAMERA = auto()
    SETTINGS = auto()
    GALLERY = auto()
    SHUTDOWN = auto()


class AppEvent(Enum):
    """Application events."""
    BOOT_COMPLETE = auto()
    OPEN_SETTINGS = auto()
    OPEN_GALLERY = auto()
    BACK_TO_CAMERA = auto()
    SHUTDOWN_REQUEST = auto()


class StateMachine:
    """
    Deterministic state machine for app flow.
    Enforces valid state transitions.
    """
    
    # Valid transitions
    TRANSITIONS: Dict[AppState, Set[AppState]] = {
        AppState.BOOT: {AppState.CAMERA},
        AppState.CAMERA: {AppState.SETTINGS, AppState.GALLERY, AppState.SHUTDOWN},
        AppState.SETTINGS: {AppState.CAMERA, AppState.SHUTDOWN},
        AppState.GALLERY: {AppState.CAMERA, AppState.SHUTDOWN},
        AppState.SHUTDOWN: set()  # Terminal state
    }
    
    def __init__(self, initial_state: AppState = AppState.BOOT):
        """
        Initialize state machine.
        
        Args:
            initial_state: Starting state
        """
        self.current_state = initial_state
        self.previous_state: Optional[AppState] = None
        
        # State callbacks
        self._on_enter_callbacks: Dict[AppState, Callable] = {}
        self._on_exit_callbacks: Dict[AppState, Callable] = {}
        
        print(f"[StateMachine] Initialized in state: {self.current_state.name}")
    
    def can_transition(self, target_state: AppState) -> bool:
        """
        Check if transition to target state is valid.
        
        Args:
            target_state: Desired state
        
        Returns:
            True if transition is allowed
        """
        return target_state in self.TRANSITIONS.get(self.current_state, set())
    
    def transition(self, target_state: AppState) -> bool:
        """
        Transition to target state.
        
        Args:
            target_state: Desired state
        
        Returns:
            True if transition successful
        """
        if not self.can_transition(target_state):
            print(f"[StateMachine] Invalid transition: {self.current_state.name} -> {target_state.name}")
            return False
        
        # Exit current state
        if self.current_state in self._on_exit_callbacks:
            self._on_exit_callbacks[self.current_state]()
        
        # Update state
        self.previous_state = self.current_state
        self.current_state = target_state
        
        print(f"[StateMachine] Transition: {self.previous_state.name} -> {self.current_state.name}")
        
        # Enter new state
        if self.current_state in self._on_enter_callbacks:
            self._on_enter_callbacks[self.current_state]()
        
        return True
    
    def handle_event(self, event: AppEvent) -> bool:
        """
        Handle event and perform appropriate transition.
        
        Args:
            event: Event to handle
        
        Returns:
            True if event caused a transition
        """
        # Event -> State mapping
        event_transitions = {
            AppEvent.BOOT_COMPLETE: AppState.CAMERA,
            AppEvent.OPEN_SETTINGS: AppState.SETTINGS,
            AppEvent.OPEN_GALLERY: AppState.GALLERY,
            AppEvent.BACK_TO_CAMERA: AppState.CAMERA,
            AppEvent.SHUTDOWN_REQUEST: AppState.SHUTDOWN
        }
        
        target_state = event_transitions.get(event)
        
        if target_state:
            return self.transition(target_state)
        
        return False
    
    def on_enter(self, state: AppState, callback: Callable) -> None:
        """Register callback for state entry."""
        self._on_enter_callbacks[state] = callback
    
    def on_exit(self, state: AppState, callback: Callable) -> None:
        """Register callback for state exit."""
        self._on_exit_callbacks[state] = callback
    
    @property
    def is_camera(self) -> bool:
        """Check if in camera state."""
        return self.current_state == AppState.CAMERA
    
    @property
    def is_settings(self) -> bool:
        """Check if in settings state."""
        return self.current_state == AppState.SETTINGS
    
    @property
    def is_gallery(self) -> bool:
        """Check if in gallery state."""
        return self.current_state == AppState.GALLERY
    
    @property
    def is_shutdown(self) -> bool:
        """Check if in shutdown state."""
        return self.current_state == AppState.SHUTDOWN