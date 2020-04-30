from . import reflections


class Reflector(object):
    """
    Arbitrary context for the import process when evaluating reflections
    """


def register_reflection(name, func):
    """
    Register a new reflection function

    The reflection function should have the following signature:
    ```
    def reflection(context, model, field_name, data, log, **kwargs):
        ...
        return create, update
    ```
    where:
        - `context` is an instance of the `Reflector`
        - `model` is a model to be filled
        - `field_name` - is a name of the field to be filled
        - `data` - dictionary of all values got from the row
        - `log` - instance of the ImportLog model to be used to send logs if necessary
        - `kwargs` - additional parameters which are used from the job options.reflections.<field_name>.parameters chapter

    The returned values pair may be used in two stages:
        - create - an instance is created or updated using `update_or_create()` function call
        - update - every value collected for this stage is assigned to the correspondent
          instance attribute, and the instance is saved
    """
    setattr(reflections, name, func)
