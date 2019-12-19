[![Build Status](https://travis-ci.org/lebrice/SimpleParsing.svg?branch=master)](https://travis-ci.org/lebrice/SimpleParsing)

# Simple, Elegant Argument Parsing <!-- omit in toc -->


`simple-parsing` extends the capabilities of the builtin `argparse` module by allowing you to group related command-line arguments into neat, reusable [dataclasses](https://docs.python.org/3.7/library/dataclasses.html) and let the ArgumentParser take care of creating the arguments for you.

```python
# examples/demo.py
import argparse
from dataclasses import dataclass

import simple_parsing
assert issubclass(simple_parsing.ArgumentParser, argparse.ArgumentParser)

parser = simple_parsing.ArgumentParser()

@dataclass
class Options:
    """ Group of command-line arguments for this script """
    log_dir: str                # a required string parameter
    learning_rate: float = 1e-4 # An optional float parameter

# you can add arguments as you usual would
parser.add_argument("--foo", dest="foo", type=int, default=123)

# or let the parser create the arguments for you
parser.add_arguments(Options, dest="options")

args = parser.parse_args()

foo: int = args.foo             # get the parsed 'foo' value
options: Options = args.options # get the parsed Options instance  
print("foo:", foo)
print("options:", options)

```

what you get for free:

```console
$ python examples/demo.py --log_dir "logs"
foo: 123
options: Options(log_dir='logs', learning_rate=0.0001)

$ python examples/demo.py --help
usage: demo.py [-h] [--foo int] --log_dir str [--learning_rate float]

optional arguments:
  -h, --help            show this help message and exit
  --foo int

Options ['options']:
  Group of command-line arguments for this script

  --log_dir str         a required string parameter (default: None)
  --learning_rate float
                        An optional float parameter (default: 0.0001)
```

## installation
| python version |                command                  |
|----------------|-----------------------------------------|
|>= 3.7          | `pip install simple-parsing`            |
|== 3.6.X        | `pip install dataclasses simple-parsing`|


## [Examples](examples/README.md)

## [API Documentation](docs/README.md) (Under construction)

## Features 
- [Automatic "--help" strings](examples/docstrings/README.md)

    As developers, we want to make it easy for people coming into our projects to understand how to run them. However, a user-friendly `--help` message is often hard to write and to maintain, especially as the number of arguments increases.

    With `simple-parsing`, your arguments and their decriptions are defined in the same place, making your code easier to read, write, and maintain.

- Modular, Reusable Arguments *(no more copy-pasting!)*
        
    When you need to add a new group of command-line arguments similar to an existing one, instead of copy-pasting a block of `argparse` code and renaming variables, you can reuse your argument class, and let the `ArgumentParser` take care of adding `relevant` prefixes to the arguments for you:

    ```python
    parser.add_arguments(Options, dest="train")
    parser.add_arguments(Options, dest="valid")
    args = parser.parse_args()
    train_options: Options = args.train
    valid_options: Options = args.valid
    print(train_options)
    print(valid_options)
    ```
    ```console
    $ python examples/demo.py \
        --train.experiment_name "training" \
        --valid.experiment_name "validation"
    Options(experiment_name='training', learning_rate=0.0001)
    Options(experiment_name='validation', learning_rate=0.0001)
    ```
        
    These prefixes can also be set explicitly, or not be used at all. For more info, take a look at the [Prefixing Guide](examples/prefixing/README.md)

- [**Inheritance**!](examples/inheritance/README.md)
You can easily customize an existing argument class by extending it and adding your own attributes, which helps promote code reuse accross projects. For more info, take a look at the [inheritance example](examples/inheritance_example.py)

- [**Nesting**!](examples/nesting/README.md): Dataclasses can be nested within dataclasses, as deep as you need!
- [**Easy serialization**](examples/dataclasses/hyperparameters_example.py): Since dataclasses are just regular classes, its easy to add methods for easy serialization/deserialization to popular formats like `json` or `yaml`. 
- [Easier parsing of lists and tuples](examples/container_types/README.md) : This is sometimes tricky to do with regular `argparse`, but `simple-parsing` makes it a lot easier by using the python's builtin type annotations to automatically convert the values to the right type for you.

    As an added feature, by using these type annotations, `simple-parsing` allows you to parse nested lists or tuples, as can be seen in [this example](examples/merging/README.md)

- [Enums support](examples/enums/README.md)

- (More to come!)


## Examples:
Additional examples for all the features mentioned above can be found in the [examples folder](examples/README.md)
