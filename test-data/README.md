# Test data

Put only de-identified or synthetic demonstration NIfTI files in:

```text
test-data/private/
```

The `private` directory is excluded from Git and Docker build contexts. A
typical end-to-end test file is:

```text
test-data/private/demo_ct.nii.gz
```

Do not place patient names, identifiers, dates of birth, or clinical exports
containing identifying metadata in this repository.
