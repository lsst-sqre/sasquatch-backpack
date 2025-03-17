##############
Redis Backpack
##############

This page outlines how sasquatch backpack uses redis.

State Storage
=============

Sasquatch-backpack uses Redis as a mechanism for storing state. In the current implementation, Redis is used to store item IDs as keys.
In the Datasource configuration, use ``uses_redis = True`` to store the IDs of the itens sent to the Sasquatch API, as shown `here <./add_datasources.html>`__.
This way Sasquatch-backpack will remove items with duplicate IDs from subsequent POST requests.
