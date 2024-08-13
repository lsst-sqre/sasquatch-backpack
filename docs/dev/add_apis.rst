################
Adding more APIs
################

This page outlines the basic process for implementing another API into Sasquatch-backpack

Set up locally
==============

First, you're going to want to get a function that can call the api locally.

To do this, clone or fork the Sasquatch-backpack repo. You'll also probably want to run up a virtual environment, then source it.


.. code-block:: sh

    git clone https://github.com/lsst-sqre/sasquatch-backpack.git
    python3.12 -m .venv venv
    source .venv/bin/activate

Finally, run ``make init`` to finish setup.



Next, add your chosen API wrapper to the ``requirements/main.in`` file and run ``make update``

Call the API
============

Navigate to the ``src/sasquatchbackpack/scripts`` folder and create a python file named appropriately for the intended API.
Inside this file, create a funciton that calls your desired API and returns the desired data.
It is reccomended to parameterize all of the API call's arguments and include default values.
For example, if your API call takes location parameters then you might add a ``coordinates`` parameter, setting its default to ``(-30.22573200864174, -70.73932987127506)``, aka: the coordinates of Cerro Pachon.
Make a similar function for each different call you want to make to this API.

Create the CLI Commands
=======================

Sasquatch-backpack uses `click <https://click.palletsprojects.com/en/8.1.x/>`__ for its CLI.
To add your API calls to the CLI, create a new python file in ``src/sasquatchbackpack/commands``
and add your CLI functions inside. There should be one function for every distinct API call you want to make.

Next, populate these functions with calls to your API, printing
the results to console via ``click.echo`` (or ``click.secho`` if you want to get funky with the colors :P)
To do so import the script in ``src/sasquatchbackpack/scripts`` that you made earlier, then
feed in the relevant paremeters, and echo the results. This will be what is logged in argoCD later on
for debugging, so make sure to make echoes detailed in nature for easier debugging down the line.

Implement commands with Click
=============================

Tag each function as ``@click.command()`` and add each parameter as a ``@click.option()``.
Next, add the command defaults as constants, refering to these constants in each relevant click option.
Do the same with any parameter validation functions you want to add, using click callbacks to trigger them.
Parameter validation functions should raise ``click.BadParameter()`` on an invalid input, and return the initial value on valid input.
Also, remember to write a help statement for each parameter.

Once complete, import your script to ``src/sasquatchbackpack/cli.py`` to access everything. You'll want to first
import your commands python script at the top of the file like so: ``from sasquatchbackpack.commands import yourfilenamehere``
then add ``main.add_command(yourfilenamehere.yourfunctionnamehere)`` at the bottom of the file. You'll want to call
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
for data serialization. Navigate to ``src/sasquatchbackpack/schemas`` and create a folder for your API.
Inside, create a ``.avsc`` file for each different API call you want to make. The contents of the file depends on the data in question, so
make sure to look at what you're getting from your API call and use the doccumentation to create an accurate representation of that data that you'll be sending.

Add configs
===========
Going back to your ``src/sasquatchbackpack/scripts`` file, you'll want to add a dataclass for each different API call you want to make.
Make sure to include all of the relevant parameters that you'll need to make that call, as well as two paths to the schema file and a topic name.

.. code-block:: python

    @dataclass
    class MyConfig:
        """I'm a docstring!"""
        # Parameters up here
        schema_file: str = "src/sasquatchbackpack/schemas/yourfoldernamehere/yourschemanamehere.avsc"
        cron_schema: str = (
            "/opt/venv/lib/python3.12/site-packages/"
            "sasquatchbackpack/schemas/yourfoldernamehere/yourschemanamehere.avsc"
        )
        topic_name: str = "yourfunctionnamehere",

The first path should be the local path to the schema and the second should be the path to the schema when running in a cron job.
The topic name should be the name of your command.

Add source
==========
Next, you'll make a source class, inhereting from ``sasquatchbackpack.sasquatch.DataSource``. This will require two methods:
``load_schema()`` and ``get_records()``.

``load_schema()`` can be copied 1 to 1 from the following:

.. code-block:: python

    def load_schema(self) -> str:
        """Load the relevant schema."""
        try:
            with Path(self.config.schema_file).open("r") as file:
                return file.read()
        except FileNotFoundError:
            with Path(self.config.cron_schema).open("r") as file:
                return file.read()

``get_records()`` should make an API call, then return the encoded results in an array.
This should be surrounded with the following try:

.. code-block:: python

    try:
        # API Call
        # return results
    except ConnectionError as ce:
        raise ConnectionError(
            f"A connection error occurred while fetching records: {ce}"
        ) from ce


The class's ``__init__`` should read in the config you made in the pervious step.
You'll also want to call ``super().__init__(config.topic_name)`` inside. Otherwise, feel free to initialize your parameters as you will.

Update CLI
==========
You'll want to add a dry run option to your CLI command. To do so, add the following to your CLI command

.. code-block:: python

    @click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Perform a trial run with no data being sent to Kafka.",
    )


Remember to also add ``dry_run: bool,  # noqa: FBT001`` as a parameter.
You can add the funciton of the dry run flag after the body of the extant function with the following:

.. code-block:: python

    if dry_run:
        click.echo("Dry run mode: No data will be sent to Kafka.")
        return

    click.echo("Sending data...")

To actually send the data, simply import and instantiate the config and source objects you made in your
``src/sasquatchbackpack/scripts`` file. Then, import ``sasquatchbackpack.sasquatch`` and add the following:

.. code-block:: python

    backpack_dispatcher = sasquatch.BackpackDispatcher(
        source, sasquatch.DispatcherConfig()
    )
    result = backpack_dispatcher.post()

    if "Error" in result:
        click.secho(result, fg="red")
    else:
        click.secho("Data successfully sent!", fg="green")

Note that the ``source`` object is simply the source you just instantiated.

Test it!
========
Running the CLI command should now result in the data being posted to sasquatch!
Specifically you can search `kafdrop on data-int <https://data-int.lsst.cloud/kafdrop/>`_
for the ``lsst.backpack`` topic, and your data should show up there.