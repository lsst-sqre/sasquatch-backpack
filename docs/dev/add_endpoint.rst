######################################
Adding a Datasource as an API Endpoint
######################################

This page outlines the process for adding a datasource as an API endpoint.
To follow along, you should have already `added a datasource <./add_datasources.html>`__ to the backpack click CLI.

Architecture
============

Backpack's API is built on python's FastAPI module, whose doccumentation is available `here <https://fastapi.tiangolo.com>`__.
Once the call is registered, backpack simply passes through the request parameters to click and invokes the relevant command.

Add API call schema
===================
If you want your endpoint to take arguments, you'll need to add another schema for requests to use.
A good rule of thumb is that if you exposed a parameter on your click command, you'd generally want to expose that same parameter through the API.

Navigate to your source's ``schemas.py`` file, and create your request schema.
This schema should be a pydantic BaseModel, and conform to fastAPI's "request body" standards.
You can refer the FastAPI's `official doccumentation <https://fastapi.tiangolo.com/tutorial/body/>`__ when creating your request schema.
Here's a sample:

.. code-block:: python

    from pydantic import BaseModel, Field

    class CommandnameRequest(BaseModel):
        """Hi! I'm a docstring!"""

        days: int= Field(
            description="The number of days to query "
        "back from the present."
        )

        comment: str = Field(
            default="Hi mom!",
            description="A silly comment!",
        )

This snippet allows two parameters, one of which (days) will be mandatory, due to its lack of a "default" field.

If you're adding multiple commands, add one schema, representing each command's inputs.

Add endpoint
============
Navigate to ``src/sasquatchbackpack/fastapi.py`` and add a new endpoint.
The specific implementation will fully depend on what your command is doing, but I've included some tips that a lot of implementations will likely benefit from.

.. code-block:: python

   from sasquatchbackpack.sources.sorcename.commands import commandname
   from sasquatchbackpack.sources.sorcename.schemas import CommandnameRequest

    # ...

    @app.post("/sources/sourcename/commandname/", status_code=201)
    async def sourcename_commandname(
        params: CommandnameRequest, response: Response
    ) -> None:
        """Request to query commandname.

        Parameters
        ----------
        params: CommandnameRequest
            Parameters to query
        """
        # command arguments for click
        args = [
            "-d",
            f"{params.days}",
            "-c",
            params.comment,
        ]

        try:
            # See note 1
            ctx = commandname.make_context("commandname", args)

            # capture click stdout for error handling
            with redirect_stdout(StringIO()) as out:
                commandname.invoke(ctx)

        except click.exceptions.BadParameter:
            # improper input
            response.status_code = 400
            return

        # use out.getvalue() to check stdout,
        # TODO: replace the following example with customized error handling.
        if "Error" in out.getvalue():
            response.status_code = 418

Note 1
------

The `relevant click doccumentation <https://click.palletsprojects.com/en/stable/api/#click.Command.invoke>`__ for invoking commands will be very helpful here.

On Status Codes
---------------
If a bad parameter was provided, a 400 is recommended.

If something was added to sasquatch, a 201 is recommended.

If the call found no data, a 204 is recommended.

If the call succeeded, but no data was added as a result, a 200 is recommended.

If the call failed, a 500 is recommended.


Testing
=======

To test if your command works properly, you can run ``fastapi dev src/sasquatchbackpack/fastapi.py``.

Then you can run your command from the commandline like so:

.. code-block:: bash

   curl -X 'POST' \
      'http://localhost:8000/sources/sourcename/commandname/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '3'

Or alternatively you can use the fastapi web interface which should be available at `http://127.0.0.1:8000/docs`__.
