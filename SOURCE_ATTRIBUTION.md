# Source attribution and scope

## Road data

© OpenStreetMap contributors. Road-derived databases are supplied under the Open Data Commons Open Database License (ODbL) 1.0: https://opendatacommons.org/licenses/odbl/1-0/. Attribution and source information: https://www.openstreetmap.org/copyright. Original country extracts were obtained from Geofabrik, https://download.geofabrik.de/europe.html. The acquisition manifests identify the frozen extraction, data timestamps and checksums; a current `latest` file is not an interchangeable replacement.

The derived graph arrays transform, clip and discretize these roads and interpret selected road tags. They are not an official OpenStreetMap or Geofabrik routing product. Historical additional way tags, where used, are recovered at the timestamp in the original PBF header using the public Overpass historical API. The source of each reconstruction remains identified separately from an original PBF checksum verification.

## Flood depths and masks

European Commission Joint Research Centre, River flood hazard maps for Europe, version 3.1.1 (March 2026), DOI: https://doi.org/10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81. © European Union, 1995–2026. The supplied source copyright notice specifies Creative Commons Attribution 4.0 International: https://creativecommons.org/licenses/by/4.0/. A copy of that notice is included in `audits/jrc_copyright.txt`.

Changes in the derived inputs include road-cell intersection, nonnegative depth processing, the documented no-impedance encoding outside valid flood cells, and scenario-specific quality-mask/bridge bounds. These are the study's processing choices and do not imply endorsement by the source producer. Original quality masks are caution information, not observed absence of flooding.

## Boundaries

Eurostat GISCO Urban Audit 2018 functional urban areas, source release: https://gisco-services.ec.europa.eu/distribution/v2/urau/urau-2018-files.html. © EuroGeographics for the administrative boundaries. The package provides sampling identifiers and derived areas, while the full original boundary geometry is identified in the audit. Use the original distribution's current download and attribution terms for redistribution of its source geometry.

## External event records

Copernicus Emergency Management Service Rapid Mapping, EMSR517 (Germany, 2021), EMSR664 (Italy, 2023), and EMSR773 (Spain, 2024): https://mapping.emergency.copernicus.eu/. The package supplies derived product-level comparisons and acquisition identities. Original product documentation and attribution remain attached to the corresponding downloaded sources. Product record lengths can overlap spatially and are not unique physical road lengths. Event imagery interpretation is distinct from operational road passability.

No synthetic response from a language model was used as an observed flood, road damage, vehicle access or traffic label. The package itself is not a new empirical traffic dataset.
