# Data

Conventions:
- source data files go into `data/src`
- generated files go into `data`

## U.S. Automated Manifest System (customs & shipping)

Retrieved: 4/26/2019
Info: <https://public.enigma.com/browse/collection/u-s-automated-manifest-system/f3d29ca5-b0de-46f4-910f-54eccece4ad2>

Downloading the Enigma data requires authentication. You can provide a cookies file and use `wget`, as below, or download them through a browser.

```
# AMS Bill of Lading Summary - 2018
wget --load-cookies cookies.txt https://public.enigma.com/api/export/28ad5b7c-f553-470f-a0bd-36fca57a6021? -O data/src/ams_bill_of_lading_summary__2018.csv

# AMS Cargo Descriptions - 2018
wget --load-cookies cookies.txt https://public.enigma.com/api/export/30c7ecaa-61bc-4de0-aee0-d51f2ea2942a? -O data/src/ams_cargo_descriptions__2018.csv

# AMS Bill of Lading Headers - 2018
wget --load-cookies cookies.txt https://public.enigma.com/api/export/a6be01f2-b029-48f0-b226-f3f1bdf849f0? -O data/src/ams_bill_of_lading_headers__2018.csv

# AMS Shippers - 2018
wget --load-cookies cookies.txt https://public.enigma.com/api/export/d1125eca-0004-4d16-bd9d-f7ec7ac3b517? -O data/src/ams_shippers__2018.csv


# AMS Shipment Consignees - 2018
wget --load-cookies cookies.txt https://public.enigma.com/api/export/676180be-d93d-43bf-97d1-d3f7c7882e27? -O data/src/ams_shipment_consignees__2018.csv
```

## Parent-Subsidiary

Retrieved: 4/26/2019
Info: <http://api.corpwatch.org/documentation/db_dump/>

```
wget http://api.corpwatch.org/documentation/db_dump/corpwatch_api_tables_csv.tar.gz
```

## Legal entity names

Retrieved: 4/26/2019
Info: <https://www.gleif.org/en/about-lei/code-lists/iso-20275-entity-legal-forms-code-list>

```
wget https://www.gleif.org/content/2-about-lei/7-code-lists/2-iso-20275-entity-legal-forms-code-list/2017-11-30_elf-code-list-publication-version-1.csv -O entity_codes.csv
```
