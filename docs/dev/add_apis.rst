################
Adding more APIs
################

This page outlines the basic process for implementing another Source into Sasquatch-backpack

Set up locally
==============

First, get a function that can call the source's API working locally.

To do this, clone or fork the Sasquatch-backpack repo. You'll also probably want to run up a virtual environment, then source it.


.. code-block:: sh

    git clone https://github.com/lsst-sqre/sasquatch-backpack.git
    python3.12 -m .venv venv
    source .venv/bin/activate

Finally, run ``make init`` to finish setup.

Next, add your chosen API wrapper or equivalent library to the ``requirements/main.in`` file and run ``make update``

Make A Source Folder
====================

Every source gets a folder under ``src/sasquatchbackpack/sources`` to put relevant commands, schemas, scripts, as well as anything else it might need.
Navigate to this directory, then make your source an appropriately named folder.

Call the API
============

Inside your source's folder, create a python file named ``scripts.py``.
Inside this file, create a funciton that calls your desired API and returns the desired data.
It is reccomended to parameterize all of the API call's arguments and include default values.
For example, if your API call takes location parameters then you might add a ``coordinates`` parameter,
setting its default to ``(-30.22573200864174, -70.73932987127506)``, aka: the coordinates of Cerro Pachon.
Make a similar function for each different call you want to make to this API.

Write CLI Command Logic
=======================

Sasquatch-backpack uses `click <https://click.palletsprojects.com/en/8.1.x/>`__ for its CLI.
To add your API calls to the CLI, create a new python file in your source's folder named ``commands.py``
and add your CLI functions inside. There should be one function for every distinct API call you want to make.

Next, populate these functions with calls to your API, printing
the results to console via ``click.echo`` (or ``click.secho`` if you want to get funky with the colors :P).
To do so import your ``scripts.py`` file that you made earlier, call relevant functions within their respective CLI wrappers, then
feed in the relevant paremeters, and echo the results. This will be what is logged in argoCD later on
for debugging, so make sure logging is detailed for easier debugging down the line.

Implement commands with Click
=============================

Tag each function as ``@click.command()`` and add each parameter as a ``@click.option()``.
Next, add the command defaults as constants, refering to these constants in each relevant click option.
Do the same with any parameter validation functions you want to add, using click callbacks to trigger them.
Parameter validation functions should raise ``click.BadParameter()`` on an invalid input, and return the initial value on valid input.
Also, remember to write a help statement for each parameter.

Once complete, import your script to ``src/sasquatchbackpack/cli.py`` to access everything. You'll want to first
import your commands python script at the top of the file like so: ``from sasquatchbackpack.sources.yoursourcenamehere import commands as youraliasnamehere``.
When importing multiple sources to the same file, as is done in cli.py, make sure to alias the bare "commands" file to a name that can be used to differentiate
your source's "commands" from that of other soures, as shown in the above command via the "as" keyword.
Next, add ``main.add_command(youraliasnamehere.yourfunctionnamehere)`` at the bottom of the file. You'll want to call
``main.add_command()`` in this way for each function you've added, so that the CLI can access them.

Test your API Call
==================
At this point (assuming you've still got your venv active) you can run the following in your terminal:

.. code-block:: sh

    pip install -e .
    sasquatchbackpack yourfunctionnamehere

You should be able to see the results echoed to console as you wrote above.
Use this as an opportunity to debug your API calls so they work as intended before you start sending data to sasquatch.

Add a schema
============
`Sasquatch <https://sasquatch.lsst.io>`__ (the wearer of the proverbial backpack), uses `Avro schemas <https://sasquatch.lsst.io/user-guide/avro.html>`__
for data serialization. Navigate to your Source's folder and create a ``schemas.py`` file for your Source.
Inside, use `pydantic's AvroBaseModel <https://marcosschroh.github.io/dataclasses-avroschema/pydantic/>`__ to create an avro schema. Below is a quick sample of usage.

.. code-block:: python

    from dataclasses_avroschema.pydantic import AvroBaseModel
    from pydantic import Field #See note 1

    class CommandnameSchema(AvroBaseModel):
        """Remember your docstrings, kids"""

        timestamp: int
        id: int # See note 2
        # Add more values here!

        # See note 3
        class Meta:
            """Schema metadata."""

            namespace = "$namespace"
            schema_name = "$topic_name"

Make one such schema for each command or API call you wish to make. Each schema should reflect the data each of its objects will send to sasquatch. Make sure to look at what you're getting from your API call and use the doccumentation to create an accurate representation of that data that you'll be sending.

Note 1: Field
-------------
The imported Field method can be used to assign extra values, such as units or descriptions,
to data points like so:

.. code-block:: python

    # Add more values here!
    name: str = Field(description="value used to refer to this object. eg: Dennis, Jill, Leonard")
    distance: float = Field(json_schema_extra={"units": "km"})

Note 2: ID
-------------
While not required, giving each entry a unique ID is strongly reccommended to identify them from within redis.

Note 3: Meta
------------
The Meta subclass is required, and must contain both namespace and schema_name values.
These will be replaced with their actual values later on when the file is parsed, so simply keep their values as shown above, in "$thing" format.

Add configs
===========
Going back to your ``scripts.py`` file, you'll want to add a dataclass for each API call you're making.
Make sure to include all of the relevant parameters that you'll need to make that call, as well as a reference to that specific schema, a topic name, and a uses_redis boolean.

.. code-block:: python

    from dataclasses import dataclass, field
    from sasquatchbackpack.sources import schemas

    @dataclass
    class MyConfig:
        """I'm a docstring!"""

        # Parameters up here
        topic_name: str = "yourfunctionnamehere",
        schema: str = field(
            default=schemas.MyFunctionSchemaHere.avro_schema().replace("double", "float")
        )
        uses_redis: bool = field(
            default=True
        )

The topic name should be the name of your command,
the schema should be similarly formatted to the example, and
the redis bool should be true if the source will be using redis to store states. If you're not sure whether your source should take advantage of backpack's redis implementation, check out `how it works <./redis.html>`__ to learn more.

Add Source
==========
Now you're finally ready to make your source. From within your ``scripts.py`` file, you'll make a source class, inhereting from ``sasquatchbackpack.sasquatch.DataSource``. This will require two methods:
``get_records()`` and ``get_redis_key()``.

``get_records()`` should make an API call using the function you coded at the beginning, then return the encoded results in an array.
This should be surrounded with a "try" like so:

.. code-block:: python

    def get_records(self) -> list[dict]:
        """This too is a docstring"""

        try:
            # API Call
            # return results
        except ConnectionError as ce:
            raise ConnectionError(
                f"A connection error occurred while fetching records: {ce}"
            ) from ce

``get_redis_key()`` can safely return an empty string if your config has set uses_redis to false, and you don't intend to integrate this souce with backpack's redis instance. Otherwise, this method should return a unique string structured as such: ``f"{self.topic_name}:uniqueItemIdentifierHere"``. This identifier is best suited as an integer id number as stated above in Note #2, however can be anything that uniquely identifies this specific object.

Further, the class's constructor (``__init__``) should read in the config you made in the pervious step.
You'll also want to call ``super().__init__(config.topic_name, config.schema, uses_redis=config.uses_redis)`` inside. Otherwise, feel free to initialize your parameters freely.

Update CLI
==========
You'll want to add a post option to your CLI command, to allow users to specify whether or not the command should go ahead and send a post request to kafka with the provided data or not. To do so, add the following to your CLI command

.. code-block:: python

    @click.option(
        "--post",
        is_flag=True,
        default=False,
        help=(
            "Allows the user to specify that the API output should be "
            "posted to kafka"
        ),
    )


Remember to also add ``post: bool,  # noqa: FBT001`` as a parameter.
You can add the funciton of the post flag after the body of the extant function with the following:

.. code-block:: python

    click.echo(
        f"Querying USGS with post mode {'enabled' if post else 'disabled'}..."
    )
    #Query
    if not post:
        click.echo("Post mode is disabled: No data will be sent to Kafka.")
        return

    click.echo("Post mode enabled: Sending data...")

To actually send the data, simply import and instantiate the config and source objects you made in your
``scripts.py`` file. Then, import ``sasquatchbackpack.sasquatch`` and add the following:

.. code-block:: python

    # the params here should already exist, as you're implementing this
    # into the CLI command you've already made!
    config = scripts.MyConfigHere(params)
    source = scripts.MySourceHere(config)
    backpack_dispatcher = sasquatch.BackpackDispatcher(
        source
    )

    result, records = backpack_dispatcher.post()

    if "Error" in result:
        click.secho(result, fg="red")
    elif "Warning" in result:
        click.secho(result, fg="yellow")
    else:
        click.secho("Data successfully sent!", fg="green")

The records returned from the post command are the ones that the command sent. They're very helpful for giving user feedback in the CLI!

Test it!
========
Running the CLI command should now result in the data being posted to sasquatch!
Specifically you can search `kafdrop on data-int <https://data-int.lsst.cloud/kafdrop/>`_
for the ``lsst.backpack`` topic, and your data should show up there.
