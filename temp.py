# Temperature class

class Temperature:
    """A temperature class that stores and converts between Celsius and Fahrenheit."""
    
    def __init__(self, value: float) -> None:
        """Initialize the temperature in Celsius."""
        self._value = value
    
    @property
    def fahrenheit(self) -> float:
        """Get the temperature in Fahrenheit."""
        return (self._value * 9/5) + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        """Set the temperature in Fahrenheit."""
        self._value = (value - 32) * 5/9
    
    @property
    def celsius(self) -> float:
        """Get the temperature in Celsius."""
        return self._value
    
    @celsius.setter
    def celsius(self, value: float) -> None:
        """Set the temperature in Celsius."""
        self._value = value
    
    @property
    def is_freezing(self) -> bool:
        """Check if the temperature is below freezing point (-18C)."""
        return self._value < -18
    
    @property
    def is_boiling(self) -> bool:
        """Check if the temperature is above boiling point (100C)."""
        return self._value > 100