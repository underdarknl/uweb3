
from uweb3.libs.forms.fields import Field
from uweb3.libs.forms.validators import ValidationError


class BaseMetaClass(type):
    """Collect Fields declared on the base classes."""

    def __new__(meta, name, bases, attrs):
        # Remove attributes from class and place them in a field dict.
        attrs["fields"] = {
            key: attrs.pop(key)
            for key, value in list(attrs.items())
            if isinstance(value, Field)
        }
        return super().__new__(meta, name, bases, attrs)


class BaseForm(metaclass=BaseMetaClass):
  def __init__(self):
    self.errors = []
    self.cleaned = {}

  def validate(self, data):
    for name, field in self.fields.items():
      try:
        self.cleaned[name] = field.validate(name, data.get(name, None))
      except ValidationError as ex:
        self.errors.append({name: str(ex)})

