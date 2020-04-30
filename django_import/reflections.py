"""
Reflections are determined by the `reflections` section of the ImportJob instance options
attribute.

Every reflection is a key-value pair, where the key is a field name, while the value is
a reflection option which determines a way to reflect data row values to this field value.

The easiest reflection option is a string. If the reflection option is a string, it corresponds
to the reflection function name, and assumes that the data contains a column having the name
equal to the field name.

Alternatively, reflection option may have a form of the key-value section, having the following structure:

- `function` determines a reflection function name

- `parameters` determines a key-value section of additional reflection function parameters

A default reflection function is `direct`, it is used if the field is not listed in the
`reflections` section.

When the data row is got, all reflection functions are called, and returned values are collected.

The returned values may be used in two stages:

- create - an instance is created or updated using
    [`update_or_create()`](https://docs.djangoproject.com/en/2.2/ref/models/querysets/#update-or-create)
    function call

- update - every value collected for this stage is assigned to the correspondent
  instance attribute, and the instance is saved

Every reflection returns data for create and update stages separately.
"""
from functools import partial

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import FieldDoesNotExist


def _get_field(model, field_name):
    """Internal helper to get the model field"""
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None


def reflection_direct(context, model, field_name, data, log, column=None):
    """
`direct` reflection sends the column value to the instance create parameters

available parameters:

- column - column name where to find a value, field name by default
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}
    if column is None:
        column = field_name
    if column not in data:
        return {}, {}
    value = data.get(column)
    return {field_name: value}, {}


def reflection_update(context, model, field_name, data, log, column=None):
    """
`update` reflection sends the column value to the instance update parameters

available parameters:

- column - column name where to find a value, field name by default
    """
    create, update = reflection_direct(context, model, field_name, data, log, column=column)
    update.update(create)
    return update, {}


def reflection_constant(context, model, field_name, data, log, value=None):
    """
`constant` reflection sets the field value to the constant

available parameters:

- value - value to be set
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}
    return {field_name: value}, {}


def reflection_avoid(*av, **kw):
    """
`avoid` reflection excludes the field from the import, to
avoid unnecessary import from the data column with the name
equal to the field name.

Any additional parameters are avoided also.
    """
    return {}, {}


def reflection_clean(context, model, field_name, data, log, column=None):
    """
`clean` reflection cleans the column value by the field clean function

available parameters:

- column - column name where to find a value, field name by default
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}

    create, update = reflection_direct(context, model, field_name, data, log, column=column)
    if not create:
        return {}, {}
    value = field.clean(list(create.values())[0], model)
    return {field_name: value}, {}


def reflection_substr(context, model, field_name, data, log, column=None, start=0, length=None):
    """
`substr` reflection gets a substring from the data column

available parameters:

- column - column name where to find a value, field name by default
- start - start index in the string, 0 by default
- length - maximal number of characters to get from the value, max_length attribute
  of the field by default
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}
    if length is None:
        length = getattr(field, 'max_length', 0)
        if not length:
            log.warning(_('Can not determine length for the substr: %s'), field_name)
            return {}, {}
    create, update = reflection_direct(context, model, field_name, data, log, column=column)
    if not create:
        return {}, {}
    value = list(create.values())[0]
    value = value[start: start + length]
    return {field_name: value}, {}


def reflection_replace(context, model, field_name, data, log, column=None, search=None, replace=None, count=None):
    """
`replace` reflection gets a value from the data column with `search` value replaced by the `replace` value.

available parameters:

- column - column name where to find a value, field name by default
- search - substring to be searched
- replace - value to replace
- count - number of occurences to replace, all by default
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}
    if search is None:
        log.warning(_('Set the search value: %s'), field_name)
        return {}, {}
    if replace is None:
        replace = ''
    create, update = reflection_direct(context, model, field_name, data, log, column=column)
    if not create:
        return {}, {}
    value = list(create.values())[0]
    if count:
        value = value.replace(search, replace, count)
    else:
        value = value.replace(search, replace)
    return {field_name: value}, {}


def reflection_format(context, model, field_name, data, log, format='<format not set>'):
    """
`format` reflection creates the field value using %-style formatting from the whole data dict

available parameters:

- format - %-style format to create a value from the dict with columns
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}
    value = format % data
    return {field_name: value}, {}


def reflection_xformat(context, model, field_name, data, log, format='<format not set>'):
    """
`xformat` reflection creates the field value using {}-style formatting from the whole data dict

available parameters:

- format - {}-style format to create a value from the dict with columns
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}
    value = format.format(data)
    return {field_name: value}, {}


def reflection_enum(context, model, field_name, data, log, column=None, mapping={}):
    """
`enum` reflection uses a mapping from the column
to field values

available parameters:

- column - column name where to find a value, field name by default
- mapping - column-to-field value mapping (column value as a key)
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}

    create, update = reflection_direct(context, model, field_name, data, log, column=column)
    if not create:
        return {}, {}
    value = list(create.values())[0]
    if value not in mapping:
        log.warning(_('Found a column value %s not in mapping: %s'), (value, field_name))
        return {}, {}
    value = mapping[value]
    return {field_name: value}, {}


def reflection_combine(context, model, field_name, data, log, reflections=[]):
    """
`combine` reflection applies several reflections sequentially,
getting output of the first and sending it as an input for
the second etc.

The output of the last is an output of the combine.

available parameters:

- reflections - a list of reflections to be applied
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}
    for r in reflections:
        if isinstance(r, str):
            r = {'function': r}
        function_name = r.get('function', None)
        if not function_name:
            log.warning(_('Function name is empty in combine: %s'), field_name)
            return {}, {}
        from django_import import reflections
        function = getattr(reflections, 'reflection_%s' % function_name, None)
        if not function:
            log.warning(_('Function name %s not found in combine: %s'), function_name, field_name)
            return {}, {}
        f = partial(function, **r.get('parameters', {}))
        c, u = f(context, model, field_name, data, log)
        data = {}
        data.update(c)
        data.update(u)
    return c, u


def reflection_lookup(context, model, field_name, data, log, column=None, lookup_field='pk'):
    """
`lookup` reflection is applied only to the foreign key or one-to-one
field reference field.

It lookups the column value in the `lookup_field` on the opposite side of
the reference, and gets the found instance, or None, if not found.

available parameters:

- column - column name where to find a value, field name by default
- lookup_field - field name of the opposide side model with the optional lookup suffix, 'pk' by default
    """
    field = _get_field(model, field_name)
    if not field:
        return {}, {}

    create, update = reflection_direct(context, model, field_name, data, log, column=column)
    if not create:
        return {}, {}
    value = list(create.values())[0]
    remote_model = field.remote_field.model
    value = remote_model.objects.filter(**{lookup_field: value}).last()
    return {field_name: value}, {}
