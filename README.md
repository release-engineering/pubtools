pubtools
========

Publishing tools project family.

- [Source](https://github.com/release-engineering/pubtools)
- [Manual]


Overview
--------

`pubtools` comprises a family of Python libraries implementing content
publishing workflows.

Each library in the `pubtools` family provides tasks for publishing or
managing content on a specific type of remote system.
These tasks are designed to be executed either as standalone command-line
utilities, or hosted within a service.

`pubtools` can be read two ways. Firstly, it is short for "publishing tools",
which describes the scope of these projects. Secondly, it can be read as
"tools for Pub", because these tools are most commonly hosted within a
service known as "Pub".

For more information, please read the online [Manual].


Notable projects
----------------

Here we list a few projects within the `pubtools` family.

This is not definitive. A more complete list is available in the
[Manual].

| Project         | Description                           |
| --------------- | ------------------------------------- |
| pubtools        | Shared functionality and docs         |
| [pubtools-pulp] | Publish content via [Pulp] 2.x        |
| [pubtools-iib]  | Manipulate operator images via [iib]  |
| [pubtools-quay] | Publish content to [quay.io]          |


License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

[Manual]: https://release-engineering.github.io/pubtools/
[pubtools-pulp]: https://github.com/release-engineering/pubtools-pulp
[Pulp]: https://pulpproject.org/
[pubtools-iib]: https://github.com/release-engineering/pubtools-iib
[iib]: https://github.com/release-engineering/iib
[pubtools-quay]: https://github.com/release-engineering/pubtools-quay
[quay.io]: https://quay.io/
