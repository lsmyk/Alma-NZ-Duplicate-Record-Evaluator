# Alma NZ Duplicate Record Evaluator

A Python utility designed to optimize the Network Zone (NZ) deduplication process in Alma by intelligently selecting the highest-quality record to retain during a merge.

## Purpose & Background
When managing a large catalog, identical OCLC control numbers can result in duplicate bibliographic records. While Alma provides a built-in automated job—**"Merge records and combine inventory"**—to resolve these duplicates, the native tool merges records blindly by retaining the first listed record and deleting the rest. 

Because the first listed record is not always the best record, this script acts as an intelligent intermediary. It processes your duplicate registry alongside raw MARC metadata, automatically scores the record quality within each duplicate group, flags which record should be kept versus deleted, and exports a configuration file optimized for the Alma merge job.

## How It Works
The tool streamlines your deduplication workflow in three major phases:
1. **Data Ingestion:** It aligns a tabular report of duplicate groups (`dups.csv`) with full MARC bibliographic text records (`bibs.mrk`).
2. **Quality Evaluation:** Within each OCLC grouping, the script evaluates structural metadata markers (such as Brief Levels and key MARC tags) to score the record completeness.
3. **Alma-Ready Export:** It explicitly marks the optimized "Keep" and "Delete" decisions, formatting the output into a structured file (`merge.csv`) designed to plug directly into Alma's bulk-merge tool.

## Prerequisites
This script requires external packages for data manipulation and MARC file handling. Run the following command if you are using a local terminal environment:

```bash
pip install pandas pymarc numpy
```
*Note: If you run this script in Google Colab, you will only need to install `pymarc`, as `pandas` and `numpy` are already pre-installed.*

## Required Input Format
The script requires two specific files to be uploaded into its working directory:

### 1. `dups.csv`
An Alma Analytics report mapping your duplicate clusters grouped by identical OCLC numbers. The file **must** include the following exact columns:
* `Group Number`
* `MMS ID`
* `Identifier` (OCLC Number)
* `Records in Group`
* `Operation`
* `Material Type`
* `Brief Level`
* `Resource Type`
* `Institution Name`
* `Title`

### 2. `bibs.mrk`
A MARC text file (MarcEdit mnemonic format) containing the full bibliographic text records corresponding to the MMS IDs in your duplicate report.

## Output Files
After execution, the script generates:
* **`merge.csv`** – A refined data layout that specifies targeted Keep/Delete actions per MMS ID, configured to bypass Alma’s random default settings and drive a high-quality automated merge.

## Contributing
Contributions are welcome! If you would like to introduce custom scoring weights (such as evaluating specific cataloguing codes or local fields), please open an issue or submit a pull request.

