.. -*- rst -*-

List Flavors
============

.. rest_method:: GET /v2.0/lbaas/flavors

List all available flavors.

Use the ``fields`` query parameter to control which fields are
returned in the response body. Additionally, you can filter results
by using query string parameters. For information, see :ref:`filtering`.

The list might be empty.

**New in version 2.6**

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

.. literalinclude:: examples/flavor-list-curl
   :language: bash

Response Parameters
-------------------

.. rest_parameters:: ../parameters.yaml

   - description: description
   - enabled: enabled
   - flavor_profile_id: flavor-profile-id
   - flavors: flavors
   - id: flavor-id
   - name: name

Response Example
----------------

.. literalinclude:: examples/flavors-list-response.json
   :language: javascript


Show Flavor Details
===================

.. rest_method:: GET /v2.0/lbaas/flavors/{flavor_id}

Shows the details of a flavor.

Use the ``fields`` query parameter to control which fields are
returned in the response body. Additionally, you can filter results
by using query string parameters. For information, see :ref:`filtering`.

This operation does not require a request body.

**New in version 2.6**

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
   - flavor_id: path-flavor-id

Curl Example
------------

.. literalinclude:: examples/flavor-show-curl
   :language: bash

Response Parameters
-------------------

.. rest_parameters:: ../parameters.yaml

   - description: description
   - enabled: enabled
   - flavor_profile_id: flavor-profile-id
   - flavor: flavor
   - id: flavor-id
   - name: name

Response Example
----------------

.. literalinclude:: examples/flavor-show-response.json
   :language: javascript
