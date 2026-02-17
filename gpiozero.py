class RotaryEncoder:
    def __init__(self, pin_a, pin_b, max_steps=0):
        raise RuntimeError("gpiozero stub used on non-Pi system. Use EncoderSimulator instead.")

    def close(self):
        pass


class Button:
    def __init__(self, pin, bounce_time=0.05):
        raise RuntimeError("gpiozero Button stub used on non-Pi system. Use ButtonSimulator instead.")

    def close(self):
        pass


class OutputDevice:
    def __init__(self, pin, active_high=True, initial_value=False):
        raise RuntimeError("gpiozero OutputDevice stub used on non-Pi system. Use FlashLEDSimulator instead.")

    def on(self):
        pass

    def off(self):
        pass

    def close(self):
        pass
