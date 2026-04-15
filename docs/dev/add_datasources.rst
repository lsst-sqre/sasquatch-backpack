#######################
Adding more Datasources
#######################

This page outlines the basic process for adding more Datasources to Sasquatch-backpack.

Set up locally
==============

First, get a function that can call the Datasource's API, or obtain its data in some other fashion, working locally.

To do this, clone or fork the Sasquatch-backpack repo. You'll also probably want to run up a virtual environment, then source it.


.. code-block:: bash

    git clone https://github.com/lsst-sqre/sasquatch-backpack.git
    python3.12 -m venv .venv
    source .venv/bin/activate

Finally, run ``make init`` to finish setup.

Next, add any relevant API wrappers or other required libraries to the ``requirements/main.in`` file and run ``make update``

Make A Source Folder
====================

Every Datasource gets a folder under ``src/sasquatchbackpack/sources`` to put relevant commands, schemas, scripts, as well as anything else it might need.
Navigate to this directory, then make your Datasource an appropriately named folder.

Get the Data
============

Inside your Datasource's folder, create a python file named ``scripts.py``.
Inside this file, create a function that obtains your Datasource's data, via an API call or by other means, and returns the desired data.
It is reccomended to parameterize any required command arguments and include default values.
For example, if an API call takes location parameters then you might add a ``coordinates`` parameter,
setting its default to ``(-30.22573200864174, -70.73932987127506)``, aka: the coordinates of Cerro Pachon.
Make a similar function for each different mode of data you want to fetch from this Datasource.

Write CLI Command Logic
=======================

Sasquatch-backpack uses `click <https://click.palletsprojects.com/en/8.1.x/>`__ for its CLI.
To add your new commands to the CLI, create a new python file in your Datasource's folder named ``commands.py``
and add your CLI functions inside. There should be one function for each distinct command.

Next, populate these functions with their respective ``scripts.py`` commands, printing the results to console via ``click.echo`` (or ``click.secho`` if you want to get funky with the colors :P).
To do so import your ``scripts.py`` file that you made earlier, call relevant functions within their respective CLI wrappers, then feed in the relevant paremeters, and echo the results.
This will be what is logged in argoCD later on for debugging, so make sure logging is detailed for easier debugging down the line.

Implement commands with Click
=============================

Tag each function as ``@click.command()`` and add each parameter as a ``@click.option()``.
Next, add the command defaults as constants, refering to these constants in each relevant click option.
Do the same with any parameter validation functions you want to add, using click callbacks to trigger them.
Parameter validation functions should raise ``click.BadParameter()`` on an invalid input, and return the initial value on valid input.
Also, remember to write a help statement for each parameter.

Once complete, import your script to ``src/sasquatchbackpack/cli.py`` to access everything. You'll want to first
import your commands python script at the top of the file like so: ``from sasquatchbackpack.sources.yoursourcenamehere import commands as youraliasnamehere``.
When importing multiple Datasources to the same file, as is done in cli.py, make sure to alias the bare "commands" file to a name that can be used to differentiate your Datasource's "commands" from that of other soures, as shown in the above command via the "as" keyword.
Next, add ``main.add_command(youraliasnamehere.yourfunctionnamehere)`` at the bottom of the file.
You'll want to call ``main.add_command()`` in this way for each function you've added, so that the CLI can access them.

Test your Command
=================
At this point (assuming you've still got your venv active) you can run the following in your terminal:

.. code-block:: sh

    pip install -e .
    sasquatchbackpack yourfunctionnamehere

You should be able to see the results echoed to console as you wrote above.
Use this as an opportunity to debug your commands so they work as intended before you start sending data to sasquatch.

Add Schemas
===========

`Sasquatch <https://sasquatch.lsst.io>`__ (the wearer of the proverbial backpack), uses `Avro schemas <https://sasquatch.lsst.io/user-guide/avro.html>`__ for data serialization.
Navigate to your Datasource's folder and create a ``schemas.py`` file for your Datasource.
Inside, use `pydantic's AvroBaseModel <https://marcosschroh.github.io/dataclasses-avroschema/pydantic/>`__ to create an avro schema.
Below is a quick sample of usage.

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

            namespace = "Default"
            schema_name = "topic_name_goes_here"

Make one such schema for each command or API call you wish to make.
Each schema should reflect the data each of its objects will send to sasquatch.
Make sure to look at what data you're getting from your Datasource and use its doccumentation to create an accurate representation of that data that you'll be sending.

Note 1: Field
-------------
The imported Field method can be used to assign extra values, such as units or descriptions, to data points like so:

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
The namespace will be replaced with its actual value later on when the file is parsed, so simply keep its value "Default" as shown above.
The schema_name, on the other hand, should be hardcoded in.

Add Configs
===========
Going back to your ``scripts.py`` file, you'll want to add a configuration dataclass for each source you're adding.
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

The topic name should be the name of your command, the schema should be similarly formatted to the example, and the redis bool should be true if the relevant source will be using redis to store states.
If you're not sure whether a given source should take advantage of backpack's redis implementation, check out `how it works <./redis.html>`__ to learn more.

Add Datasources
===============
Now you're finally ready to add Datasources.
From within your ``scripts.py`` file, for each command you have, make a new Datasource class inheriting from ``sasquatchbackpack.sasquatch.Datasource``.
These new classes will require three methods: ``get_records()``, ``assemble_schema()`` and ``get_redis_key()``.

``get_records()`` should call the Datasource's respective ``scripts.py`` function, then return the encoded results in an array.
This should be surrounded with a "try" like so:

.. code-block:: python

    def get_records(self) -> list[dict]:
        """This too is a docstring"""

        try:
            # GetData()
            # return formatted_results
        except ConnectionError as ce:
            raise ConnectionError(
                f"A connection error occurred while fetching records: {ce}"
            ) from ce

``assemble_schema()`` should take one of the list items obtained by get records (or None), and the namespace. This is where that default value above is substituted. This function has two purposes. One is to create a full schema object from a provided record and the other is to provide a compliant boilerplate schema if not provided a record. This is achieved like so:

.. code-block:: python

    def assemble_schema(self, namespace: str, record:dict | None = None) -> AvroBaseModel:
        """Docstring: the third"""
        if record is None:
            schema = {
                "timestamp": 1,
                "id": "default",
                # Every object in the schema needs to be here, and provided with a boiler plate values
                #eg: "percentage":1.0,
                "namespace"=namespace,
            }
        else:
            schema = {
                "timestamp": record["timestamp"],
                "id": record["id"],
                # Again, Every object in the schema needs to be here, and provided with its record value.
                #eg: "percentage":record["percentage"]
                "namespace": namespace,
            }

        return CommandnameSchema.parse_obj(data=schema)

``get_redis_key()`` can safely return an empty string if your config has set uses_redis to false, and you don't intend to integrate this souce with backpack's redis instance.
Otherwise, this method should return a unique string structured as such: ``f"{self.topic_name}:uniqueItemIdentifierHere"``.
This identifier is best suited as an integer id number as stated above in Note #2, however can be anything that uniquely identifies this specific object.

Further, the class's constructor (``__init__``) should read in the config you made in the pervious step.
You'll also want to call ``super().__init__(config.topic_name, config.schema, uses_redis=config.uses_redis)`` inside.
Otherwise, feel free to initialize your parameters freely.

Update CLI
==========
You'll want to add a publish option to your CLI command, to allow users to specify whether or not the command should go ahead and send a publish request to kafka with the provided data or not.
To do so, add the following to your CLI command

.. code-block:: python

    @click.option(
        "--publish",
        is_flag=True,
        default=False,
        help=(
            "Allows the user to specify that the command output"
            "should be published to kafka"
        ),
    )


Remember to also add ``publish: bool,  # noqa: FBT001`` as a parameter.
You can add the funciton of the publish flag after the body of the extant function with the following:

.. code-block:: python

    click.echo(
        f"Querying USGS with publish mode {'enabled' if publish else 'disabled'}..."
    )
    #Query
    if not publish:
        click.echo("Publish mode is disabled: No data will be sent to Kafka.")
        return

    click.echo("Publish mode enabled: Sending data...")

To actually send the data, simply import and instantiate the config and source objects you made in your ``scripts.py`` file.
Then, import ``sasquatchbackpack.sasquatch`` and add the following:

.. code-block:: python

    # the params here should already exist, as you're implementing this
    # into the CLI command you've already made!
    config = scripts.MyConfigHere(params)
    source = scripts.MySourceHere(config)
    backpack_dispatcher = sasquatch.BackpackDispatcher(
        source
    )

    result, records = backpack_dispatcher.publish()

    if "Error" in result:
        click.secho(result, fg="red")
    elif "Warning" in result:
        click.secho(result, fg="yellow")
    else:
        click.secho("Data successfully sent!", fg="green")

The records returned from the publish command are the ones that the command sent.
They're very helpful for giving user feedback in the CLI!

Test it!
========
Running the CLI command should now result in the data being published to sasquatch!
Specifically you can search `kafdrop on data-int <https://data-int.lsst.cloud/kafdrop/>`__
for the ``lsst.backpack`` topic, and your data should show up there.

Make it an endpoint
===================
Backpack also supports revealing datasources as API endpoints.
To enable this behavior, you can see the `relevant doccumentation <./add_endpoint.html>`__

