EMPTY_VALUES = (None, "", [], (), {})

class ValidationError(Exception):
  """Basic validation excpetion"""

class BaseLengthValidator:
  def __init__(self, limit):
    self.error_message = "Base validation error"
    self.limit = limit
    self.value = None

  def __call__(self, value):
    self.value = value
    prepared_value = self.prepare(value)
    if self.compare(prepared_value, self.limit):
      raise ValidationError(self.error_message)

  def compare(self, value, limit):
    raise NotImplementedError("Not implemented")

  def prepare(self, value):
    raise NotImplementedError("Not implemented")


class MinValueValidator(BaseLengthValidator):
  def __call__(self, value):
    self.error_message = f"Value '{value}' smaller than {self.limit}"
    super().__call__(value)

  def compare(self, value, min):
    return value < min

  def prepare(self, value):
    return len(value)

class MaxValueValidator(BaseLengthValidator):
  def __call__(self, value):
    self.error_message = f"Value '{value}' smaller than {self.limit}"
    super().__call__(value)

  def compare(self, value, max):
    return value > max

  def prepare(self, value):
    return len(value)