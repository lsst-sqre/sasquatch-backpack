##############
Redis Backpack
##############

This page outlines how sasquatch backpack uses redis.

State Storage
=============

As of version 0.3.0, sasquatch backpack supports Redis for storing the state of a remote. Sources that opt in, by toggling their ``uses_redis`` boolean to true and implementing ``get_redis_key()`` will automatically write each pushed key (obtained via the get_redis_key() command) to the redis server, and will remove items with duplicate keys from subsequent post requests.
In short, redis acts as a set of keys that persists id's of items that backpack sends to the remote so they can be referenced in the future.

Plans
=====

As of 0.3.0, Values are unused, with the redis server acting as a set of keys instead. If a use for both keys and values is determined, or it becomes prudent to allow sources to self-define redis implementation, the system will be expanded. Issues and pull requests on backpack's `github <https://github.com/lsst-sqre/sasquatch-backpack>`__ are more than welcome <3

