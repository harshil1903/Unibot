import pandas as pd

def merge():
    a = pd.read_csv("data/CU_SR_OPEN_DATA_CATALOG-37272173.csv", encoding= 'unicode_escape')
    b = pd.read_csv("data/CU_SR_OPEN_DATA_CATALOG_DESC-45649197.csv", encoding= 'unicode_escape')

    df = pd.merge(a, b, on = "Course ID", how="inner")
    df = df.drop(df.columns[[5, 6, 7, 8, 9]], axis=1)

    df = df.drop_duplicates("Course ID", keep = "first")
    df.rename(columns = {"Catalog":"Number", "Class Units":"Credits","Descr":"Description","Long Title":"Name"}, inplace=True)
    print(df.head())
    df.to_csv("data/dataset.csv", index = False)


merge()