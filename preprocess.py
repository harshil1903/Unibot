import pandas as pd

def merge():
    a = pd.read_csv("data/CU_SR_OPEN_DATA_CATALOG-37272173.csv", encoding= 'unicode_escape')
    b = pd.read_csv("data/CU_SR_OPEN_DATA_CATALOG_DESC-45649197.csv", encoding= 'unicode_escape')

    merged = pd.merge(a, b, on = "Course ID")

    merged = merged.drop(merged.columns[[5, 6, 7, 8, 9]], axis=1)
    merged.rename(columns = {"Catalog":"Number", "Class Units":"Credits","Descr":"Description","Long Title":"Name"}, inplace=True)
    print(merged.head())
    merged.to_csv("data/output.csv", index = False)


merge()