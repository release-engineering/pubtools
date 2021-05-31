.. _projects:

Project Overview
================

In this page we list notable projects within or closely associated with the
``pubtools`` project family.

.. contents::
  :local:
  :depth: 1


Task libraries
..............

These libraries each provide a collection of :ref:`tasks <task>`, designed to be invoked either
:ref:`standalone or within a task execution environment <hosted>`.


`pubtools-pulp`_
  Tasks for publishing content via a `Pulp`_ system.

  Supports RPM-related content as well as generic files.

`pubtools-iib`_
  Tasks for manipulating operator image bundles via the `iib`_ service.

`pubtools-pyxis`_
  Tasks for manipulating metadata via the ``pyxis`` service (e.g. signatures of container images).

`pubtools-quay`_
  Tasks for publishing or manipulating content on `quay.io <quayio>`_.



Helper libraries
................

These libraries provide common functionality to be used from within the above Task libraries.

`pubtools`_
  Documentation for the ``pubtools`` project family. May later include a (very) conservative
  set of common functionality for the projects.

  You are currently reading the documentation of this project.

`pushsource`_
  Provides a common API for accessing content ("push items") from a variety of sources,
  such as: `koji`_ builds; advisories in Errata Tool; local directories.

`pushcollector`_
  A simple facade to enable collection of artifacts and push item metadata within task
  libraries.

  This glue library helps to support the :ref:`hosted` paradigm. Metadata collected by this
  library may be discarded or saved to local files during standalone task execution, and
  may be saved to a database or otherwise processed when tasks are hosted.

`pubtools-pulplib`_
  A high-level and somewhat opinionated `Pulp`_ 2.x client library.

  This library is used primarily by ``pubtools-pulp``, and also by some legacy code outside
  of the ``pubtools`` family.



.. _pushsource: https://release-engineering.github.io/pushsource/
.. _pushcollector: https://release-engineering.github.io/pushcollector/
.. _pubtools: https://release-engineering.github.io/pubtools/
.. _pubtools-pulp: https://release-engineering.github.io/pubtools-pulp/
.. _pubtools-pulplib: https://release-engineering.github.io/pubtools-pulplib/
.. _pubtools-pyxis: https://github.com/release-engineering/pubtools-pyxis
.. _pubtools-iib: https://github.com/release-engineering/pubtools-iib
.. _pubtools-quay: https://github.com/release-engineering/pubtools-quay
.. _iib: https://github.com/release-engineering/iib
.. _koji: https://fedoraproject.org/wiki/Koji
.. _pulp: https://pulpproject.org/
.. _quayio: http://quay.io/
