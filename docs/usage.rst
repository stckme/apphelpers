=====
Usage
=====

To use Common helper libraries for Python Apps in a project::

    import apphelpers

Securing APIs
=============


Example
--------

.. code-block:: python

   def foo_api():
      return "bar"

   foo_api.login_required = True

Supported directives
--------------------

login_required
~~~~~~~~~~~~~~
Boolean: True / False

If this is set to True only authenticated users are allowed to access the API.
By default APIs are public.

any_group_required
~~~~~~~~~~~~~~~
List/Tuple

User accessing the API must be member of any of the groups specified

all_groups_required
~~~~~~~~~~~~~~~
List/Tuple

User accessing the API must be member of all the groups specified

.. code-block:: python

   def foo_api():
      return "bar"

   foo_api.groups_required = ['admin', 'moderator']


groups_forbidden
~~~~~~~~~~~~~~~~

List/Tuple

API Access is forbidden to the members of specified groups.
