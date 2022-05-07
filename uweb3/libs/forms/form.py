
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
  def __init__(self, allow_unknown=True):
    self.errors = []
    self.cleaned = {}
    self.allow_unknown = allow_unknown

  def validate(self, data):
    if not self.allow_unknown:
      for key in data.keys():
        if key not in self.fields.keys():
          self.errors.append({key: f"Unknown field {key} in data."})

    for name, field in self.fields.items():
      try:
        self.cleaned[name] = field.validate(name, data[name])
      except ValidationError as ex:
        self.errors.append({name: str(ex)})
      except KeyError as ex:
        if field.required:
          self.errors.append({name: f"'{name}' is a required field"})

