# Change log

sasquatch-backpack is versioned with [semver](https://semver.org/).

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/sasquatch-backpack/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-0.3.0'></a>
## 0.3.0 (2025-03-17)

### Backwards-incompatible changes

- Removed deprecated load_schema() method (replaced with schema field in the superclass)
- Added redis boolean in the source config to allow users to define wheter the source will make use of redis or not

### New features

- Adds state persistance via redis
- Updates USGS to use redis to store earthquake keys

### Other changes

- Changes filesystem structure for better ease of use when more sources are added
- Adds new tests

- Datetime is now displayed on usgs items after posting to sasquatch

<a id='changelog-0.2.2'></a>
## 0.2.2 (2024-09-18)

### New features

- Avro schemas are now generated via dataclass rather than being strictly typed

<a id='changelog-0.2.1'></a>
## 0.2.1 (2024-08-15)

### New features

- Reorganize topic_name variable

### Other changes

- Update doccumentation for api additions

<a id='changelog-0.2.0'></a>
## 0.2.0 (2024-08-06)

### New features

Reorganize project structure to better support other APIs

<a id='changelog-0.1.0'></a>
## 0.1.0 (2024-08-01)

### New features

- Initialize sasquatch-backpack
- Add the USGS API
- Add a click CLI

