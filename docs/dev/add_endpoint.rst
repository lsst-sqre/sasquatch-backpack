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

