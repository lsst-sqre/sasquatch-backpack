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

Add it to the CLI
=================

Sasquatch-backpack uses `click <https://click.palletsprojects.com/en/8.1.x/>`__ for its CLI.
To add your API calls to the CLI, create a function in ``src/sasquatchbackpack/cli.py`` and tag it as ``@main.command()``
Add each parameter as a ``@click.option()``. Add the command defaults as constants in the scripts file you created earlier.
Do the same with any parameter validation functions you want to add, then import your script to ``cli.py`` to access everything.

There should be one function for every distinct API call you want to make.

Add a schema
============
`Sasquatch <https://sasquatch.lsst.io>`__ (the wearer of the proverbial backpack), uses `Avro schemas <https://sasquatch.lsst.io/user-guide/avro.html>`__
for data serialization. Navigate to ``src/sasquatchbackpack/schemas`` and create a ``.avsc`` file for each different API call you want to make.
