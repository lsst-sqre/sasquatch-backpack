###############
Publish Methods
###############

This page outlines the various methods that backpack can use to publish data to sasquatch.

Technically speaking, PublishMethod is an Enum representing each discreet mode of publishing that backpack can take advantage of. At present that includes a direct connection to the sasquatch kafka server, a rest API call, and simply nothing.

This is relevant, as any call of BackpackDispatcher's publish() method requires a PublishMethod.

Direct Connection
=================

PublishMethod.DIRECT_CONNECTION is the current default option. With sasquatch and backpack running on the same clusters, it just makes sense to directly connect in. This runs up a connection to sasquatch when publish is called, and sends published data through that tunnel.

.. warning ::

    Sasquatch-backpack version 0.4.0 does not support non-json schemas in its default publishing method. Support is planned, but in the meantime either opt to use the old publish method (PublishMethod.REST_API), or serialize any schema data to json before publishing.

REST_API
========

The classic (and previously sole) option, PublishMethod.REST_API, lives on as a publish method. This simply makes a POST request to sasquatch's API containing relevant data and schemas.

NONE
====

If you wish to simply prevent data from being sent to sasquatch with minimal changes to your code, this publish method does so.
