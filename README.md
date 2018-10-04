# Environmental Simulator Quest

| Gitter | Linux/Mac | Windows | ReadTheDocs | Test Coverage |
| --------- | --------- | --------- | ------------- | ------------- |
| [![Join the chat at https://gitter.im/Quest-Development/Quest](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Quest-Development/Quest) | [![Build Status](https://travis-ci.org/erdc/quest.svg?branch=master)](https://travis-ci.org/erdc/quest) | [![Build Status](https://ci.appveyor.com/api/projects/status/e20arxcfrcmb2ylm/branch/master?svg=true)](https://ci.appveyor.com/project/dharhas/quest) | [![Documentation Status](https://readthedocs.org/projects/quest/badge/?version=latest)](https://quest.readthedocs.io/en/latest/?badge=latest) | [![Coverage Status](https://coveralls.io/repos/github/erdc/quest/badge.svg)](https://coveralls.io/github/erdc/quest) |

### Project Description
Quest is a Python library that provides the ability to search, publish and download data (both geographical and non-geographical) from multiple data sources, including local repositories and web-based data providers. Quest also provides a suite of tools for manipulating and transforming data once it is downloaded.

### Project Links
- Here is a live link for the Quest Documentation: https://quest.readthedocs.io/en/latest/

Quest was designed to be extensible and has three types of plugins (io, tool, and provider). Provider plugins allow Quest to search for data from remote and local data providers. Tool plugins alloww Quest to perform different data manipulations. I/O plugins allows Quest to read and write different file formats.

- Here is a link to an example Quest Plugin: https://github.com/quest-dev/quest_ncep_provider_plugin