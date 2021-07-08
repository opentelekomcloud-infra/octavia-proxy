.. -*- rst -*-

List Availability Zones
=======================

.. rest_method:: GET /v2.0/lbaas/availabilityzones

List all available availability zones.

Use the ``fields`` query parameter to control which fields are
returned in the response body. Additionally, you can filter results
by using query string parameters. For information, see :ref:`filtering`.

The list might be empty.

**New in version 2.14**

.. rest_status_code:: success ../http-status.yaml

   - 200

.. rest_status_code:: error ../http-status.yaml

   - 400
   - 401
   - 500

Request
-------

.. rest_parameters:: ../parameters.yaml

   - fields: fields

Curl Example
------------

.. literalinclude:: examples/availabilityzone-list-curl
   :language: bash

Response Parameters
-------------------

.. rest_parameters:: ../parameters.yaml

   - description: description
   - enabled: enabled
   - availability_zone_profile_id: availability-zone-profile-id
   - availability_zones: availability-zones
   - name: name

Response Example
----------------

.. literalinclude:: examples/availabilityzone-list-response.json
   :language: javascript


Show Availability Zone Details
==============================

.. rest_method:: GET /v2.0/lbaas/availabilityzones/{availability_zone_name}

Shows the details of an availability zone.

Use the ``fields`` query parameter to control which fields are
returned in the response body. Additionally, you can filter results
by using query string parameters. For information, see :ref:`filtering`.

This operation does not require a request body.

**New in version 2.14**

.. rest_status_code:: success ../http-status.yaml

   - 200

.. rest_status_code:: error ../http-status.yaml

   - 401
   - 404
   - 500

Request
-------

.. rest_parameters:: ../parameters.yaml

   - fields: fields
   - availability_zone_name: path-availability-zone-name

Curl Example
------------

.. literalinclude:: examples/availabilityzone-show-curl
   :language: bash

Response Parameters
-------------------

.. rest_parameters:: ../parameters.yaml

   - description: description
   - enabled: enabled
   - availability_zone_profile_id: availability-zone-profile-id
   - availability_zone: availability_zone
   - name: name

Response Example
----------------

.. literalinclude:: examples/availabilityzone-show-response.json
   :language: javascript
