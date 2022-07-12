[![Build Status](https://api.travis-ci.com/nnseva/django-import.svg?branch=master)](https://travis-ci.com/github/nnseva/django-import)



# Django Import

The [Django Import](https://github.com/nnseva/django-import) package provides a rich Django models import feature for the admin interface as well as using any API.

The following options are present:

- synchronous as well as asynchronous (using [Celery](http://www.celeryproject.org/)) import procedure depending on the project-wide settings
- customizing project-wide storage settings to store imported files
- import any model present in the project
- restricting project-wide list of models available to import
- wide range of input file formats (with help of [pandas](https://pandas.pydata.org/docs/reference/io.html) package)
- online customizing column-to-field reflection
- wide and extendable set of conversion and checking functions for imported values

The idea of the package has been *inspired* by the [django-csvimport](https://github.com/edcrewe/django-csvimport) package which unfortunately was
too hard to modify because of very long history.

## Installation

For the stable version:

*Stable version* from the PyPi package repository
```bash
pip install django-import
```

*Last development version* from the GitHub source version control system
```
pip install git+git://github.com/nnseva/django-import.git
```

*Note* that the [Django Import](https://github.com/nnseva/django-import) package itself doesn't depend on the [Celery](http://www.celeryproject.org/) project.

if you are planning to start import procedures *asynchronously*, install [Celery](http://www.celeryproject.org/) accordingly installation
instructions in the documentation.

## Usage scenario

The user should create or save an instance of the `ImportJob` model to start the import. It may be done using any available way - from the code,
from the admin page, etc.

The `ImportJob` instance has an `upload_file` attribute which contains an imported file, `options` attribute to provide import customization options,
and `model` atrribute which references to the `ContentType` instance determining a model whose instances will be created by the import procedure.

### Start importing from the admin interface

Just add a new `Import Job`, fill the record appropriately, and save the instance. You will see an import log entry below.

You can repeat the import procedure. Every time when the `Import Job` is saved, the import procedure is repeated. You can change any attribute
of the `Import Job` between calls to save.

Delete unnecessary import log entries between `Import Job` saves just switching the delete flag `on` to the right of the import log entry.

Every start of the import procedure generates a new instance of the `ImportLog` model where you can find timestamp and detailed log of the import.

### Start importing from the arbitrary tool

Every time when you create or update the `ImportJob`, the import procedure is started, and an instance of the `ImportLog` is created.

## Customizing the import

If you don't provide any options for the `ImportJob`, the import procedure will:

- open and read file using passed `mode`, or `rb` if not set
- import all data and headers from the file using the passed `format`, or `csv` if not set
- search columns in the input file corresponding to the field names
- create model instances filling the instance field values by the data found in the correspondent input data columns

Every of these steps is customizable.

### Set the opening mode explicitly

`options` attribute value:
```json
{
    ...
    "mode": "rt",
    ...
}
```

The `mode` option allows to set the file opening mode explicitly. It can receive either `rb` (read binary), or `rt` (read text) value.

The default value is `rb`.

In case of read text mode, the `utf-8` encoding is assumed. You are free to detect and convert the text input file encoding
yourself using some external tools like iconv, enconv, etc. Some of formats, as modern XML, are self-descriptive, so you can try
to import the file unchanged without explicit mode parameter.

### Set the format explicitly

`options` attribute value:
```json
{
    ...
    "format": "csv"
    ...
}
```

You can set the `format` value to any appropriate suffix for the [`pandas.read_*`](https://pandas.pydata.org/docs/reference/io.html) function. Tested examples are `csv` with different formatting (using additional parameters), and `excel` - for `xls` and `xlsx` files. Note that you can use additional parameters to select a sheet from the excel file to import.

### Force header names

`options` attribute value:
```json
{
    ...
    "headers": [
        "id",
        "name",
        "code",
        ...
    ]
    ...
}
```

This `headers` option overrides header names. Note that number of headers in the option should correspond to the number of columns in the input file.

When the `headers` option is not set, and no any header names are recognized for some reason, headers like sequential numbers with leading zeros are used
in the following importing steps: "0001", "0002", "0003", ...
model

### Reflecting values

The most poweful option of the import procedure is customizing where and how the input values should appear in the output instances.

This customization is called *reflection* and appears in the `reflections` section of the `options` job attribute:

```json
{
    ...
    "reflections": {
        "name": "direct",
        "surname": {
            "function": "direct",
            "parameters": {
                "column": "second name"
            }
        },
        "code": {
            "function": "clean",
            "parameters": {
                "column": "passcode"
            }
        },
        "access_level": {
            "function": "constant",
            "parameters": {
                "value": 1
            }
        },
        "nationality": "avoid",
        "address": {
            "function": "format",
            "parameters": {
                "format": "%(post_code)s, %(building)s-%(apartment)s, %(street), %(city)s, %(country)s"
            }
        },
        "has_car": {
            "function": "enum",
            "parameters": {
                "column": "car",
                "mapping": {
                    "yes": true,
                    "no": false
                }
            }
        }
        ...
    }
    ...
}
```

Every *reflection* in the `reflections` option is a key-value pair, where the key is a *field name*,
while the value is a *reflection option* which determines a way how to reflect data row
values to this field value.

The reflection option determines a *reflection function*, and optional parameters section
for this function.

The easiest *reflection option* is a string. If the *reflection option* is a string, it corresponds
to the *reflection function* name, and assumes that the data contains a column having the name
equal to the field name (see the `name` reflection in the example above).

Alternatively, *reflection option* may have a form of the subsection, having the following structure:

- `function` key determines a *reflection function* name
- `parameters` key determines a subsection of additional reflection function parameters

A default *reflection function* is `direct`, it is used if the field is not listed in the
`reflections` section (the same reflection function is assigned for the `name` reflection
in the example above explicitly).

When the data row is got, all reflection functions are called, and returned values are collected.

The returned values may be used in two stages:

- create - an instance is created or updated from these values using `update_or_create()` function call
- update - every value collected for this stage is assigned to the correspondent
  instance attribute, and after the all, the instance is saved again

Every *reflection function* returns data for create and update stages separately.

The most *reflection functions* return data for the create stage. The update stage may be used when the
existence of the instance is important, for some custom field types for example.

List of core reflection functions:

- `direct` - sends data column value directly to the field on the instance *create* stage, parameters:
    - `column` - name of the data column to get a value, field name by defalut
- `update` - sends data column value to the field on the instance *update* stage. This reflection, as a rule, is used to update instance attributes which are not fields really, f.e. properties, or some custom fields. Parameters:
    - `column` - name of the data column to get a value, field name by defalut
- `constant` - sends a constant value to the field on the instance create stage, parameters:
    - `value` - value to be sent, None by default
- `avoid` - forces ignore of the field by it's name, avoiding a default direct reflection
- `clean` - sends data column value to the field on the instance create stage, cleaning it
  by the field clean method, parameters:
    - `column` - name of the data column to get a value, field name by defalut
- `substr` - sends substring of the data column value to the field on the instance create stage, parameters:
    - `column` - name of the data column to get a value, field name by defalut
    - `start` - start index in the string, 0 by default
    - `length` - maximal number of characters to get from the value, max_length attribute
      of the field by default
- `replace` - sends a value from the data column with `search` value replaced by the `replace` value, parameters:
    - `column` - column name where to find a value, field name by default
    - `search` - substring to be searched
    - `replace` - value to replace
    - `count` - number of occurences to replace, all by default
- `format` - sends a formatted value collected from the data row to the field on the instance create stage, parameters:
    - `format` - %-style format to create a value from the dictionary of data with column names as keys
- `xformat` - sends a formatted value collected from the data row to the field on the instance create stage, parameters:
    - `format` - {}-style format to create a value from the dictionary of data with column names as keys
- `enum` - sends a enum value accordingly to the mapping from data value to the field value, parameters:
    - `column` - column name where to find a value, field name by default
    - `mapping` - column-to-field value mapping (column value as a key)
- `combine` - applies several reflections sequentially, parameters:
    - `reflections` - a list of reflections to be applied
- `lookup` - lookups the column value in the `lookup_field` on the opposite side of the reference, parameters:
    - `column` - column name where to find a value, field name by default
    - `lookup_field` - field name of the opposide side model with the optional lookup suffix, 'pk' by default

You can see the detailed help with the actual list of all registered reflections at the change page of the `ImportJob` instance.

### Customizing a field list to be imported

The field list to be imported is determined as a union of two name sets:
- a model field names set
- a reflection names set

Every Django model determines a list of fields. Every such field has a name. The package tries to import all fields found in the model.

The import options contain a set of reflections [see before](#reflecting-values), with unique names. Every such a name also determines a model field or property which should be imported.

The reflection whose name is equal to the model field name, determines a reflection for this field.

The default import column name is equal to the field name.

When the import file contains a column whose name is equal to the field name, it is imported even the reflection is not declared. To avoid such an import, use the special `avoid` reflection with the name equal to the column name.


### Identify instances

`options` attribute value:
```json
{
    ...
    "identity": [
        "name",
        "surname",
        "birthday"
    ]
    ...
}
```

When the import is evaluated several times, it is important to find and update the existent instance imported before
instead of creating a new one. The `identity` option allows to select list of fields which will be used to find an existent
instance.

Any existent model fields may be included into this identity list. But note that only those of them which are really imported
will be used for the instance identification in the particular import procedure.

## Settings

### Asynchronous import procedure

The import procedure is started synchronously by default. It also can be started asynchronously
in the separate [Celery](http://www.celeryproject.org/) worker,
depending on the `async` value in the `DJANGO_IMPORT` attribute of the `settings` file:

`settings.py`
```python
DJANGO_IMPORT = {
    ...
    "async": True
    ...
}
```

The `django_import.tasks` module contains a definition of the `run_import` shared task, if you need to register it yourself instead
of the automatic procedure.

You can check whether the procedure is finished using a special `is_finished` flag of the `ImportLog` instance.

*Note* that as minimum one [Celery](http://www.celeryproject.org/) Worker process should be started
in order to start asynchronous import procedure. If no Workers are started, the import procedure will never finished.

### Models list allowed to import

Two keys containing lists in settings, `models` and `except` mean, what models are allowed to import.

If `models` key is not empty, only those models, which are included into this list, are allowed.

`settings.py`
```python
DJANGO_IMPORT = {
    ...
    "models": [
       'accounting.Debit',
       'accounting.Credit',
       'accounting.Orders',
       'accounting.Accounts',
       ...
    ],
    "except": []
    ...
}
```

Else, the `except` key enlists models which are forbidden to import using this packet. All models except enlisted are allowed to import in this case.

`settings.py`
```python
DJANGO_IMPORT = {
    ...
    "models": [],
    "except": [
       'contenttypes.ContentType',
       'admin.LogEntry',
       'auth.Permission',
       'sessions.Session',
       'django_import.ImportJob',
       'django_import.ImportLog',
       ...
    ]
    ...
}
```

### Setting up storage configuration to store files to be imported

Storage configuration is configured using the `storage` key.

The `class` key is used to setup a storage class.

The `settings` key is used to setup keyword parameters to call the storage instance constructor.

The `upload_to` key is used to setup `upload_to` keyword parameter of the `ImportJob.upload_file` field.

There is a sample of the custom storage settings for the package below:

`settings.py`
```python
DJANGO_IMPORT = {
    ...
    'storage': {
        'class': 'storages.backends.s3boto3.S3Boto3Storage',
        'settings': {
            'access_key': PROJECT_AWS_ACCESS_KEY_ID,
            'secret_key': PROJECT_AWS_SECRET_ACCESS_KEY,
            'bucket_name': PROJECT_AWS_STORAGE_BUCKET_NAME,
            'querystring_auth': PROJECT_AWS_QUERYSTRING_AUTH,
            'use_ssl': PROJECT_AWS_S3_USE_SSL,
            'default_acl': PROJECT_AWS_DEFAULT_ACL,
            'location': PROJECT_AWS_LOCATION,
            'custom_domain': PROJECT_AWS_S3_CUSTOM_DOMAIN,
        },
        'upload_to': 'imports',
    ...
}
```

### Default settings

The default settings are the folowing:

```python
DJANGO_IMPORT = {
    'storage': {
        'class': 'django.core.files.storage.FileSystemStorage',
        'settings': {
            'location': '',
        },
        'upload_to': 'uploads',
    },
    'models': [],
    'except': [
        'contenttypes.ContentType',
        'admin.LogEntry',
        'auth.Permission',
        'sessions.Session',
        'django_import.ImportJob',
        'django_import.ImportLog',
    ],
    'sync': True,
}
```

Note that the default options are united with the custom options from the `settings.py` file to get the actual value, like:

```python
options = {
    **default_options,
    **custom_options
}
```

## Import examples

### Prerequisites

We would like to import files into the model ImportModel which has the following structure:

```python
class ImportExample(models.Model):
    """ Import Example """

    name = models.CharField(
        max_length=128,
        verbose_name=_('Name'),
    )
    quantity = models.IntegerField(
        null=True, blank=True,
        verbose_name=_('Quantity'),
    )
    weight = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Weight'),
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Price'),
    )
    kind = models.CharField(
        max_length=32,
        choices=[
            ('wood', _('Wood')),
            ('steel', _('Steel')),
            ('oil', _('Oil')),
        ],
        verbose_name=_('Kind'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='examples',
        null=True, blank=True,
        verbose_name=_('User'),
        help_text=_('User who regards to this example'),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Import Example')
        verbose_name_plural = _('Import Examples')
```

We also will assume that we have (as minimum) two users in the User model with usernames `u1` and `u2`.

The `Import Example` model exists in the `tests` application of the package if you have cloned it locally using:

```bash
git clone git@github.com:nnseva/django-import.git
```

or download from the repository https://github.com/nnseva/django-import/archive/master.zip and unpack it.

The package itself should be installed as described at the top here.

Just go to the `dev` subdirectory and start the following sequentially:

```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Input superuser name and password, and see the WEB admin interface on the `http://127.0.0.1:8000/admin/` URL.

### Try a simplest import

Let we have a CSV file like this (you will find it in the `dev/tests/data` directory).

```csv
"name","quantity","weight","price","type","user"
"etewrt",123,10.3,11.11,S,"u1"
"cvbncv",112,54.333,34.12,W,"u2"
```

Create an `ImportJob` instance without options, select `ImportExample` model, upload the file and try to save it.

You will see the following log in the import log:

```
2020-05-12 08:29:49.712041+00:00: [INFO(4)] Starting import for: uploads/test_WyIyugj.csv
2020-05-12 08:29:50.051297+00:00: [INFO(4)] Trying to import uploads/test_WyIyugj.csv
2020-05-12 08:29:50.068780+00:00: [INFO(4)] Import file has been recognized, 6 columns, 2 rows: uploads/test_WyIyugj.csv
2020-05-12 08:29:50.071130+00:00: [ERROR(2)] Unexpected error: Cannot assign "'u1'": "ImportExample.user" must be a "User" instance.
2020-05-12 08:29:50.071589+00:00: [INFO(4)] Finished
```

The `ERROR` string means that we can not import for some reason, which is explained in this line: the `user` column is a user reference, and import package doesn't know, how to import it.

### Avoid importing unnecessary fields

Let we exclude a `user` column a while to make import possible. You can find an `avoid` reflection in the help page below the record which does exactly what we need now.

Change view of the `options` field from the `Tree` to the `Code` and input:

```json
{
  "reflections": {
    "user": "avoid"
  }
}
```

then press "Save and continue editing" button at the bottom.

You will find a new import log record at the bottom with the following log text:

```
2020-05-12 09:02:23.176985+00:00: [INFO(4)] Starting import for: uploads/test_WyIyugj.csv
2020-05-12 09:02:23.178720+00:00: [INFO(4)] Trying to import uploads/test_WyIyugj.csv
2020-05-12 09:02:23.182253+00:00: [INFO(4)] Import file has been recognized, 6 columns, 2 rows: uploads/test_WyIyugj.csv
2020-05-12 09:02:23.184719+00:00: [INFO(4)] Import has been processed, 2 rows successfully imported
2020-05-12 09:02:23.185278+00:00: [INFO(4)] Finished
```

The text `Import has been processed, 2 rows successfully imported` means that all 2 records are successfully imported.

You can ensure it looking to the `Import Example` instance list of the admin.

### Import columns with the `choices` option

We can see that neither `user` (which has been avoided), nor `kind` column have been imported.

Looking into the model, we can see that the `kind` column has a choice selector. Let we convert the `type` CSV column to the `kind` model field. Searching in the help on the admin page, we can see a `enum` reflection which does what we would like to have.

```json
{
  "reflections": {
    "user": "avoid",
    "kind": {
        "function": "enum",
        "parameters": {
            "column": "type",
            "mapping": {
                "S": "steel",
                "W": "wood",
                "O": "oil"
            }
        }
    }
  }
}
```

After saving the job, we can see success log. Check the imported instances. We can see, that instances have been imported successfully, but duplicated.

### Avoid duplication on the repeated import

Remove all imported instances of the `Import Example` model. We should avoid such a problem in a future, the `identity` option will help us to do it. Change options appropriately:

```json
{
  "reflections": {
    "user": "avoid",
    "kind": {
        "function": "enum",
        "parameters": {
            "column": "type",
            "mapping": {
                "S": "steel",
                "W": "wood",
                "O": "oil"
            }
        }
    }
  },
  "identity": [ "name" ]
}
```

### Delete unnecessary logs

You can also notice that there are too many log records in the interface. Just select every of them using the flag `Delete` on the right side of every such a record.

Then we will save the `Import Job` and see what happens.

The import happens successfully, all import log entries have been deleted, and a new one created with the log of the last import.

Let we save the job again and check the `Import Example` admin page. We will see that no any additional records are added, so the `identity` option helps us as we expected.

### Import a reference field

Now it's a time to make a reference to the user in the imported records. We will replace the `avoid` reflection by the special `lookup` reflection which does what we would like to have.

```json
{
  "reflections": {
    "user": {
      "function": "lookup",
      "parameters": {
        "lookup_field": "username"
      }
    },
    "kind": {
        "function": "enum",
        "parameters": {
            "column": "type",
            "mapping": {
                "S": "steel",
                "W": "wood",
                "O": "oil"
            }
        }
    }
  },
  "identity": [ "name" ]
}
```

### Import unusual format

Let we have a different format of the CSV, like the `Excel` application produces if the Russian localization is a default in the system (you will find an example in the `dev/tests/data/test-ru.csv` file).

```CSV
"name";"quantity";"weight";"price";"type";"user"
"etewrt";123;10,3;11,11;S;"u1"
"cvbncv";112;54,333;34,12;W;"u2"
```

We can pass explicit CSV convertor parameters to the conversion function (all available parameters for the CSV conversion are on the [pandas page](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html):

```json
{
  "reflections": {
    "user": {
      "function": "lookup",
      "parameters": {
        "lookup_field": "username"
      }
    },
    "kind": {
        "function": "enum",
        "parameters": {
            "column": "type",
            "mapping": {
                "S": "steel",
                "W": "wood",
                "O": "oil"
            }
        }
    }
  },
  "identity": [ "name" ],
  "format": "csv",
  "parameters": {
    "sep": ";",
    "decimal": ","
  }
}
```

Delete all previously imported records and save the job again. You will see that all records are imported successfully.

### Import an excel file

You can import the `Excel` file directly (the example is present in the `/dev/tests/data/test.xls` file). Upload a file and use the appropriate format in the options:

```json
{
  "reflections": {
    "user": {
      "function": "lookup",
      "parameters": {
        "lookup_field": "username"
      }
    },
    "kind": {
        "function": "enum",
        "parameters": {
            "column": "type",
            "mapping": {
                "S": "steel",
                "W": "wood",
                "O": "oil"
            }
        }
    }
  },
  "identity": [ "name" ],
  "format": "excel"
}
```
