# Urban road flood screening

Sole creator: Junjie Zhang, Shanghai International Studies University, ORCID 0009-0004-8821-4018.

Version 1.0.0 contains the actual derived data, code and results needed for the complete 36-area scenario analysis. Download the source archive for this tag and extract it to a working directory. This release is intended for automatic Zenodo archiving; a DOI is not asserted until the public Zenodo record is verified.

## Quick numerical reproduction

Install requirements.txt, then run `python -B runtime_safe.py portable_hazard.py --output D:/MLWork/fresh_archive_check --codes ES059L1 --cumulative`. Pass all 36 directory names from `hazard_inputs` to `--codes` to recompute all areas. Output must be outside the archive in a working directory. `archive_manifest.json` records all distributed file identities.

## Original sources

Original GISCO boundaries, the GEOSTAT raster/factsheet and cartographic outlines are not bundled in this public release. Source allocation and country-map reproduction require these optional files, acquired under provider terms. Main routing and the archived metric comparisons use included derived inputs and require no original source download. See THIRD_PARTY_TERMS.md and `fetch_optional_sources.py --help`. Recover these optional original files before source allocation or country-map reproduction.

Natural Hazards
Population geography and hazard intensity in urban road flood screening
Junjie Zhang; Shanghai Academy of Global Governance & Area Studies, and School of Economics and Finance, Shanghai International Studies University, Shanghai 201620, China; junjiezhang2024@shisu.edu.cn; ORCID 0009-0004-8821-4018

Online Resource 1: derived inputs, executable code, complete scenario results, source provenance and numerical verification records for 36 study areas. No new numerical analysis was performed during submission formatting. Original third-party licenses remain applicable.

Graphics were generated with Python and Matplotlib. The upload graphics are vector PDF with embedded fonts and 1200 dpi RGB TIFF rasterizations.

# Natural Hazards revision: cross-intensity and population geography

Run a complete fresh 384-row factorial for a selected city:
```
python -B runtime_safe.py portable_hazard.py --output D:/MLWork/fresh_hazard_check --codes ES059L1
```
Use a new output directory outside this package. This verifies inputs and recomputes shortest paths; it does not read the archived absolute matrix paths. Each city comparison checks 1,152 numerical metrics against the delivered reference. Add `--cumulative` to recompute and verify the explicit monotone-depth envelope control. The driver uses the occupied population endpoints, both road scopes, three return periods, four impedance scales, two bridge assumptions, two mask assumptions and four origin/destination weighting combinations.

`hazard_inputs` contains locally intersected RP10/RP100/RP500 depths and common geometry from the same JRC source release. `hazard_reference` is the complete reference output; its absolute cached-matrix paths document original execution but are unnecessary for fresh routing. `hazard_input_manifest.json` verifies derived inputs. `hazard_analysis.json` and its arrays supply the main cross-intensity and decomposition figures. `mechanism_results` partitions disconnection into endpoint isolation and loss beyond live incident roads; it is not observed damage attribution. Country outlines are cartographic context only.

The scripts `summarize_hazard.py`, `summarize_controls.py` and `network_mechanism.py` preserve analysis definitions. The latter uses archived routing paths unless run against fresh outputs and appropriately configured inputs; it is not the portable routing entry point. `figures_natural_hazards.py` rebuilds all six figures from the supplied summary inputs. The runtime wrapper avoids an optional Windows WMI probe that hung on the execution host. Raw providers, licenses and acquisition manifests are retained from the earlier analysis below. Existing third-party data licenses continue to apply; this package does not relicense them.

## Earlier computational components retained

# Resident model reproduction

Python 3.10+, NumPy and SciPy. Run from this directory:

```
python portable_population.py --output recomputed --codes BE004L2
```

Omit `--codes` to rerun every city. Output and all caches must be on a writable working disk. This entry point hashes supplied inputs, calculates fresh shortest paths (an empty output directory has no routing cache), and compares all 88 population/unit/restricted-support rows against the supplied reference. `--response` additionally runs all three depth-response variants. Cached matrices are reused only within that chosen output directory. Approximate city runtime varies substantially with graph and endpoint count; run serially on memory-constrained machines.

Graph and hazard inputs are the frozen derived arrays used in the prior geometric reference. Population support arrays contain every positive intersecting cell, allocated mass, boundary fraction, snapping distance, and node mappings on both graphs. The original GEOSTAT source and technical factsheet are identified by population_source_check.json and source_manifest.json. The resident endpoint model is conditional on distinct dry reachable destinations and excludes within-node travel. No actual trips or flood labels were generated by a language model.

The complete article contains the scientific definitions and limitations. Checks establish numerical reproduction, not hydrological or behavioral validity. Source identifiers in reference results document the original calculation; the portable entry point uses the relative files in this package, not those workstation paths.

## Rebuild population allocation from source files

Install rasterio, shapely and pyproj in addition to NumPy/SciPy, then run:

```
python build_population_support.py --output rebuilt_support --codes ES059L1
```

Omit `--codes` for all cities. After optional source acquisition, this verifies the source grid and full boundary-file identities, intersects original grid cells, applies the stated boundary allocation and rebuilds node mappings against the packaged graphs. Compare arrays numerically against population_support. The optional source acquisition script verifies exact original archive-member identities. All original source licensing and attribution requirements continue to apply; no new license is asserted over third-party source data.

Response summaries and unit comparisons cover all 36 areas. audit_response_results.py is an archival audit of the original cached path identities; use portable_population.py --response for a fresh portable response computation.

Response summaries and unit comparisons cover all 36 areas. audit_response_results.py is an archival audit of the original cached path identities; use portable_population.py --response for a fresh portable response computation.
