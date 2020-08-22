# CalibreLibgenStore
A Libgen Fiction store plugin for Calibre

## Installation
- Download the latest release from [here](https://github.com/fallaciousreasoning/CalibreLibgenStore/releases)
- Open Calibre
- Navigate to Preferences -> Plugins (in the advanced section) -> Load Plugin from File and select the zip file you downloaded.
- Restart Calibre

## Usage
- Click the 'Get Books' menu in Calibre
- Ensure that 'Libgen Fiction' is selected in the search providers menu
![image](https://cloud.githubusercontent.com/assets/7678024/26022030/fefe8b24-37dc-11e7-8373-16c6069fa538.png)
- Search!

## Testing & development

While working on any of the scripts, run this to update the plugin in Calibre and start it in debug mode:

```shell
calibre-customize -b . && calibre-debug -g
```

## Build a release

Run this to zip all PY files together:

```shell
./zip.sh
```
