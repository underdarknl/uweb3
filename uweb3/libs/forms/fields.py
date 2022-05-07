
from uweb3.libs.forms import validators
from uweb3.libs.forms.validators import EMPTY_VALUES

class Field:
  def __init__(self, required=False, error_messages=None):
    self.validators = []
    self.required = required
    self.error_messages = error_messages

  def run_validators(self, name, value):
    if value in EMPTY_VALUES and self.required:
      raise validators.ValidationError(f"'{name}' is a required field")

    for validator in self.validators:
      validator(value)


class StrField(Field):
  def __init__(self, min_lenth=None, max_length=None, **kwargs):
    super().__init__(**kwargs)
    self.min_length = min_lenth
    self.max_length = max_length
    if min_lenth:
      self.validators.append(validators.MinLenValidator(min_lenth))
    if max_length:
      self.validators.append(validators.MaxLenValidator(max_length))

  def validate(self, name, value):
    value = self.clean(value)
    super().run_validators(name, value)
    return value

  def clean(self, value):
    if value not in EMPTY_VALUES:
      return str(value)
    return value

class NumberField(Field):
  def __init__(self, min_value=None, max_value=None, **kwargs):
    super().__init__(**kwargs)
    self.min_value = min_value
    self.max_value = max_value
    if min_value:
      self.validators.append(validators.MinValueValidator(min_value))
    if max_value:
      self.validators.append(validators.MaxValueValidator(max_value))

  def validate(self, name, value):
    value = self.clean(value)
    super().run_validators(name, value)
    return value

  def clean(self, value):
    try:
      return int(value)
    except:
      raise validators.ValidationError(f"Value: '{value}' is an invalid integer.")