# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- n/a

## [1.4.1] - 2024-07-19

- Fixed source code structure.

## [1.4.0] - 2023-12-06

- Introduced OTEL tracing wrapper.

## [1.3.0] - 2022-05-10

- pubtools now includes a hook for tuning malloc at task start using the
  [glibc malloc environment variables](https://man7.org/linux/man-pages/man3/mallopt.3.html).

## [1.2.1] - 2021-08-18

- Fixed compatibility with `setuptools` older than 11.3.

## [1.2.0] - 2021-08-16

- Added `get_cert_key_paths` hook to assist with the management of SSL certificates.

## [1.1.0] - 2021-08-06

- Introduced `pubtools.hooks` entry point group to support hook-only libraries.

## [1.0.0] - 2021-07-19

- Set version to 1.0.0 to indicate that SemVer is now in effect.

## [0.3.0] - 2021-06-30

- Introduced hooks/event system in `pubtools.pluggy`. See documentation for more info.

## 0.2.0 - 2021-06-01

- Initial release from release-engineering organization

[Unreleased]: https://github.com/release-engineering/pubtools/compare/v1.4.1...HEAD
[1.4.1]: https://github.com/release-engineering/pubtools/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/release-engineering/pubtools/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/release-engineering/pubtools/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/release-engineering/pubtools/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/release-engineering/pubtools/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/release-engineering/pubtools/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/release-engineering/pubtools/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/release-engineering/pubtools/compare/v0.2.0...v0.3.0
